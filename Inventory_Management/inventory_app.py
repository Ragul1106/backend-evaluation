import os
import sqlite3
import datetime
from decimal import Decimal, ROUND_HALF_UP
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Excel export
try:
    from openpyxl import Workbook
except Exception as e:
    Workbook = None

DB_FILE = "inventory.db"

# --------------------------
# Utility
# --------------------------
def money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# --------------------------
# Database
# --------------------------
def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    # products
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE,
        name TEXT,
        category TEXT,
        qty REAL DEFAULT 0,
        reorder_level REAL DEFAULT 0,
        cost_price REAL DEFAULT 0.0,
        created_at TEXT
    )""")
    # suppliers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        phone TEXT,
        email TEXT,
        created_at TEXT
    )""")
    # purchase orders
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_no TEXT UNIQUE,
        supplier_id INTEGER,
        date TEXT,
        total_amount REAL,
        created_at TEXT,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS po_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER,
        product_id INTEGER,
        qty REAL,
        cost_price REAL,
        line_total REAL,
        FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )""")
    # simple audit/stock adjustments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        qty_change REAL,
        reason TEXT,
        created_at TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )""")
    con.commit()
    con.close()

# --------------------------
# Data operations
# --------------------------
def add_supplier(name, phone="", email=""):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cur.execute("INSERT INTO suppliers(name, phone, email, created_at) VALUES (?, ?, ?, ?)",
                    (name.strip(), phone.strip(), email.strip(), now))
        con.commit()
        sid = cur.lastrowid
    except sqlite3.IntegrityError:
        sid = None
    con.close()
    return sid

def list_suppliers():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id, name, phone, email FROM suppliers ORDER BY name")
    rows = cur.fetchall()
    con.close()
    return rows

def add_product(sku, name, category, qty, reorder_level, cost_price):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cur.execute("""
            INSERT INTO products(sku, name, category, qty, reorder_level, cost_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sku.strip(), name.strip(), category.strip(), float(qty), float(reorder_level), float(cost_price), now))
        con.commit()
        pid = cur.lastrowid
    except sqlite3.IntegrityError:
        pid = None
    con.close()
    return pid

def update_product(pid, sku, name, category, qty, reorder_level, cost_price):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        UPDATE products SET sku=?, name=?, category=?, qty=?, reorder_level=?, cost_price=?
        WHERE id=?
    """, (sku.strip(), name.strip(), category.strip(), float(qty), float(reorder_level), float(cost_price), pid))
    con.commit()
    con.close()

def delete_product(pid):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    con.commit()
    con.close()

def list_products(search=None):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("SELECT id, sku, name, category, qty, reorder_level, cost_price FROM products WHERE sku LIKE ? OR name LIKE ? OR category LIKE ? ORDER BY name",
                    (like, like, like))
    else:
        cur.execute("SELECT id, sku, name, category, qty, reorder_level, cost_price FROM products ORDER BY name")
    rows = cur.fetchall()
    con.close()
    return rows

def adjust_stock(product_id, qty_change, reason="Adjustment"):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    now = datetime.datetime.now().isoformat()
    cur.execute("INSERT INTO stock_movements(product_id, qty_change, reason, created_at) VALUES (?, ?, ?, ?)",
                (product_id, float(qty_change), reason, now))
    cur.execute("UPDATE products SET qty = qty + ? WHERE id=?", (float(qty_change), product_id))
    con.commit()
    con.close()

# Purchase Orders
def next_po_no():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT po_no FROM purchase_orders ORDER BY id DESC LIMIT 1")
    r = cur.fetchone()
    con.close()
    if not r:
        return "PO0001"
    import re
    m = re.search(r"(\d+)$", r[0])
    if m:
        n = int(m.group(1)) + 1
        return f"PO{n:04d}"
    return r[0] + "_1"

