"""
Restaurant POS (Tkinter) - single-file

Features:
- Table management (create/select tables)
- Menu items loaded from SQLite (sample data auto-inserted if empty)
- Order entry (add items, qty)
- Kitchen screen (view pending orders per table, mark prepared)
- Save bills to SQLite, generate PDF receipt in receipts/
- Offline storage with sqlite3

Requires:
    pip install reportlab
Run:
    python restaurant_pos.py
"""

import os
import sys
import sqlite3
import datetime
from decimal import Decimal, ROUND_HALF_UP
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# reportlab for receipts
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

DB_FILE = "pos.db"

def money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# ---------------------
# Database helpers
# ---------------------
def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        status TEXT DEFAULT 'Free'
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        category TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER,
        created_at TEXT,
        status TEXT DEFAULT 'open', -- open, billed
        total REAL,
        gst REAL,
        paid INTEGER DEFAULT 0,
        receipt_path TEXT,
        FOREIGN KEY(table_id) REFERENCES tables(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        menu_item_id INTEGER,
        name TEXT,
        qty REAL,
        rate REAL,
        total REAL,
        status TEXT DEFAULT 'pending', -- pending, preparing, done, served
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
    )""")
    con.commit()

    # Insert sample menu items if none
    cur.execute("SELECT COUNT(*) FROM menu_items")
    if cur.fetchone()[0] == 0:
        sample = [
            ("Margherita Pizza", 220.00, "Pizza"),
            ("Pepperoni Pizza", 260.00, "Pizza"),
            ("Veg Burger", 90.00, "Burger"),
            ("Chicken Burger", 120.00, "Burger"),
            ("French Fries", 60.00, "Sides"),
            ("Coke (500ml)", 40.00, "Beverage"),
            ("Masala Dosa", 80.00, "South Indian"),
            ("Filter Coffee", 30.00, "Beverage"),
        ]
        cur.executemany("INSERT INTO menu_items(name, price, category) VALUES (?, ?, ?)", sample)
        con.commit()

    # Insert some tables if none
    cur.execute("SELECT COUNT(*) FROM tables")
    if cur.fetchone()[0] == 0:
        tables = [("T1",), ("T2",), ("T3",), ("T4",), ("T5",)]
        cur.executemany("INSERT INTO tables(name) VALUES (?)", tables)
        con.commit()

    con.close()

def get_tables():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id, name, status FROM tables ORDER BY id")
    rows = cur.fetchall()
    con.close()
    return rows

def get_menu_items():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id, name, price, category FROM menu_items ORDER BY category, name")
    rows = cur.fetchall()
    con.close()
    return rows

def create_order(table_id):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    now = datetime.datetime.now().isoformat()
    cur.execute("INSERT INTO orders(table_id, created_at, status) VALUES (?, ?, 'open')", (table_id, now))
    oid = cur.lastrowid
    cur.execute("UPDATE tables SET status='Occupied' WHERE id=?", (table_id,))
    con.commit()
    con.close()
    return oid

def get_open_order_for_table(table_id):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id FROM orders WHERE table_id=? AND status='open' ORDER BY id DESC LIMIT 1", (table_id,))
    r = cur.fetchone()
    con.close()
    return r[0] if r else None

def add_order_item(order_id, menu_item_id, name, qty, rate):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    total = float(money(qty * Decimal(rate)))
    cur.execute("""
        INSERT INTO order_items(order_id, menu_item_id, name, qty, rate, total, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (order_id, menu_item_id, name, float(qty), float(rate), total))
    con.commit()
    con.close()

def get_order_items(order_id):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id, name, qty, rate, total, status FROM order_items WHERE order_id=? ORDER BY id", (order_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def set_order_item_status(item_id, status):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("UPDATE order_items SET status=? WHERE id=?", (status, item_id))
    con.commit()
    con.close()

