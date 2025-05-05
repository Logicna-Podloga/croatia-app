import frappe
from frappe.utils import cstr

def after_install():
    """Run after app installation"""
    try:
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

        # Automatically run the distribute process
        from croatia_app.utils.po_utils import distribute_po_files, run_translation_commands

        frappe.logger().info("Distributing Croatian translation files...")
        processed = distribute_po_files()
        if processed:
            frappe.logger().info(f"Processed translation files: {', '.join(processed)}")

        # We don't automatically run translation commands on install to avoid potential issues
        # User should run the command manually after installation
        frappe.msgprint(
            "Croatia App installed successfully. Run <code>bench update-croatian-translations</code> "
            "to distribute and compile Croatian translations."
        )

    except Exception as e:
        frappe.logger().error(f"Error in after_install: {str(e)}")
