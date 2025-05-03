# croatia_app/commands/__init__.py
import os
import click
import frappe
from frappe.commands import pass_context
from frappe.exceptions import ValidationError

@click.command('generate-croatian-translations')
@pass_context
def generate_croatian_translations(context):
    """Generate and update Croatian translations for ERPNext"""
    from croatia_app.utils.translation_utils import update_translations

    site = context.sites[0]
    frappe.init(site=site)
    frappe.connect()

    try:
        result = update_translations()
        click.echo(result)
    except Exception as e:
        click.echo(f"Error updating translations: {str(e)}")
    finally:
        frappe.destroy()

@click.command('create-initial-po')
@pass_context
def create_initial_po(context):
    """Create initial PO file with common accounting terms"""
    from croatia_app.utils.translation_utils import create_initial_po_file

    site = context.sites[0]
    frappe.init(site=site)
    frappe.connect()

    try:
        result = create_initial_po_file()
        click.echo(f"Initial PO file created at: {result}")
    except Exception as e:
        click.echo(f"Error creating initial PO file: {str(e)}")
    finally:
        frappe.destroy()

commands = [generate_croatian_translations, create_initial_po]
