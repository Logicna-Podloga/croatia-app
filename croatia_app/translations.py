import os
import frappe
import polib
from frappe.translate import get_translation_dict_from_file

def setup_translations():
    """Setup Croatian translations for ERPNext"""
    frappe.utils.logger.set_log_level("DEBUG")
    frappe.logger().debug("Setting up Croatian translations")

    # Register Croatian language if not already registered
    if not frappe.db.exists("Language", "hr"):
        lang = frappe.get_doc({
            "doctype": "Language",
            "language_name": "Croatian",
            "language_code": "hr",
            "enabled": 1
        })
        lang.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info("Croatian language registered")

def get_translation_path():
    """Return the path to translation files"""
    app_path = frappe.get_app_path("croatia_app")
    return os.path.join(app_path, "translations")

def load_hr_translations():
    """Load Croatian translations from PO file"""
    translation_path = get_translation_path()
    hr_file = os.path.join(translation_path, "hr.po")

    if os.path.exists(hr_file):
        translations = {}
        po = polib.pofile(hr_file)

        for entry in po:
            if entry.msgstr and not entry.obsolete:
                # Using the msgid as key and msgstr as value
                translations[entry.msgid] = entry.msgstr

                # If there's a context, use it too (Frappe format uses tuple with source and context)
                if entry.msgctxt:
                    translations[(entry.msgid, entry.msgctxt)] = entry.msgstr

        return translations

    return {}

def po_to_dict(po_file):
    """Convert PO file to translation dictionary"""
    translations = {}
    po = polib.pofile(po_file)

    for entry in po:
        if entry.msgstr and not entry.obsolete:
            translations[entry.msgid] = entry.msgstr
            if entry.msgctxt:
                translations[(entry.msgid, entry.msgctxt)] = entry.msgstr

    return translations
