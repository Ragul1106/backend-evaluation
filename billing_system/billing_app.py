
import os
import sys
import sqlite3
import datetime
import csv
from decimal import Decimal, ROUND_HALF_UP
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

DB_FILE = "billing.db"

def money(x):
    return Decimal(x).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def init_db():
    """
    Initialise DB. Create tables if missing.
    Also perform a tiny migration: if 'pdf_path' column is missing in invoices,
    add it (so older DB files are upgraded).
    """
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    # Create invoices table if it doesn't exist (older DB may have this without pdf_path)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE,
        date TEXT,
        customer_name TEXT,
        customer_phone TEXT,
        customer_address TEXT,
        total_taxable REAL,
        total_gst REAL,
        total_amount REAL
        -- pdf_path may be added below if missing
    )
    """)

    # Ensure invoice_items exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        description TEXT,
        qty REAL,
        rate REAL,
        gst_percent REAL,
        taxable_value REAL,
        gst_amount REAL,
        total REAL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )
    """)

    # Check columns in invoices table and add pdf_path if it's not present
    cur.execute("PRAGMA table_info(invoices)")
    cols = [row[1] for row in cur.fetchall()]  # row[1] is column name
    if 'pdf_path' not in cols:
        try:
            cur.execute("ALTER TABLE invoices ADD COLUMN pdf_path TEXT")
            # if you want to preserve older invoices' PDFs, this column will be NULL
        except Exception as e:
            # If ALTER TABLE fails for some reason, print/log but continue
            print("Warning: failed to add pdf_path column:", e)

    con.commit()
    con.close()


def insert_invoice(invoice_no, date_iso, customer_name, customer_phone, customer_address,
                   total_taxable, total_gst, total_amount, items, pdf_path=None):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO invoices(invoice_no, date, customer_name, customer_phone, customer_address,
                             total_taxable, total_gst, total_amount, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (invoice_no, date_iso, customer_name, customer_phone, customer_address,
          float(total_taxable), float(total_gst), float(total_amount), pdf_path))
    invoice_id = cur.lastrowid
    for it in items:
        cur.execute("""
            INSERT INTO invoice_items(invoice_id, description, qty, rate, gst_percent, taxable_value, gst_amount, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_id, it['description'], float(it['qty']), float(it['rate']),
              float(it['gst_percent']), float(it['taxable_value']),
              float(it['gst_amount']), float(it['total'])))
    con.commit()
    con.close()
    return invoice_id

def fetch_sales_by_date(date_from, date_to):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT invoice_no, date, customer_name, total_taxable, total_gst, total_amount
        FROM invoices
        WHERE date BETWEEN ? AND ?
        ORDER BY date ASC
    """, (date_from, date_to))
    rows = cur.fetchall()
    con.close()
    return rows

def fetch_all_invoices():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT id, invoice_no, date, customer_name, total_amount, pdf_path
        FROM invoices
        ORDER BY date DESC, id DESC
    """)
    rows = cur.fetchall()
    con.close()
    return rows

def fetch_invoice_items(invoice_id):
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT description, qty, rate, gst_percent, taxable_value, gst_amount, total
        FROM invoice_items
        WHERE invoice_id = ?
    """, (invoice_id,))
    rows = cur.fetchall()
    con.close()
    return rows

