# croatia_app/utils/translation_utils.py

import os
import polib
import frappe
from frappe.translate import get_messages_for_app

def extract_messages_from_erpnext():
    """Extract all translatable strings from ERPNext and save them to a PO file"""
    messages = get_messages_for_app("erpnext")
    target_path = os.path.join(frappe.get_app_path("croatia_app"),
                              "translations", "erpnext_messages.po")

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Create a new PO file
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': 'ERPNext Croatian Translation',
        'Language': 'hr',
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

    # Add messages to PO file - Fixed to properly handle different message types
    for message in messages:
        try:
            # Handle different message formats
            if isinstance(message, tuple) and len(message) >= 2:
                # It's a (msgid, context) tuple
                entry = polib.POEntry(
                    msgid=str(message[0]),  # Convert to string to be safe
                    msgctxt=str(message[1]) if message[1] else None  # Handle None context
                )
            elif isinstance(message, str):
                # It's a simple string message
                entry = polib.POEntry(
                    msgid=message
                )
            else:
                # It's some other format, convert to string
                entry = polib.POEntry(
                    msgid=str(message)
                )

            po.append(entry)
        except Exception as e:
            frappe.logger().error(f"Error processing message {message}: {str(e)}")
            continue

    # Save the PO file
    po.save(target_path)

    return target_path