def finalize_bill(order_id, gst_percent=5.0):
    # calculate totals, set order status billed
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT SUM(total) FROM order_items WHERE order_id=?", (order_id,))
    subtotal = cur.fetchone()[0] or 0.0
    gst = float(money(Decimal(subtotal) * Decimal(gst_percent) / Decimal(100)))
    total = float(money(Decimal(subtotal) + Decimal(gst)))
    cur.execute("UPDATE orders SET total=?, gst=?, status='billed' WHERE id=?", (total, gst, order_id))
    # free table
    cur.execute("SELECT table_id FROM orders WHERE id=?", (order_id,))
    tid = cur.fetchone()[0]
    cur.execute("UPDATE tables SET status='Free' WHERE id=?", (tid,))
    con.commit()
    con.close()
    return subtotal, gst, total

def save_receipt_path(order_id, path):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("UPDATE orders SET receipt_path=? WHERE id=?", (path, order_id))
    con.commit()
    con.close()

def get_pending_items():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT oi.id, o.table_id, t.name, oi.name, oi.qty, oi.rate, oi.total, oi.status, o.id
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN tables t ON o.table_id = t.id
        WHERE o.status='open' AND oi.status IN ('pending','preparing')
        ORDER BY o.table_id, oi.id
    """)
    rows = cur.fetchall()
    con.close()
    return rows

# ---------------------
# Receipt PDF
# ---------------------
def generate_receipt_pdf(order_id, receipt_path):
    # fetch order, items
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT o.id, t.name, o.created_at, o.total, o.gst FROM orders o JOIN tables t ON o.table_id=t.id WHERE o.id=?", (order_id,))
    r = cur.fetchone()
    if not r:
        con.close()
        raise RuntimeError("Order not found")
    _, table_name, created_at, total, gst = r
    cur.execute("SELECT name, qty, rate, total FROM order_items WHERE order_id=?", (order_id,))
    items = cur.fetchall()
    con.close()

    # Build PDF
    os.makedirs("receipts", exist_ok=True)
    doc = SimpleDocTemplate(receipt_path, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("<b>Safari World</b>", styles['Title']))
    story.append(Paragraph("3rd Floor, Safari Mall, Gachibowli, Chennai", styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Table: {table_name}", styles['Normal']))
    story.append(Paragraph(f"Order ID: {order_id}  Date: {created_at}", styles['Normal']))
    story.append(Spacer(1, 8))

    data = [["Item", "Qty", "Rate", "Total"]]
    for it in items:
        data.append([it[0], str(it[1]), f"{money(it[2])}", f"{money(it[3])}"])

    tbl = Table(data, colWidths=[90*mm, 20*mm, 30*mm, 30*mm])
    tbl.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))

    subtotal = sum([it[3] for it in items]) if items else 0.0
    story.append(Paragraph(f"<b>Subtotal:</b> {money(subtotal)}", styles['Normal']))
    story.append(Paragraph(f"<b>GST:</b> {money(gst) if gst else '0.00'}", styles['Normal']))
    story.append(Paragraph(f"<b>Total:</b> {money(total) if total else money(subtotal)}", styles['Heading2']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Thank you! Visit again.", styles['Normal']))
    doc.build(story)

# ---------------------
# GUI Application
# ---------------------
class POSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant POS")
        self.geometry("1100x700")
        self.resizable(True, True)
        self.style = ttk.Style(self)
        self.selected_table_id = None
        self.current_order_id = None
        self.menu_items = []
        self.order_items = []  # in-memory for UI (but persisted when saved)
        self.create_widgets()
        self.refresh_tables()
        self.load_menu()

    def create_widgets(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill='both', expand=True)

        # Left: tables
        left = ttk.LabelFrame(top, text="Tables", width=220)
        left.pack(side='left', fill='y', padx=6, pady=6)
        self.tables_list = tk.Listbox(left, height=20, width=20)
        self.tables_list.pack(padx=6, pady=6)
        self.tables_list.bind("<<ListboxSelect>>", self.on_table_select)
        ttk.Button(left, text="New Table", command=self.create_table).pack(fill='x', padx=6, pady=4)
        ttk.Button(left, text="Open Kitchen", command=self.open_kitchen_screen).pack(fill='x', padx=6, pady=4)

        # Center: order & items
        center = ttk.Frame(top)
        center.pack(side='left', fill='both', expand=True, padx=6, pady=6)

        meta = ttk.Frame(center)
        meta.pack(fill='x')
        ttk.Label(meta, text="Selected Table:").pack(side='left')
        self.table_label = ttk.Label(meta, text="-")
        self.table_label.pack(side='left', padx=6)

        # Menu + add controls
        menu_frame = ttk.LabelFrame(center, text="Menu")
        menu_frame.pack(fill='both', expand=True, padx=4, pady=4)

        self.menu_tree = ttk.Treeview(menu_frame, columns=("name","price","category"), show='headings', height=12)
        self.menu_tree.heading("name", text="Name")
        self.menu_tree.heading("price", text="Price")
        self.menu_tree.heading("category", text="Category")
        self.menu_tree.column("name", width=320, anchor='w')
        self.menu_tree.column("price", width=80, anchor='e')
        self.menu_tree.column("category", width=120, anchor='center')
        self.menu_tree.pack(side='left', fill='both', expand=True, padx=4, pady=4)

        right_ctrl = ttk.Frame(menu_frame)
        right_ctrl.pack(side='left', fill='y', padx=6)
        ttk.Label(right_ctrl, text="Qty:").pack(anchor='w')
        self.qty_spin = tk.Spinbox(right_ctrl, from_=1, to=100, width=6)
        self.qty_spin.pack(anchor='w', pady=4)
        ttk.Button(right_ctrl, text="Add to Order", command=self.add_selected_menu_item).pack(fill='x', pady=4)

        # Current order frame
        order_frame = ttk.LabelFrame(center, text="Current Order")
        order_frame.pack(fill='both', expand=True, padx=4, pady=4)

        self.order_tree = ttk.Treeview(order_frame, columns=("name","qty","rate","total","status"), show='headings', height=12)
        for c in ("name","qty","rate","total","status"):
            self.order_tree.heading(c, text=c.title())
        self.order_tree.column("name", width=320, anchor='w')
        self.order_tree.column("qty", width=60, anchor='center')
        self.order_tree.column("rate", width=80, anchor='e')
        self.order_tree.column("total", width=90, anchor='e')
        self.order_tree.column("status", width=100, anchor='center')
        self.order_tree.pack(fill='both', expand=True, padx=4, pady=4)

        buttons = ttk.Frame(center)
        buttons.pack(fill='x', pady=6)
        ttk.Button(buttons, text="Remove Item", command=self.remove_order_item).pack(side='left', padx=4)
        ttk.Button(buttons, text="Send to Kitchen", command=self.send_to_kitchen).pack(side='left', padx=4)
        ttk.Button(buttons, text="Save & Print Bill", command=self.save_and_print_bill).pack(side='left', padx=4)

        # Right: summary & controls
        right = ttk.LabelFrame(top, text="Summary", width=300)
        right.pack(side='right', fill='y', padx=6, pady=6)

        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        ttk.Label(right, text="Subtotal:").pack(anchor='w', padx=6, pady=(6,0))
        ttk.Label(right, textvariable=self.subtotal_var, font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', padx=6)

        ttk.Label(right, text="GST %:").pack(anchor='w', padx=6, pady=(12,0))
        self.gst_percent_var = tk.DoubleVar(value=5.0)
        ttk.Entry(right, textvariable=self.gst_percent_var, width=6).pack(anchor='w', padx=6)

        ttk.Label(right, text="GST Amount:").pack(anchor='w', padx=6, pady=(12,0))
        ttk.Label(right, textvariable=self.gst_var).pack(anchor='w', padx=6)

        ttk.Label(right, text="Total:").pack(anchor='w', padx=6, pady=(12,0))
        ttk.Label(right, textvariable=self.total_var, font=('TkDefaultFont', 14, 'bold')).pack(anchor='w', padx=6)

        ttk.Button(right, text="Refresh Tables", command=self.refresh_tables).pack(fill='x', padx=6, pady=(20,4))
        ttk.Button(right, text="Open Kitchen", command=self.open_kitchen_screen).pack(fill='x', padx=6, pady=4)

    # --------------------
    # UI actions
    # --------------------
    def refresh_tables(self):
        self.tables_list.delete(0, 'end')
        rows = get_tables()
        for r in rows:
            display = f"{r[1]}  ({r[2]})"
            self.tables_list.insert('end', display)
        # if a table selected, keep selection
        self.update_title()

    def on_table_select(self, evt):
        sel = self.tables_list.curselection()
        if not sel:
            return
        idx = sel[0]
        rows = get_tables()
        row = rows[idx]
        self.selected_table_id = row[0]
        self.table_label.config(text=row[1])
        # find open order or create new
        order_id = get_open_order_for_table(self.selected_table_id)
        if not order_id:
            order_id = create_order(self.selected_table_id)
        self.current_order_id = order_id
        self.load_order_items()
        self.update_title()

    def load_menu(self):
        self.menu_tree.delete(*self.menu_tree.get_children())
        self.menu_items = get_menu_items()
        for m in self.menu_items:
            self.menu_tree.insert('', 'end', iid=str(m[0]), values=(m[1], f"{money(m[2])}", m[3]))

    def add_selected_menu_item(self):
        if not self.selected_table_id or not self.current_order_id:
            messagebox.showwarning("Select Table", "Please select a table first.")
            return
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("Select Item", "Select a menu item to add.")
            return
        menu_id = int(sel[0])
        # find menu entry
        m = next((x for x in self.menu_items if x[0] == menu_id), None)
        if not m:
            return
        qty = Decimal(self.qty_spin.get())
        name = m[1]
        rate = Decimal(str(m[2]))
        add_order_item(self.current_order_id, menu_id, name, qty, rate)
        # mark UI
        self.load_order_items()
        # refresh kitchen view if open (best-effort)
        try:
            if hasattr(self, "kitchen_window") and self.kitchen_window.winfo_exists():
                self.kitchen_window.refresh()
        except Exception:
            pass

    def load_order_items(self):
        self.order_tree.delete(*self.order_tree.get_children())
        self.order_items = []
        if not self.current_order_id:
            return
        rows = get_order_items(self.current_order_id)
        for r in rows:
            self.order_items.append(r)
            self.order_tree.insert('', 'end', iid=str(r[0]), values=(r[1], r[2], f"{money(r[3])}", f"{money(r[4])}", r[5]))
        self.recalc_summary()

    def remove_order_item(self):
        sel = self.order_tree.selection()
        if not sel:
            return
        iid = int(sel[0])
        # only allow remove if not preparing/done
        for it in self.order_items:
            if it[0] == iid:
                if it[4] in ('preparing','done','served'):
                    messagebox.showwarning("Cannot remove", "Item already preparing/served.")
                    return
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute("DELETE FROM order_items WHERE id=?", (iid,))
        con.commit()
        con.close()
        self.load_order_items()

    def send_to_kitchen(self):
        # set pending items to preparing
        if not self.current_order_id:
            return
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute("UPDATE order_items SET status='preparing' WHERE order_id=? AND status='pending'", (self.current_order_id,))
        con.commit()
        con.close()
        self.load_order_items()
        # refresh kitchen
        try:
            if hasattr(self, "kitchen_window") and self.kitchen_window.winfo_exists():
                self.kitchen_window.refresh()
        except Exception:
            pass
        messagebox.showinfo("Sent", "Order sent to kitchen.")

    def recalc_summary(self):
        subtotal = Decimal('0.00')
        for it in self.order_items:
            subtotal += money(it[4])
        gst_percent = Decimal(str(self.gst_percent_var.get()))
        gst_amt = money(subtotal * gst_percent / Decimal(100))
        total = money(subtotal + gst_amt)
        self.subtotal_var.set(f"{money(subtotal)}")
        self.gst_var.set(f"{gst_amt}")
        self.total_var.set(f"{total}")

    def save_and_print_bill(self):
        if not self.current_order_id:
            messagebox.showwarning("No order", "Select a table and create an order first.")
            return
        # finalize bill (calculates totals & frees table)
        gst_percent = float(self.gst_percent_var.get())
        subtotal, gst_amt, total = finalize_bill(self.current_order_id, gst_percent=gst_percent)
        # ask where to save receipt
        os.makedirs("receipts", exist_ok=True)
        suggested = os.path.join("receipts", f"receipt_order_{self.current_order_id}.pdf")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=os.path.basename(suggested),
                                            initialdir=os.path.abspath("receipts"), filetypes=[("PDF files","*.pdf")])
        if not path:
            # user cancelled: still save order as billed but no receipt file
            save_receipt_path(self.current_order_id, None)
            messagebox.showinfo("Billed", f"Order {self.current_order_id} billed (no receipt saved).")
        else:
            try:
                generate_receipt_pdf(self.current_order_id, path)
                save_receipt_path(self.current_order_id, path)
                # open the PDF for printing/viewing
                if sys.platform.startswith('win'):
                    os.startfile(path)
                elif sys.platform.startswith('darwin'):
                    os.system(f"open '{path}'")
                else:
                    os.system(f"xdg-open '{path}'")
                messagebox.showinfo("Billed", f"Order {self.current_order_id} billed and receipt saved:\n{path}")
            except Exception as e:
                messagebox.showwarning("Saved but error", f"Order billed but failed to create/open receipt:\n{e}")
        # reset selection & refresh
        self.selected_table_id = None
        self.current_order_id = None
        self.table_label.config(text='-')
        self.load_order_items()
        self.refresh_tables()

    def create_table(self):
        name = simpledialog.askstring("New Table", "Enter table name (e.g. T6):", parent=self)
        if not name:
            return
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO tables(name) VALUES (?)", (name.strip(),))
            con.commit()
            messagebox.showinfo("Created", f"Table {name} created.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Exists", "Table name already exists.")
        finally:
            con.close()
        self.refresh_tables()

    def open_kitchen_screen(self):
        if hasattr(self, "kitchen_window") and getattr(self, "kitchen_window"):
            try:
                if self.kitchen_window.winfo_exists():
                    self.kitchen_window.lift()
                    return
            except Exception:
                pass
        self.kitchen_window = KitchenWindow(self)
        self.kitchen_window.refresh()

    def update_title(self):
        self.title(f"Restaurant POS - Selected Table: {self.table_label['text']}")

# ---------------------
# Kitchen window
# ---------------------
class KitchenWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Kitchen Screen - Pending Orders")
        self.geometry("700x500")
        self.create_widgets()

    def create_widgets(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(top, columns=("item_id","table","name","qty","rate","total","status","order_id"), show='headings')
        for h,w in (("item_id",60),("table",80),("name",260),("qty",50),("rate",80),("total",80),("status",100),("order_id",80)):
            self.tree.heading(h, text=h.title())
            self.tree.column(h, width=w, anchor='center')
        self.tree.pack(fill='both', expand=True)
        btns = ttk.Frame(self)
        btns.pack(fill='x', pady=6)
        ttk.Button(btns, text="Mark Preparing", command=lambda: self.change_status("preparing")).pack(side='left', padx=6)
        ttk.Button(btns, text="Mark Done", command=lambda: self.change_status("done")).pack(side='left', padx=6)
        ttk.Button(btns, text="Refresh", command=self.refresh).pack(side='left', padx=6)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = get_pending_items()
        for r in rows:
            # r: item.id, table_id, table_name, item_name, qty, rate, total, status, order_id
            self.tree.insert('', 'end', iid=str(r[0]), values=(r[0], r[2], r[3], r[4], f"{money(r[5])}", f"{money(r[6])}", r[7], r[8]))

    def change_status(self, new_status):
        sel = self.tree.selection()
        if not sel:
            return
        iid = int(sel[0])
        set_order_item_status(iid, new_status)
        self.refresh()

# ---------------------
# Main
# ---------------------
if __name__ == "__main__":
    init_db()
    app = POSApp()
    app.mainloop()