def create_purchase_order(po_no, supplier_id, items):
    """
    items: list of dicts {product_id, qty, cost_price}
    """
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    now = datetime.datetime.now().isoformat()
    total_amount = 0.0
    try:
        cur.execute("INSERT INTO purchase_orders(po_no, supplier_id, date, total_amount, created_at) VALUES (?, ?, ?, ?, ?)",
                    (po_no, supplier_id, now, 0.0, now))
        po_id = cur.lastrowid
        for it in items:
            line_total = float(Decimal(it['qty'] * Decimal(it['cost_price'])).quantize(Decimal("0.01")))
            total_amount += line_total
            cur.execute("INSERT INTO po_items(po_id, product_id, qty, cost_price, line_total) VALUES (?, ?, ?, ?, ?)",
                        (po_id, it['product_id'], float(it['qty']), float(it['cost_price']), line_total))
            # increase stock
            cur.execute("UPDATE products SET qty = qty + ? WHERE id=?", (float(it['qty']), it['product_id']))
            # record stock movement
            cur.execute("INSERT INTO stock_movements(product_id, qty_change, reason, created_at) VALUES (?, ?, ?, ?)",
                        (it['product_id'], float(it['qty']), f"PO {po_no}", now))
        cur.execute("UPDATE purchase_orders SET total_amount=? WHERE id=?", (float(total_amount), po_id))
        con.commit()
    except Exception as e:
        con.rollback()
        con.close()
        raise
    con.close()
    return po_id

def list_purchase_orders():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id, po_no, supplier_id, date, total_amount FROM purchase_orders ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return rows