def merge_translations(custom_po_file, erpnext_po_file, output_file):
    """Merge custom translations with ERPNext messages"""
    # Load custom translations
    custom_po = polib.pofile(custom_po_file)

    # Create a dictionary of custom translations
    custom_translations = {}
    for entry in custom_po:
        if entry.msgctxt:
            key = (entry.msgid, entry.msgctxt)
        else:
            key = entry.msgid

        if entry.msgstr:
            custom_translations[key] = entry.msgstr

    # Load ERPNext messages
    erpnext_po = polib.pofile(erpnext_po_file)

    # Create merged PO file
    merged_po = polib.POFile()
    merged_po.metadata = {
        'Project-Id-Version': 'ERPNext Croatian Translation',
        'Language': 'hr',
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

    # Process entries from ERPNext
    for entry in erpnext_po:
        # Create a new entry for the merged file to avoid reference issues
        new_entry = polib.POEntry(
            msgid=entry.msgid,
            msgctxt=entry.msgctxt,
            msgstr=''
        )

        # Check if we have a custom translation
        key = entry.msgid
        if entry.msgctxt:
            key = (entry.msgid, entry.msgctxt)

        if key in custom_translations:
            new_entry.msgstr = custom_translations[key]

        # Add to merged file
        merged_po.append(new_entry)

    # Save merged file
    merged_po.save(output_file)

    return output_file

def generate_complete_hr_translation():
    """Generate complete Croatian translation file for ERPNext"""
    # Get all translatable strings from ERPNext
    erpnext_po_file = extract_messages_from_erpnext()

    # Get path to our custom translations
    app_path = frappe.get_app_path("croatia_app")
    custom_po_file = os.path.join(app_path, "translations", "hr.po")

    # Merge translations
    output_file = os.path.join(app_path, "translations", "hr-complete.po")

    # Check if custom PO file exists
    if not os.path.exists(custom_po_file):
        frappe.logger().warning(f"Custom translation file {custom_po_file} not found. Creating empty file.")
        # Create an empty PO file
        po = polib.POFile()
        po.metadata = {
            'Project-Id-Version': 'ERPNext Croatian Translation',
            'Language': 'hr',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }
        po.save(custom_po_file)

    # Merge translations
    merge_translations(custom_po_file, erpnext_po_file, output_file)

    return output_file

def update_translations():
    """Command to update translations - can be run from bench console"""
    frappe.logger().info("Updating Croatian translations")
    output_file = generate_complete_hr_translation()
    frappe.logger().info(f"Updated translations saved to {output_file}")

    # Clear translation cache
    frappe.translate.clear_cache()
    return f"Updated translations saved to {output_file}"

def create_initial_po_file():
    """Create an initial PO file with common accounting terms"""
    app_path = frappe.get_app_path("croatia_app")
    po_file = os.path.join(app_path, "translations", "hr.po")

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(po_file), exist_ok=True)

    # Create PO file
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': 'ERPNext Croatian Translation',
        'Language': 'hr',
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

    # Define common accounting terms
    accounting_terms = [
        ("Accounting", "Računovodstvo"),
        ("Account", "Račun"),
        ("Accounts", "Računi"),
        ("Address", "Adresa"),
        ("Amount", "Iznos"),
        ("Asset", "Imovina"),
        ("Assets", "Imovina"),
        ("Balance", "Saldo"),
        ("Balance Sheet", "Bilanca"),
        ("Bank", "Banka"),
        ("Bank Account", "Bankovni račun"),
        ("Bill", "Račun"),
        ("Cancel", "Otkaži"),
        ("Cash", "Gotovina"),
        ("Chart of Accounts", "Kontni plan"),
        ("City", "Grad"),
        ("Company", "Tvrtka"),
        ("Contact", "Kontakt"),
        ("Cost", "Trošak"),
        ("Cost Center", "Mjesto troška"),
        ("Country", "Država"),
        ("Credit", "Kredit"),
        ("Credit Note", "Knjižno odobrenje"),
        ("Currency", "Valuta"),
        ("Customer", "Kupac"),
        ("Customers", "Kupci"),
        ("Date", "Datum"),
        ("Day", "Dan"),
        ("Debit", "Duguje"),
        ("Debit Note", "Knjižno zaduženje"),
        ("Default", "Zadano"),
        ("Delete", "Izbriši"),
        ("Description", "Opis"),
        ("Discount", "Popust"),
        ("Document", "Dokument"),
        ("Documents", "Dokumenti"),
        ("Draft", "Nacrt"),
        ("Due Date", "Datum dospijeća"),
        ("Email", "E-pošta"),
        ("Employee", "Zaposlenik"),
        ("Employees", "Zaposlenici"),
        ("Expense", "Trošak"),
        ("Expenses", "Troškovi"),
        ("File", "Datoteka"),
        ("Filter", "Filter"),
        ("Financial Year", "Financijska godina"),
        ("From Date", "Od datuma"),
        ("General Ledger", "Glavna knjiga"),
        ("Grand Total", "Ukupno"),
        ("Group", "Grupa"),
        ("GST", "PDV"),
        ("Hour", "Sat"),
        ("Income", "Prihod"),
        ("Invoice", "Račun"),
        ("Invoices", "Računi"),
        ("Item", "Stavka"),
        ("Items", "Stavke"),
        ("Journal Entry", "Temeljnica"),
        ("Ledger", "Knjiga"),
        ("List", "Popis"),
        ("Management", "Upravljanje"),
        ("Manager", "Menadžer"),
        ("Margin", "Marža"),
        ("Month", "Mjesec"),
        ("Name", "Naziv"),
        ("Net Total", "Ukupno neto"),
        ("Number", "Broj"),
        ("Order", "Narudžba"),
        ("Orders", "Narudžbe"),
        ("Outstanding Amount", "Nepodmireni iznos"),
        ("Paid", "Plaćeno"),
        ("Pay", "Plati"),
        ("Payment", "Plaćanje"),
        ("Payment Entry", "Unos plaćanja"),
        ("Period", "Razdoblje"),
        ("Phone", "Telefon"),
        ("Postal Code", "Poštanski broj"),
        ("Price", "Cijena"),
        ("Print", "Ispis"),
        ("Profit", "Dobit"),
        ("Profit and Loss", "Račun dobiti i gubitka"),
        ("Project", "Projekt"),
        ("Projects", "Projekti"),
        ("Purchase", "Nabava"),
        ("Purchase Invoice", "Ulazni račun"),
        ("Purchase Order", "Narudžba dobavljaču"),
        ("Quantity", "Količina"),
        ("Rate", "Stopa"),
        ("Receipt", "Primka"),
        ("Reference", "Referenca"),
        ("Report", "Izvještaj"),
        ("Reports", "Izvještaji"),
        ("Sales", "Prodaja"),
        ("Sales Invoice", "Izlazni račun"),
        ("Sales Order", "Prodajni nalog"),
        ("Save", "Spremi"),
        ("Settings", "Postavke"),
        ("State", "Županija"),
        ("Status", "Status"),
        ("Stock", "Zaliha"),
        ("Submit", "Potvrdi"),
        ("Supplier", "Dobavljač"),
        ("Suppliers", "Dobavljači"),
        ("Tax", "Porez"),
        ("Taxes", "Porezi"),
        ("Taxes and Charges", "Porezi i naknade"),
        ("To Date", "Do datuma"),
        ("Total", "Ukupno"),
        ("Total Amount", "Ukupni iznos"),
        ("Type", "Vrsta"),
        ("Unit", "Jedinica"),
        ("User", "Korisnik"),
        ("VAT", "PDV"),
        ("View", "Pregledaj"),
        ("Warehouse", "Skladište"),
        ("Week", "Tjedan"),
        ("Year", "Godina"),
    ]

    # Add entries to PO file
    for english, croatian in accounting_terms:
        entry = polib.POEntry(
            msgid=english,
            msgstr=croatian,
            comment="Accounting term"
        )
        po.append(entry)

    # Save PO file
    po.save(po_file)

    return po_file