# ---------------------------
# PDF Generation (reportlab)
# ---------------------------
def generate_pdf(invoice_no, date_str, customer_name, customer_phone, customer_address, items, totals, filename):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    story = []

    # ---- Header ----
    story.append(Paragraph("<b>Ice Land</b>", styles['Title']))
    story.append(Paragraph("Web: www.ice-land.com\nEmail: 7G2tI@example.com\nPhone: 123-456-7890\nAddress: Chennai, Tamilnadu", styles['Normal']))
    story.append(Paragraph("GSTIN: 12ABCDE3456F7Z8", styles['Normal']))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"<b>Invoice No:</b> {invoice_no}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {date_str}", styles['Normal']))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"<b>Bill To:</b> {customer_name}", styles['Normal']))
    if customer_phone:
        story.append(Paragraph(f"Phone: {customer_phone}", styles['Normal']))
    if customer_address:
        story.append(Paragraph(customer_address.replace("\n", "<br/>"), styles['Normal']))
    story.append(Spacer(1, 10))

    # ---- Table of items ----
    # Fit table inside 180 mm width (A4 = 210 mm, with 15 mm margins each side)
    col_widths = [12*mm, 60*mm, 15*mm, 20*mm, 23*mm, 18*mm, 23*mm, 24*mm]

    data = [["S.No", "Description", "Qty", "Rate", "Taxable", "GST %", "GST Amt", "Total"]]
    for i, it in enumerate(items, start=1):
        data.append([
            str(i),
            it['description'],
            str(it['qty']),
            f"{money(it['rate'])}",
            f"{money(it['taxable_value'])}",
            f"{money(it['gst_percent'])}%",
            f"{money(it['gst_amount'])}",
            f"{money(it['total'])}"
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # ---- Totals ----
    story.append(Paragraph(f"<b>Taxable Total:</b> {money(totals['total_taxable'])}", styles['Normal']))
    story.append(Paragraph(f"<b>Total GST:</b> {money(totals['total_gst'])}", styles['Normal']))
    story.append(Paragraph(f"<b>Grand Total:</b> INR {money(totals['total_amount'])}", styles['Heading2']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Thank you for your business!", styles['Normal']))

    doc.build(story)


# ---------------------------
# GUI
# ---------------------------
class BillingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Billing & Invoice Management System")
        self.geometry("1000x700")
        self.style = ttk.Style(self)
        # data
        self.items = []
        self.next_invoice_number = self._get_next_invoice_number()
        self.invoice_date_var = tk.StringVar(value=datetime.date.today().isoformat())
        self.last_pdf_path = None
        # build
        self.create_widgets()

    def _get_next_invoice_number(self):
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute("SELECT invoice_no FROM invoices ORDER BY id DESC LIMIT 1")
        r = cur.fetchone()
        con.close()
        if not r:
            return "INV0001"
        last = r[0]
        import re
        m = re.search(r'(\d+)$', last)
        if m:
            n = int(m.group(1)) + 1
            return f"INV{n:04d}"
        else:
            return last + "_1"

    def create_widgets(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill='both', expand=True)

        # Top: invoice meta
        meta = ttk.LabelFrame(frm, text="Invoice Details", padding=8)
        meta.pack(fill='x', padx=4, pady=4)

        ttk.Label(meta, text="Invoice No:").grid(row=0, column=0, sticky='w', padx=3, pady=2)
        self.invoice_no_var = tk.StringVar(value=self.next_invoice_number)
        ttk.Entry(meta, width=18, textvariable=self.invoice_no_var).grid(row=0, column=1, padx=3, pady=2)
        ttk.Label(meta, text="Date (YYYY-MM-DD):").grid(row=0, column=2, sticky='w', padx=3, pady=2)
        ttk.Entry(meta, width=15, textvariable=self.invoice_date_var).grid(row=0, column=3, padx=3, pady=2)

        ttk.Label(meta, text="Customer Name:").grid(row=1, column=0, sticky='w', pady=6)
        self.cust_name_var = tk.StringVar()
        ttk.Entry(meta, width=30, textvariable=self.cust_name_var).grid(row=1, column=1, columnspan=2, sticky='w', padx=3)

        ttk.Label(meta, text="Phone:").grid(row=1, column=3, sticky='w', padx=3)
        self.cust_phone_var = tk.StringVar()
        ttk.Entry(meta, width=20, textvariable=self.cust_phone_var).grid(row=1, column=4, padx=3)

        ttk.Label(meta, text="Address:").grid(row=2, column=0, sticky='nw', pady=6)
        self.cust_addr = tk.Text(meta, width=60, height=3)
        self.cust_addr.grid(row=2, column=1, columnspan=4, pady=6, sticky='w')

        # Items area
        items_frame = ttk.LabelFrame(frm, text="Items", padding=8)
        items_frame.pack(fill='both', expand=True, padx=4, pady=4)

        # input row (keep all controls visible by placing in same grid row)
        ttk.Label(items_frame, text="Description:").grid(row=0, column=0, sticky='w', padx=3)
        self.desc_var = tk.StringVar()
        ttk.Entry(items_frame, width=44, textvariable=self.desc_var).grid(row=0, column=1, padx=3)

        ttk.Label(items_frame, text="Qty:").grid(row=0, column=2, sticky='w', padx=3)
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(items_frame, width=6, textvariable=self.qty_var).grid(row=0, column=3, padx=3)

        ttk.Label(items_frame, text="Rate:").grid(row=0, column=4, sticky='w', padx=3)
        self.rate_var = tk.StringVar(value="0.00")
        ttk.Entry(items_frame, width=10, textvariable=self.rate_var).grid(row=0, column=5, padx=3)

        ttk.Label(items_frame, text="GST %:").grid(row=0, column=6, sticky='w', padx=3)
        self.gst_var = tk.StringVar(value="18")
        ttk.Entry(items_frame, width=6, textvariable=self.gst_var).grid(row=0, column=7, padx=3)

        # Add Item button — make sure it's visible by using grid and padding
        self.add_item_btn = ttk.Button(items_frame, text="Add Item", command=self.add_item)
        self.add_item_btn.grid(row=0, column=8, padx=8, pady=2, sticky='w')

        # Treeview for items with sensible widths
        cols = ("description", "qty", "rate", "taxable", "gst_percent", "gst_amount", "total")
        self.tree = ttk.Treeview(items_frame, columns=cols, show='headings', height=10)
        widths = [420, 60, 80, 100, 80, 100, 120]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=w, anchor='center')
        # make description left aligned
        self.tree.column("description", anchor='w')
        self.tree.grid(row=1, column=0, columnspan=9, pady=8, sticky='nsew')

        # allow the tree to expand when the window resizes
        items_frame.grid_rowconfigure(1, weight=1)
        for i in range(9):
            items_frame.grid_columnconfigure(i, weight=0)
        items_frame.grid_columnconfigure(1, weight=1)  # description column expands

        ttk.Button(items_frame, text="Remove Selected", command=self.remove_selected).grid(row=2, column=0, pady=4, sticky='w', padx=3)

        # Totals area
        totals_frame = ttk.Frame(frm)
        totals_frame.pack(fill='x', padx=4, pady=4)

        ttk.Label(totals_frame, text="Total Taxable:").grid(row=0, column=0, sticky='e')
        self.total_taxable_var = tk.StringVar(value="0.00")
        ttk.Label(totals_frame, textvariable=self.total_taxable_var).grid(row=0, column=1, sticky='w', padx=6)

        ttk.Label(totals_frame, text="Total GST:").grid(row=0, column=2, sticky='e')
        self.total_gst_var = tk.StringVar(value="0.00")
        ttk.Label(totals_frame, textvariable=self.total_gst_var).grid(row=0, column=3, sticky='w', padx=6)

        ttk.Label(totals_frame, text="Grand Total:").grid(row=0, column=4, sticky='e')
        self.grand_total_var = tk.StringVar(value="0.00")
        ttk.Label(totals_frame, textvariable=self.grand_total_var, font=('TkDefaultFont', 12, 'bold')).grid(row=0, column=5, sticky='w', padx=6)

        # Actions area
        actions = ttk.Frame(frm)
        actions.pack(fill='x', padx=4, pady=6)

        self.generate_invoice_button = ttk.Button(actions, text="Save & Generate PDF", command=self.save_and_generate)
        self.generate_invoice_button.pack(side='left', padx=6)
        ttk.Button(actions, text="Print Last PDF", command=self.print_last_pdf).pack(side='left', padx=6)
        ttk.Button(actions, text="Clear Invoice", command=self.clear_invoice).pack(side='left', padx=6)

        # Reports
        rep_frame = ttk.LabelFrame(frm, text="Reports", padding=8)
        rep_frame.pack(fill='x', padx=4, pady=6)

        ttk.Label(rep_frame, text="From:").grid(row=0, column=0)
        self.rep_from = tk.StringVar(value=(datetime.date.today().replace(day=1).isoformat()))
        ttk.Entry(rep_frame, textvariable=self.rep_from, width=12).grid(row=0, column=1, padx=4)

        ttk.Label(rep_frame, text="To:").grid(row=0, column=2)
        self.rep_to = tk.StringVar(value=(datetime.date.today().isoformat()))
        ttk.Entry(rep_frame, textvariable=self.rep_to, width=12).grid(row=0, column=3, padx=4)

        ttk.Button(rep_frame, text="Show Report", command=self.show_report).grid(row=0, column=4, padx=6)
        ttk.Button(rep_frame, text="Export CSV", command=self.export_report_csv).grid(row=0, column=5, padx=6)
        ttk.Button(rep_frame, text="View Invoices", command=self.view_invoices).grid(row=0, column=6, padx=6)


    def add_item(self):
        desc = self.desc_var.get().strip()
        try:
            qty = Decimal(self.qty_var.get())
        except:
            messagebox.showerror("Invalid", "Quantity must be numeric")
            return
        try:
            rate = Decimal(self.rate_var.get())
        except:
            messagebox.showerror("Invalid", "Rate must be numeric")
            return
        try:
            gst_percent = Decimal(self.gst_var.get())
        except:
            messagebox.showerror("Invalid", "GST % must be numeric")
            return

        if not desc:
            messagebox.showerror("Invalid", "Description required")
            return

        taxable = money(qty * rate)
        gst_amount = money(taxable * gst_percent / Decimal('100'))
        total = money(taxable + gst_amount)

        item = {
            'description': desc,
            'qty': float(qty),
            'rate': float(rate),
            'gst_percent': float(gst_percent),
            'taxable_value': float(taxable),
            'gst_amount': float(gst_amount),
            'total': float(total)
        }
        self.items.append(item)
        self.tree.insert('', 'end', values=(
            item['description'],
            str(qty),
            f"{money(item['rate'])}",
            f"{money(item['taxable_value'])}",
            f"{money(item['gst_percent'])}%",
            f"{money(item['gst_amount'])}",
            f"{money(item['total'])}"
        ))
        self._recalc_totals()

        # clear inputs for next item
        self.desc_var.set("")
        self.qty_var.set("1")
        self.rate_var.set("0.00")
        self.gst_var.set("18")

    def remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        self.tree.delete(sel[0])
        if 0 <= idx < len(self.items):
            del self.items[idx]
        self._recalc_totals()

    def _recalc_totals(self):
        total_taxable = Decimal('0.00')
        total_gst = Decimal('0.00')
        total_amount = Decimal('0.00')
        for it in self.items:
            total_taxable += money(it['taxable_value'])
            total_gst += money(it['gst_amount'])
            total_amount += money(it['total'])
        self.total_taxable_var.set(f"{money(total_taxable)}")
        self.total_gst_var.set(f"{money(total_gst)}")
        self.grand_total_var.set(f"{money(total_amount)}")

    def save_and_generate(self):
        if not self.items:
            messagebox.showerror("No items", "Add at least one item to invoice.")
            return
        invoice_no = self.invoice_no_var.get().strip()
        if not invoice_no:
            messagebox.showerror("Missing", "Invoice number required.")
            return
        date_str = self.invoice_date_var.get().strip()
        try:
            dt = datetime.datetime.fromisoformat(date_str)
        except Exception:
            messagebox.showerror("Invalid date", "Enter date as YYYY-MM-DD")
            return

        customer_name = self.cust_name_var.get().strip()
        customer_phone = self.cust_phone_var.get().strip()
        customer_address = self.cust_addr.get("1.0", "end").strip()

        total_taxable = Decimal(self.total_taxable_var.get())
        total_gst = Decimal(self.total_gst_var.get())
        total_amount = Decimal(self.grand_total_var.get())

        suggested = f"invoice_{invoice_no}.pdf"
        f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")],
                                         initialfile=suggested)
        if not f:
            pdf_path = None
        else:
            pdf_path = f

        try:
            invoice_id = insert_invoice(invoice_no, dt.date().isoformat(), customer_name, customer_phone, customer_address,
                         total_taxable, total_gst, total_amount, self.items, pdf_path)
        except sqlite3.IntegrityError as e:
            messagebox.showerror("DB Error", f"Invoice no exists. Choose a different number. ({e})")
            return
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        # Generate PDF if path chosen
        if pdf_path:
            totals = {'total_taxable': total_taxable, 'total_gst': total_gst, 'total_amount': total_amount}
            try:
                generate_pdf(invoice_no, date_str, customer_name, customer_phone, customer_address, self.items, totals, pdf_path)
                self.last_pdf_path = pdf_path
                messagebox.showinfo("Saved", f"Invoice saved (ID {invoice_id}) and PDF generated at:\n{pdf_path}")
            except Exception as e:
                messagebox.showwarning("Saved (no PDF)", f"Invoice saved but PDF generation failed:\n{e}")
        else:
            messagebox.showinfo("Saved", f"Invoice saved (ID {invoice_id}) without PDF (you cancelled save location).")

        # bump invoice number and clear current invoice
        self.next_invoice_number = self._get_next_invoice_number()
        self.invoice_no_var.set(self.next_invoice_number)
        self.clear_invoice_items()

    def print_last_pdf(self):
        if not self.last_pdf_path or not os.path.exists(self.last_pdf_path):
            messagebox.showwarning("No PDF", "No PDF available to print. Generate one first.")
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(self.last_pdf_path, "print")
            elif sys.platform.startswith('darwin'):
                os.system(f"lp '{self.last_pdf_path}'")
            else:
                os.system(f"lpr '{self.last_pdf_path}'")
            messagebox.showinfo("Print", "Print command sent (depends on system configuration).")
        except Exception as e:
            messagebox.showerror("Print error", str(e))

    def clear_invoice_items(self):
        self.items = []
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._recalc_totals()
        self.cust_name_var.set("")
        self.cust_phone_var.set("")
        self.cust_addr.delete("1.0", "end")

    def clear_invoice(self):
        if messagebox.askyesno("Confirm", "Clear all fields and start new invoice?"):
            self.invoice_no_var.set(self._get_next_invoice_number())
            self.invoice_date_var.set(datetime.date.today().isoformat())
            self.clear_invoice_items()

    def show_report(self):
        from_date = self.rep_from.get().strip()
        to_date = self.rep_to.get().strip()
        try:
            df = datetime.date.fromisoformat(from_date)
            dt = datetime.date.fromisoformat(to_date)
        except:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD for report dates")
            return
        rows = fetch_sales_by_date(df.isoformat(), dt.isoformat())
        if not rows:
            messagebox.showinfo("Report", "No invoices in selected range.")
            return
        top = tk.Toplevel(self)
        top.title(f"Sales Report: {from_date} to {to_date}")
        cols = ("invoice_no", "date", "customer", "taxable", "gst", "total")
        tree = ttk.Treeview(top, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c.title())
            tree.column(c, anchor='center')
        tree.pack(fill='both', expand=True)
        sum_taxable = Decimal('0.00')
        sum_gst = Decimal('0.00')
        sum_total = Decimal('0.00')
        for r in rows:
            tree.insert('', 'end', values=(r[0], r[1], r[2] or "", money(r[3]), money(r[4]), money(r[5])))
            sum_taxable += money(r[3])
            sum_gst += money(r[4])
            sum_total += money(r[5])
        footer = ttk.Frame(top)
        footer.pack(fill='x')
        ttk.Label(footer, text=f"Total Taxable: {money(sum_taxable)}").pack(side='left', padx=8)
        ttk.Label(footer, text=f"Total GST: {money(sum_gst)}").pack(side='left', padx=8)
        ttk.Label(footer, text=f"Grand Total: {money(sum_total)}").pack(side='left', padx=8)

    def export_report_csv(self):
        from_date = self.rep_from.get().strip()
        to_date = self.rep_to.get().strip()
        try:
            df = datetime.date.fromisoformat(from_date)
            dt = datetime.date.fromisoformat(to_date)
        except:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD for report dates")
            return
        rows = fetch_sales_by_date(df.isoformat(), dt.isoformat())
        if not rows:
            messagebox.showinfo("Export", "No invoices in selected range.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not f:
            return
        with open(f, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(["Invoice No", "Date", "Customer", "Total Taxable", "Total GST", "Total Amount"])
            for r in rows:
                w.writerow([r[0], r[1], r[2], r[3], r[4], r[5]])
        messagebox.showinfo("Exported", f"Report exported to {f}")

    def view_invoices(self):
        rows = fetch_all_invoices()
        if not rows:
            messagebox.showinfo("Invoices", "No invoices found.")
            return
        top = tk.Toplevel(self)
        top.title("Saved Invoices")
        cols = ("id", "invoice_no", "date", "customer", "total", "pdf")
        tree = ttk.Treeview(top, columns=cols, show='headings', height=12)
        for c in cols:
            tree.heading(c, text=c.title())
            tree.column(c, anchor='center')
        tree.column("customer", width=200, anchor='w')
        tree.pack(fill='both', expand=True)

        for r in rows:
            pid = r[0]
            tree.insert('', 'end', values=(pid, r[1], r[2], r[3] or "", money(r[4]), r[5] or ""))

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill='x', pady=6)
        def open_selected_pdf():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])['values']
            pdf_path = item[5]
            if not pdf_path:
                messagebox.showinfo("No PDF", "No PDF was saved for this invoice.")
                return
            if not os.path.exists(pdf_path):
                messagebox.showerror("Missing", f"PDF file not found:\n{pdf_path}")
                return
            if sys.platform.startswith('win'):
                os.startfile(pdf_path)
            elif sys.platform.startswith('darwin'):
                os.system(f"open '{pdf_path}'")
            else:
                os.system(f"xdg-open '{pdf_path}'")
        ttk.Button(btn_frame, text="Open PDF", command=open_selected_pdf).pack(side='left', padx=6)
        def show_items():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])['values']
            invoice_id = item[0]
            items = fetch_invoice_items(invoice_id)
            t = tk.Toplevel(top)
            t.title(f"Items for Invoice {item[1]}")
            tcols = ("description", "qty", "rate", "gst", "taxable", "gst_amt", "total")
            tview = ttk.Treeview(t, columns=tcols, show='headings')
            for c in tcols:
                tview.heading(c, text=c.title())
                tview.column(c, anchor='center')
            tview.column("description", anchor='w', width=300)
            tview.pack(fill='both', expand=True)
            for it in items:
                tview.insert('', 'end', values=(it[0], it[1], money(it[2]), money(it[3]), money(it[4]), money(it[5]), money(it[6])))
        ttk.Button(btn_frame, text="Show Items", command=show_items).pack(side='left', padx=6)

if __name__ == "__main__":
    init_db()
    app = BillingApp()
    app.mainloop()