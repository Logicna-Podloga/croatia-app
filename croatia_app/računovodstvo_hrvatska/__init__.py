# croatia_app/računovodstvo_hrvatska/translations/__init__.py

import os
import frappe
import csv
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
    return os.path.join(app_path, "računovodstvo_hrvatska", "translations")

def load_hr_translations():
    """Load Croatian translations"""
    translation_path = get_translation_path()
    hr_file = os.path.join(translation_path, "hr.csv")

    if os.path.exists(hr_file):
        return get_translation_dict_from_file(hr_file, "hr")

    return {}
