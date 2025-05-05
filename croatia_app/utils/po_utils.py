import os
import shutil
import frappe
import subprocess
from frappe.utils import cstr

def get_bench_path():
    """Get the bench path from Frappe"""
    return os.path.abspath(os.path.join(frappe.utils.get_bench_path()))

def get_all_apps():
    """Get all installed apps"""
    return frappe.get_all_apps(True)

def find_locale_path(app_name):
    """Find the locale directory for an app"""
    bench_path = get_bench_path()
    app_path = os.path.join(bench_path, 'apps', app_name)

    # Check common locale paths
    possible_paths = [
        os.path.join(app_path, app_name, 'locale'),
        os.path.join(app_path, 'locale'),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Create if it doesn't exist
    default_path = possible_paths[0]
    os.makedirs(default_path, exist_ok=True)
    return default_path

def distribute_po_files():
    """Distribute PO files to respective app locale directories"""
    bench_path = get_bench_path()
    apps = get_all_apps()

    # Get path to our translations folder
    croatia_app_path = frappe.get_app_path("croatia_app")
    translations_dir = os.path.join(croatia_app_path, "translations")

    if not os.path.exists(translations_dir):
        frappe.msgprint("Translations directory not found")
        return

    processed_files = []

    # Process each file in translations directory
    for filename in os.listdir(translations_dir):
        if filename.startswith("hr-") and filename.endswith(".po") or filename.endswith(".clean.po"):
            # Parse the app name from the filename (hr-{app}.clean.po)
            parts = filename.split('-', 1)
            if len(parts) < 2:
                continue

            app_part = parts[1].replace('.clean.po', '').replace('.po', '')
            app_name = app_part.split('.')[0]  # In case there are more dots

            if app_name not in apps:
                frappe.logger().warning(f"App {app_name} not found, but translation file exists")
                continue

            source_file = os.path.join(translations_dir, filename)
            locale_dir = find_locale_path(app_name)
            hr_dir = os.path.join(locale_dir, 'hr')
            lc_messages_dir = os.path.join(hr_dir, 'LC_MESSAGES')

            # Create directories if they don't exist
            os.makedirs(lc_messages_dir, exist_ok=True)

            # Copy file to destination with new name
            target_file = os.path.join(lc_messages_dir, 'messages.po')
            shutil.copy2(source_file, target_file)

            processed_files.append(f"{app_name}: {filename} → {target_file}")

    return processed_files

def run_translation_commands(site_name=None):
    """Run bench commands for updating translations"""
    bench_path = get_bench_path()

    if not site_name:
        # Get the current site if not specified
        try:
            site_name = frappe.local.site
        except Exception:
            sites = os.listdir(os.path.join(bench_path, 'sites'))
            sites = [site for site in sites if os.path.isdir(os.path.join(bench_path, 'sites', site))
                    and not site.startswith('.')]
            if sites:
                site_name = sites[0]
            else:
                frappe.throw("No site found in bench")

    commands = [
        ["bench", "update-translations", "--locale", "hr"],
        ["bench", "compile-translations", "--locale", "hr"],
        ["bench", "--site", site_name, "clear-cache"],
        ["bench", "--site", site_name, "clear-website-cache"]
    ]

    results = []
    for cmd in commands:
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=bench_path
            )
            stdout, stderr = process.communicate()

            result = {
                'command': ' '.join(cmd),
                'return_code': process.returncode,
                'stdout': cstr(stdout),
                'stderr': cstr(stderr)
            }

            results.append(result)

            if process.returncode != 0:
                frappe.logger().error(f"Command failed: {' '.join(cmd)}")
                frappe.logger().error(f"Error: {stderr}")
        except Exception as e:
            frappe.logger().error(f"Failed to run command {' '.join(cmd)}: {str(e)}")
            results.append({
                'command': ' '.join(cmd),
                'error': str(e)
            })

    return results