def get_po_items(po_id):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT pi.id, pi.product_id, p.sku, p.name, pi.qty, pi.cost_price, pi.line_total
        FROM po_items pi
        JOIN products p ON p.id = pi.product_id
        WHERE pi.po_id = ?
    """, (po_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def low_stock_products():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT id, sku, name, qty, reorder_level FROM products WHERE qty <= reorder_level ORDER BY name")
    rows = cur.fetchall()
    con.close()
    return rows

def seed_sample_data():
    """
    Insert example suppliers, products and one PO if tables are empty.
    Safe to run multiple times (it checks counts).
    """
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    # Suppliers
    cur.execute("SELECT COUNT(*) FROM suppliers")
    if cur.fetchone()[0] == 0:
        sample_suppliers = [
            ("Fresh Farms", "9876500001", "sales@freshfarms.example"),
            ("ABC Distributors", "9876500002", "contact@abcdistribs.example"),
            ("Global Foods", "9876500003", "info@globalfoods.example"),
        ]
        cur.executemany("INSERT INTO suppliers(name, phone, email, created_at) VALUES (?, ?, ?, ?)",
                        [(s[0], s[1], s[2], datetime.datetime.now().isoformat()) for s in sample_suppliers])
        con.commit()

    # Products
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample_products = [
            ("PZ001", "Margherita Pizza", "Pizza", 10, 5, 150.00),
            ("PZ002", "Pepperoni Pizza", "Pizza", 8, 4, 180.00),
            ("BG001", "Veg Burger", "Burger", 20, 8, 60.00),
            ("BG002", "Chicken Burger", "Burger", 15, 5, 80.00),
            ("FR001", "French Fries", "Sides", 30, 10, 30.00),
            ("BV001", "Coke (500ml)", "Beverage", 50, 10, 25.00),
            ("SD001", "Masala Dosa", "South Indian", 12, 4, 50.00),
            ("CF001", "Filter Coffee", "Beverage", 40, 10, 20.00),
        ]
        now = datetime.datetime.now().isoformat()
        cur.executemany(
            "INSERT INTO products(sku, name, category, qty, reorder_level, cost_price, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(p[0], p[1], p[2], float(p[3]), float(p[4]), float(p[5]), now) for p in sample_products]
        )
        con.commit()

    # Purchase Order (one sample) — only if no POs exist
    cur.execute("SELECT COUNT(*) FROM purchase_orders")
    if cur.fetchone()[0] == 0:
        # pick a supplier id (first one)
        cur.execute("SELECT id FROM suppliers ORDER BY id LIMIT 1")
        sup = cur.fetchone()
        if sup:
            supplier_id = sup[0]
            # build items: choose a few products and quantities
            cur.execute("SELECT id, cost_price FROM products LIMIT 4")
            prod_rows = cur.fetchall()
            items = []
            for pr in prod_rows:
                pid = pr[0]
                cost = pr[1] if pr[1] else 50.0
                items.append({"product_id": pid, "qty": 5, "cost_price": float(cost)})
            po_no = next_po_no()
            # use create_purchase_order to insert and update stock
            try:
                create_purchase_order(po_no, supplier_id, items)
            except Exception as e:
                # if any error, ignore but print to console for debugging
                print("Seed PO creation error:", e)

    con.close()
# --------------------------
# Excel export
# --------------------------
def export_products_to_excel(path):
    if Workbook is None:
        raise RuntimeError("openpyxl not installed")
    rows = list_products()
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    ws.append(["SKU", "Name", "Category", "Quantity", "Reorder Level", "Cost Price"])
    for r in rows:
        ws.append([r[1], r[2], r[3], float(r[4]), float(r[5]), float(r[6])])
    wb.save(path)

def export_pos_to_excel(path):
    if Workbook is None:
        raise RuntimeError("openpyxl not installed")
    pos = list_purchase_orders()
    wb = Workbook()
    ws = wb.active
    ws.title = "Purchase Orders"
    ws.append(["PO No", "Supplier", "Date", "Total Amount"])
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    for po in pos:
        cur.execute("SELECT name FROM suppliers WHERE id=?", (po[2],))
        sup = cur.fetchone()
        supname = sup[0] if sup else ""
        ws.append([po[1], supname, po[3], float(po[4])])
    con.close()
    wb.save(path)

# --------------------------
# GUI
# --------------------------
class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Management System")
        self.geometry("1000x650")
        self.create_widgets()
        self.refresh_products()
        self.refresh_suppliers()
        self.refresh_pos()
        self.check_low_stock_startup()

    def create_widgets(self):
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        # Products tab
        self.tab_products = ttk.Frame(nb)
        nb.add(self.tab_products, text="Products")

        # Suppliers tab
        self.tab_suppliers = ttk.Frame(nb)
        nb.add(self.tab_suppliers, text="Suppliers")

        # Purchase Orders tab
        self.tab_pos = ttk.Frame(nb)
        nb.add(self.tab_pos, text="Purchase Orders")

        # ---------- Products tab ----------
        p_top = ttk.Frame(self.tab_products)
        p_top.pack(fill='x', pady=6)
        ttk.Label(p_top, text="Search:").pack(side='left')
        self.prod_search = tk.StringVar()
        ent = ttk.Entry(p_top, textvariable=self.prod_search, width=40)
        ent.pack(side='left', padx=6)
        ttk.Button(p_top, text="Search", command=self.on_search_products).pack(side='left', padx=6)
        ttk.Button(p_top, text="Clear", command=self.on_clear_search).pack(side='left', padx=6)
        ttk.Button(p_top, text="Export to Excel", command=self.on_export_products).pack(side='right', padx=6)

        cols = ("id", "sku", "name", "category", "qty", "reorder", "cost")
        self.prod_tree = ttk.Treeview(self.tab_products, columns=cols, show='headings', height=18)
        for c in cols:
            self.prod_tree.heading(c, text=c.title())
        self.prod_tree.column("id", width=40, anchor='center')
        self.prod_tree.column("sku", width=110)
        self.prod_tree.column("name", width=260)
        self.prod_tree.column("category", width=120)
        self.prod_tree.column("qty", width=80, anchor='e')
        self.prod_tree.column("reorder", width=90, anchor='e')
        self.prod_tree.column("cost", width=100, anchor='e')
        self.prod_tree.pack(fill='both', expand=True, padx=6, pady=6)

        p_buttons = ttk.Frame(self.tab_products)
        p_buttons.pack(fill='x', pady=6)
        ttk.Button(p_buttons, text="Add Product", command=self.add_product_dialog).pack(side='left', padx=6)
        ttk.Button(p_buttons, text="Edit Product", command=self.edit_selected_product).pack(side='left', padx=6)
        ttk.Button(p_buttons, text="Delete Product", command=self.delete_selected_product).pack(side='left', padx=6)
        ttk.Button(p_buttons, text="Adjust Stock", command=self.adjust_stock_dialog).pack(side='left', padx=6)
        ttk.Button(p_buttons, text="Low Stock Alert", command=self.show_low_stock).pack(side='left', padx=6)

        # ---------- Suppliers tab ----------
        s_top = ttk.Frame(self.tab_suppliers)
        s_top.pack(fill='x', pady=6)
        ttk.Button(s_top, text="Add Supplier", command=self.add_supplier_dialog).pack(side='left', padx=6)
        ttk.Button(s_top, text="Refresh", command=self.refresh_suppliers).pack(side='left', padx=6)

        self.sup_tree = ttk.Treeview(self.tab_suppliers, columns=("id","name","phone","email"), show='headings', height=18)
        for c,w in (("id",50),("name",300),("phone",150),("email",250)):
            self.sup_tree.heading(c, text=c.title())
            self.sup_tree.column(c, width=w, anchor='w')
        self.sup_tree.pack(fill='both', expand=True, padx=6, pady=6)

        # ---------- POs tab ----------
        po_top = ttk.Frame(self.tab_pos)
        po_top.pack(fill='x', pady=6)
        ttk.Button(po_top, text="Create PO", command=self.create_po_dialog).pack(side='left', padx=6)
        ttk.Button(po_top, text="Refresh", command=self.refresh_pos).pack(side='left', padx=6)
        ttk.Button(po_top, text="Export POs to Excel", command=self.on_export_pos).pack(side='right', padx=6)

        self.po_tree = ttk.Treeview(self.tab_pos, columns=("id","po_no","supplier","date","total"), show='headings', height=16)
        self.po_tree.heading("id", text="ID")
        self.po_tree.column("id", width=50)
        self.po_tree.heading("po_no", text="PO No")
        self.po_tree.column("po_no", width=110)
        self.po_tree.heading("supplier", text="Supplier")
        self.po_tree.column("supplier", width=260)
        self.po_tree.heading("date", text="Date")
        self.po_tree.column("date", width=160)
        self.po_tree.heading("total", text="Total")
        self.po_tree.column("total", width=120, anchor='e')
        self.po_tree.pack(fill='both', expand=True, padx=6, pady=6)
        ttk.Button(self.tab_pos, text="View PO Items", command=self.view_po_items).pack(pady=6)

    # -----------------------
    # Product actions
    # -----------------------
    def refresh_products(self):
        rows = list_products()
        self.prod_tree.delete(*self.prod_tree.get_children())
        for r in rows:
            tag = ""
            if float(r[4]) <= float(r[5]):
                tag = "low"
            self.prod_tree.insert('', 'end', values=(r[0], r[1], r[2], r[3], float(r[4]), float(r[5]), float(r[6])), tags=(tag,))
        self.prod_tree.tag_configure("low", background="#ffe6e6")  # light red

    def on_search_products(self):
        q = self.prod_search.get().strip()
        rows = list_products(search=q)
        self.prod_tree.delete(*self.prod_tree.get_children())
        for r in rows:
            tag = ""
            if float(r[4]) <= float(r[5]):
                tag = "low"
            self.prod_tree.insert('', 'end', values=(r[0], r[1], r[2], r[3], float(r[4]), float(r[5]), float(r[6])), tags=(tag,))
        self.prod_tree.tag_configure("low", background="#ffe6e6")

    def on_clear_search(self):
        self.prod_search.set("")
        self.refresh_products()

    def add_product_dialog(self):
        dlg = ProductDialog(self)
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            sku, name, category, qty, reorder, cost = dlg.result
            pid = add_product(sku, name, category, qty, reorder, cost)
            if not pid:
                messagebox.showerror("Error", "SKU already exists or invalid data.")
            self.refresh_products()

    def edit_selected_product(self):
        sel = self.prod_tree.selection()
        if not sel:
            return
        iid = sel[0]
        vals = self.prod_tree.item(iid, "values")
        pid = int(vals[0])
        dlg = ProductDialog(self, prefill={
            "id": pid, "sku": vals[1], "name": vals[2], "category": vals[3],
            "qty": vals[4], "reorder": vals[5], "cost": vals[6]
        })
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            sku, name, category, qty, reorder, cost = dlg.result
            update_product(pid, sku, name, category, qty, reorder, cost)
            self.refresh_products()

    def delete_selected_product(self):
        sel = self.prod_tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("Confirm", "Delete selected product?"):
            return
        iid = sel[0]
        pid = int(self.prod_tree.item(iid, "values")[0])
        delete_product(pid)
        self.refresh_products()

    def adjust_stock_dialog(self):
        sel = self.prod_tree.selection()
        if not sel:
            return
        pid = int(self.prod_tree.item(sel[0], "values")[0])
        desc = simpledialog.askstring("Adjust Stock", "Reason (Sale/Return/Manual):", parent=self)
        if desc is None:
            return
        try:
            qty = float(simpledialog.askfloat("Quantity", "Qty change (use negative for reduce):", parent=self))
        except Exception:
            return
        adjust_stock(pid, qty, reason=desc)
        self.refresh_products()

    def show_low_stock(self):
        rows = low_stock_products()
        if not rows:
            messagebox.showinfo("Low Stock", "No low-stock products.")
            return
        top = tk.Toplevel(self)
        top.title("Low Stock Products")
        tree = ttk.Treeview(top, columns=("id","sku","name","qty","reorder"), show='headings')
        for h,w in (("id",50),("sku",120),("name",300),("qty",100),("reorder",100)):
            tree.heading(h, text=h.title())
            tree.column(h, width=w)
        tree.pack(fill='both', expand=True, padx=6, pady=6)
        for r in rows:
            tree.insert('', 'end', values=(r[0], r[1], r[2], float(r[3]), float(r[4])))
        ttk.Button(top, text="Close", command=top.destroy).pack(pady=6)

    def check_low_stock_startup(self):
        rows = low_stock_products()
        if rows:
            messagebox.showwarning("Low Stock Alert", f"There are {len(rows)} low-stock products. Open 'Products' tab and click 'Low Stock Alert' to view.")

    # -----------------------
    # Supplier actions
    # -----------------------
    def refresh_suppliers(self):
        rows = list_suppliers()
        self.sup_tree.delete(*self.sup_tree.get_children())
        for r in rows:
            self.sup_tree.insert('', 'end', values=(r[0], r[1], r[2], r[3]))

    def add_supplier_dialog(self):
        name = simpledialog.askstring("Supplier", "Name:", parent=self)
        if not name:
            return
        phone = simpledialog.askstring("Supplier", "Phone (optional):", parent=self) or ""
        email = simpledialog.askstring("Supplier", "Email (optional):", parent=self) or ""
        sid = add_supplier(name, phone, email)
        if not sid:
            messagebox.showerror("Error", "Supplier may already exist or invalid.")
        self.refresh_suppliers()

    # -----------------------
    # Purchase Order actions
    # -----------------------
    def refresh_pos(self):
        rows = list_purchase_orders()
        self.po_tree.delete(*self.po_tree.get_children())
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        for r in rows:
            cur.execute("SELECT name FROM suppliers WHERE id=?", (r[2],))
            sup = cur.fetchone()
            supname = sup[0] if sup else ""
            self.po_tree.insert('', 'end', values=(r[0], r[1], supname, r[3], float(r[4])))
        con.close()

    def create_po_dialog(self):
        # build dialog that selects supplier and products with qty/cost
        dlg = PODialog(self)
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            po_no, supplier_id, items = dlg.result
            try:
                pid = create_purchase_order(po_no, supplier_id, items)
                messagebox.showinfo("PO Created", f"PO {po_no} saved (id {pid}). Stock updated.")
                self.refresh_products()
                self.refresh_pos()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create PO: {e}")

    def view_po_items(self):
        sel = self.po_tree.selection()
        if not sel:
            return
        iid = sel[0]
        po_id = int(self.po_tree.item(iid, "values")[0])
        items = get_po_items(po_id)
        top = tk.Toplevel(self)
        top.title(f"PO Items - {po_id}")
        tree = ttk.Treeview(top, columns=("prod_id","sku","name","qty","cost","line"), show='headings', height=12)
        for h,w in (("prod_id",60),("sku",100),("name",300),("qty",80),("cost",100),("line",120)):
            tree.heading(h, text=h.title())
            tree.column(h, width=w)
        tree.pack(fill='both', expand=True, padx=6, pady=6)
        for it in items:
            tree.insert('', 'end', values=(it[1], it[2], it[3], float(it[4]), float(it[5]), float(it[6])))

    # -----------------------
    # Export actions
    # -----------------------
    def on_export_products(self):
        if Workbook is None:
            messagebox.showerror("Missing dependency", "Install openpyxl (pip install openpyxl) to export to Excel.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")], initialfile="products.xlsx")
        if not f:
            return
        try:
            export_products_to_excel(f)
            messagebox.showinfo("Exported", f"Products exported to {f}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def on_export_pos(self):
        if Workbook is None:
            messagebox.showerror("Missing dependency", "Install openpyxl (pip install openpyxl) to export to Excel.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")], initialfile="purchase_orders.xlsx")
        if not f:
            return
        try:
            export_pos_to_excel(f)
            messagebox.showinfo("Exported", f"POs exported to {f}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

# --------------------------
# Dialogs
# --------------------------
class ProductDialog(tk.Toplevel):
    def __init__(self, master, prefill=None):
        super().__init__(master)
        self.title("Product")
        self.result = None
        self.create_widgets(prefill)
        self.grab_set()

    def create_widgets(self, prefill):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill='both', expand=True)
        ttk.Label(frm, text="SKU:").grid(row=0, column=0, sticky='e')
        self.sku = tk.StringVar(value=(prefill.get("sku") if prefill else ""))
        ttk.Entry(frm, textvariable=self.sku, width=30).grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(frm, text="Name:").grid(row=1, column=0, sticky='e')
        self.name = tk.StringVar(value=(prefill.get("name") if prefill else ""))
        ttk.Entry(frm, textvariable=self.name, width=50).grid(row=1, column=1, padx=6, pady=4)
        ttk.Label(frm, text="Category:").grid(row=2, column=0, sticky='e')
        self.cat = tk.StringVar(value=(prefill.get("category") if prefill else ""))
        ttk.Entry(frm, textvariable=self.cat, width=30).grid(row=2, column=1, padx=6, pady=4)
        ttk.Label(frm, text="Qty:").grid(row=3, column=0, sticky='e')
        self.qty = tk.DoubleVar(value=(prefill.get("qty") if prefill else 0.0))
        ttk.Entry(frm, textvariable=self.qty, width=12).grid(row=3, column=1, padx=6, pady=4, sticky='w')
        ttk.Label(frm, text="Reorder Level:").grid(row=4, column=0, sticky='e')
        self.reorder = tk.DoubleVar(value=(prefill.get("reorder") if prefill else 0.0))
        ttk.Entry(frm, textvariable=self.reorder, width=12).grid(row=4, column=1, padx=6, pady=4, sticky='w')
        ttk.Label(frm, text="Cost Price:").grid(row=5, column=0, sticky='e')
        self.cost = tk.DoubleVar(value=(prefill.get("cost") if prefill else 0.0))
        ttk.Entry(frm, textvariable=self.cost, width=12).grid(row=5, column=1, padx=6, pady=4, sticky='w')

        btn = ttk.Frame(frm)
        btn.grid(row=6, column=0, columnspan=2, pady=8)
        ttk.Button(btn, text="Save", command=self.on_save).pack(side='left', padx=6)
        ttk.Button(btn, text="Cancel", command=self.destroy).pack(side='left', padx=6)

    def on_save(self):
        sku = self.sku.get().strip()
        name = self.name.get().strip()
        cat = self.cat.get().strip()
        try:
            qty = float(self.qty.get())
            reorder = float(self.reorder.get())
            cost = float(self.cost.get())
        except Exception:
            messagebox.showerror("Invalid", "Qty, Reorder and Cost must be numbers")
            return
        if not sku or not name:
            messagebox.showerror("Invalid", "SKU and Name are required")
            return
        self.result = (sku, name, cat, qty, reorder, cost)
        self.destroy()

class PODialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Create Purchase Order")
        self.result = None
        self.items = []  # list of dicts
        self.create_widgets()
        self.grab_set()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill='both', expand=True)

        top = ttk.Frame(frm)
        top.pack(fill='x', pady=4)
        ttk.Label(top, text="PO No:").grid(row=0, column=0, sticky='e')
        self.po_no_var = tk.StringVar(value=next_po_no())
        ttk.Entry(top, textvariable=self.po_no_var, width=16).grid(row=0, column=1, padx=6)
        ttk.Label(top, text="Supplier:").grid(row=0, column=2, sticky='e')
        self.supplier_cb = ttk.Combobox(top, values=[s[1] for s in list_suppliers()], state='readonly')
        self.supplier_cb.grid(row=0, column=3, padx=6)

        # product selection
        mid = ttk.Frame(frm)
        mid.pack(fill='x', pady=6)
        ttk.Label(mid, text="Product:").grid(row=0, column=0, sticky='e')
        prods = list_products()
        self.prod_map = {f"{p[2]} ({p[1]})": p for p in prods}  # display -> row
        self.prod_cb = ttk.Combobox(mid, values=list(self.prod_map.keys()), width=60)
        self.prod_cb.grid(row=0, column=1, columnspan=3, padx=6)
        ttk.Label(mid, text="Qty:").grid(row=1, column=0, sticky='e')
        self.qty_var = tk.DoubleVar(value=1.0)
        ttk.Entry(mid, textvariable=self.qty_var, width=12).grid(row=1, column=1, padx=6, sticky='w')
        ttk.Label(mid, text="Cost Price:").grid(row=1, column=2, sticky='e')
        self.cost_var = tk.DoubleVar(value=0.0)
        ttk.Entry(mid, textvariable=self.cost_var, width=12).grid(row=1, column=3, padx=6, sticky='w')
        ttk.Button(mid, text="Add Item", command=self.add_po_item).grid(row=2, column=3, sticky='e', padx=6, pady=6)

        # items tree
        cols = ("prod_id","sku","name","qty","cost","line")
        self.items_tree = ttk.Treeview(frm, columns=cols, show='headings', height=8)
        for c,w in (("prod_id",60),("sku",120),("name",300),("qty",80),("cost",100),("line",120)):
            self.items_tree.heading(c, text=c.title())
            self.items_tree.column(c, width=w)
        self.items_tree.pack(fill='both', expand=True, padx=6, pady=6)

        btns = ttk.Frame(frm)
        btns.pack(fill='x', pady=6)
        ttk.Button(btns, text="Remove Selected", command=self.remove_po_item).pack(side='left', padx=6)
        ttk.Button(btns, text="Create PO", command=self.create_po).pack(side='right', padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side='right', padx=6)

    def add_po_item(self):
        key = self.prod_cb.get()
        if not key or key not in self.prod_map:
            messagebox.showerror("Choose product", "Select a valid product")
            return
        try:
            qty = float(self.qty_var.get())
            cost = float(self.cost_var.get())
        except Exception:
            messagebox.showerror("Invalid", "Qty and Cost should be numbers")
            return
        prod = self.prod_map[key]
        item = {"product_id": prod[0], "sku": prod[1], "name": prod[2], "qty": qty, "cost_price": cost}
        self.items.append(item)
        line_total = float(Decimal(qty * Decimal(cost)).quantize(Decimal("0.01")))
        self.items_tree.insert('', 'end', values=(prod[0], prod[1], prod[2], qty, cost, line_total))

    def remove_po_item(self):
        sel = self.items_tree.selection()
        if not sel:
            return
        idx = self.items_tree.index(sel[0])
        self.items_tree.delete(sel[0])
        if 0 <= idx < len(self.items):
            del self.items[idx]

    def create_po(self):
        po_no = self.po_no_var.get().strip()
        sup_name = self.supplier_cb.get().strip()
        if not po_no or not sup_name or not self.items:
            messagebox.showerror("Missing", "PO No, Supplier and at least one item required")
            return
        # get supplier id
        sup = [s for s in list_suppliers() if s[1] == sup_name]
        if not sup:
            messagebox.showerror("Supplier", "Choose a valid supplier (or add one first)")
            return
        supplier_id = sup[0][0]
        # prepare items
        items = []
        for it in self.items:
            items.append({"product_id": it["product_id"], "qty": it["qty"], "cost_price": it["cost_price"]})
        self.result = (po_no, supplier_id, items)
        self.destroy()

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    init_db()
    seed_sample_data() 
    app = InventoryApp()
    app.mainloop()
