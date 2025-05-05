import os
import click
import frappe
from frappe.commands import pass_context

@click.command('update-croatian-translations')
@pass_context
def update_croatian_translations(context):
    """Distribute Croatian translation files to respective apps and update translations"""
    from croatia_app.utils.po_utils import distribute_po_files, run_translation_commands

    site = context.sites[0] if context.sites else None
    frappe.init(site=site)
    frappe.connect()

    try:
        print("Distributing PO files to apps...")
        processed_files = distribute_po_files()

        if processed_files:
            for file_info in processed_files:
                print(f"✓ {file_info}")
        else:
            print("No translation files found to process.")

        print("\nRunning translation update commands...")
        results = run_translation_commands(site)

        for result in results:
            if 'error' in result:
                print(f"✗ {result['command']} - Error: {result['error']}")
            elif result['return_code'] == 0:
                print(f"✓ {result['command']}")
            else:
                print(f"✗ {result['command']} - Return code: {result['return_code']}")
                if result['stderr']:
                    print(f"  Error: {result['stderr']}")

        print("\nTranslation update process completed.")
    except Exception as e:
        print(f"Error updating translations: {str(e)}")
    finally:
        frappe.destroy()

commands = [update_croatian_translations]
