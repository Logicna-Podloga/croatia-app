Frist error today was at 13:24 
#{
	#"exception": "pymysql.err.DataError: (1406, \"Data too long for column 'name' at row 1\")",
	#"exc_type": "DataError",
	#"_exc_source": "erpnext (app)"
#}

We TIRED FIx 1 in convert_accounts.py

import csv
import re

def truncate_account_name(name, max_length=140):
    """Truncate account name to max_length while preserving uniqueness"""
    if len(name) <= max_length:
        return name
    
    # Remove any extra spaces
    name = ' '.join(name.split())
    
    # If still too long, truncate
    if len(name) > max_length:
        # Try to truncate at a word boundary
        truncated = name[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + '...'
    return name

def determine_account_type(account_name, is_group, account_number):
    """Determine account type using minimal type assignment for maximum compatibility"""
    
    # Default to empty string, which is acceptable in ERPNext
    account_type = ""
    
    # Only parent accounts can be Current Asset or Current Liability
    if is_group == "1" and account_number.endswith('0'):
        # Asset group accounts
        if any(keyword in account_name.lower() for keyword in ['imovina', 'potraživanja']):
            return "Current Asset"
        # Liability group accounts
        elif any(keyword in account_name.lower() for keyword in ['obveze', 'dug']):
            return "Current Liability"
    else:
        # Non-group accounts get simpler type assignments
        if 'potraživanja' in account_name.lower():
            return "Receivable"
        elif 'dobavljač' in account_name.lower() or 'obveze' in account_name.lower():
            return "Payable"
        elif 'banka' in account_name.lower() or 'račun' in account_name.lower():
            return "Bank"
        elif 'novac' in account_name.lower() or 'gotovina' in account_name.lower():
            return "Cash"
        elif 'zalihe' in account_name.lower() or 'inventar' in account_name.lower():
            return "Stock"
        elif 'porez' in account_name.lower() or 'pdv' in account_name.lower():
            return "Tax"
        elif 'amortizacija' in account_name.lower():
            return "Depreciation"
        elif 'prihod' in account_name.lower():
            return "Income Account"
        elif 'trošak' in account_name.lower() or 'rashod' in account_name.lower():
            return "Expense Account"
        elif 'kapital' in account_name.lower() or 'rezultat' in account_name.lower():
            return "Equity"
    
    # Return empty string for all other cases
    return account_type

def determine_root_type(account_type):
    """Determine root type based on account type"""
    if account_type in ["Current Asset", "Fixed Asset", "Bank", "Cash", "Receivable", "Stock"]:
        return "Asset"
    elif account_type in ["Current Liability", "Payable", "Tax"]:
        return "Liability"
    elif account_type == "Equity":
        return "Equity"
    elif account_type in ["Expense Account", "Depreciation"]:
        return "Expense"
    elif account_type == "Income Account":
        return "Income"
    return ""

def is_group_account(account_number):
    """Determine if this is a group account based on account number ending with 0"""
    # Special case for account number 5
    if account_number == "5":
        return True
    return account_number.endswith('0')

def get_parent_account_number(account_number):
    """Get parent account number by removing the last digit"""
    if len(account_number) <= 1:
        return ""
    return account_number[:-1]

def get_root_type(account_number, account_name):
    """Get root type based on first digit of account number and special cases"""
    # Handle special cases explicitly
    if "MJESTA I NOSITELJI TROŠKOVA - U PROIZVODNO-USLUŽNIM DJELATNOSTIMA" in account_name:
        return "Expense"
    if "MJESTA I NOSITELJI TROŠKOVA - U DJELATNOSTI TRGOVINE" in account_name:
        return "Expense"
    
    if not account_number:
        return ""
    
    first_digit = account_number[0]
    
    # Based on Croatian chart of accounts standard classification
    if first_digit in ['0', '1']:
        return "Asset"
    elif first_digit in ['2']:
        return "Liability"
    elif first_digit in ['3']:
        return "Equity" 
    elif first_digit in ['4', '7', '5']:  # Added 5 for cost centers
        return "Expense"
    elif first_digit in ['6', '7']:
        return "Income"
    elif first_digit in ['8']:
        return "Expense"
    elif first_digit in ['9']:
        return "Income"
    
    return ""

def get_account_type(account_number, is_group, root_type, account_name):
    """Get account type based on account pattern and root type"""
    # Handle special cases explicitly
    if "MJESTA I NOSITELJI TROŠKOVA - U PROIZVODNO-USLUŽNIM DJELATNOSTIMA" in account_name:
        return "Expense Account"
    if "MJESTA I NOSITELJI TROŠKOVA - U DJELATNOSTI TRGOVINE" in account_name:
        return "Expense Account"
    
    if not account_number:
        return ""
    
    first_digit = account_number[0]
    
    # For non-group accounts (is_group == "0")
    if is_group == "0":
        if first_digit == '0':
            if account_number.startswith('03'):
                return "Fixed Asset"
            elif account_number.startswith('019') or account_number.startswith('029'):
                return "Depreciation"
            else:
                return "Fixed Asset"
        elif first_digit == '1':
            if account_number.startswith('10'):
                return "Bank"
            else:
                return "Receivable"
        elif first_digit == '2':
            return "Payable"
        elif first_digit == '3':
            return "Equity"
        elif first_digit in ['4', '7', '8', '5']:  # Added 5 for cost centers
            return "Expense Account"
        elif first_digit in ['6', '7', '9']:
            return "Income Account"
    # For group accounts (is_group == "1")
    else:
        if first_digit == '0' or first_digit == '1':
            # Only parent accounts ending with '0' can be Current Asset
            if account_number.endswith('0'):
                return "Current Asset"
            else:
                return "Fixed Asset"
        elif first_digit == '2':
            return "Current Liability"
        elif first_digit == '3':
            return "Equity"
        elif first_digit in ['4', '7', '8', '5']:  # Added 5 for cost centers
            return "Expense Account"
        elif first_digit in ['6', '7', '9']:
            return "Income Account"
    
    return ""

def convert_accounts():
    input_file = 'RRiF-RP2024.csv'
    output_file = 'RRiF-RP2024_converted.csv'
    
    # First pass: collect all accounts to build parent-child relationships
    accounts = {}
    account_order = []
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=';')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                account_number = row[0].strip()
                account_name = row[1].strip()
                accounts[account_number] = account_name
                account_order.append(account_number)
    
    # Fix parent-child relationships for special accounts
    cost_center_parents = {}
    for account_number in accounts:
        if account_number.startswith('5') and len(account_number) > 1:
            if "MJESTA I NOSITELJI TROŠKOVA - U PROIZVODNO-USLUŽNIM DJELATNOSTIMA" in accounts.get('5', ''):
                cost_center_parents[account_number] = "5"
    
    # Create top-level parent accounts based on ERPNext defaults
    top_level_accounts = {
        "Asset": "Application Of Funds(Assets)",
        "Liability": "Sources Of Funds(Liabilities)",
        "Equity": "Equity",
        "Expense": "Expenses",
        "Income": "Income"
    }
    
    # Second pass: write the converted file
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        # Write header
        writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "Account Name",
            "Parent Account",
            "Account Number",
            "Parent Account Number",
            "Is Group",
            "Account Type",
            "Root Type",
            "Account Currency"
        ])
        
        # First write the top-level accounts (ERPNext defaults)
        for root_type, account_name in top_level_accounts.items():
            writer.writerow([
                account_name,
                "",
                "",
                "",
                "1",  # All top level accounts are groups
                "",   # No account type for top-level groups
                root_type,
                "EUR"
            ])
        
        # Read and process each line from the original file
        for account_number in account_order:
            account_name = accounts[account_number]
            
            # Truncate account name if it's too long (MySQL column limit is typically 140 characters)
            account_name = truncate_account_name(account_name, 120)
            
            # Add account number as prefix for uniqueness and clarity
            account_name = f"{account_number} - {account_name}"
            
            # Determine if this is a group account (must end with 0)
            is_group = "1" if is_group_account(account_number) else "0"
            
            # Special cases for account 5
            if account_number == "5":
                is_group = "1"  # Force it to be a group account
            
            # Get parent account number
            parent_account_number = get_parent_account_number(account_number)
            
            # Override parent for special accounts if needed
            if account_number in cost_center_parents:
                parent_account_number = "5"
            
            # Get root type based on account number and name
            root_type = get_root_type(account_number, account_name)
            
            # Get parent account name
            if parent_account_number in accounts:
                parent_account_name = accounts[parent_account_number]
                # Truncate and prefix parent account name too
                parent_account_name = truncate_account_name(parent_account_name, 120)
                parent_account_name = f"{parent_account_number} - {parent_account_name}"
            else:
                # If no parent account found, assign to the appropriate top-level account
                parent_account_name = top_level_accounts.get(root_type, "")
            
            # Get account type - but only for non-group accounts
            if is_group == "0":
                if root_type == "Asset":
                    # For specific asset types, assign appropriate types
                    if account_number.startswith('03'):
                        account_type = "Fixed Asset"
                    elif account_number.startswith('10'):
                        account_type = "Bank"
                    elif account_number.startswith('102'):
                        account_type = "Cash"
                    elif account_number.startswith('12'):
                        account_type = "Receivable"
                    elif account_number.startswith('19') or account_number.startswith('29') or account_number.startswith('39'):
                        account_type = "Depreciation"
                    else:
                        account_type = "Fixed Asset"  # Default for other asset accounts
                elif root_type == "Liability":
                    account_type = "Payable"
                elif root_type == "Equity":
                    account_type = "Equity"
                elif root_type == "Expense":
                    account_type = "Expense Account"
                elif root_type == "Income":
                    account_type = "Income Account"
                else:
                    account_type = ""
            else:
                # For group accounts, we NEVER assign Current Asset or Current Liability
                account_type = ""
            
            # Write the converted row
            writer.writerow([
                account_name,        # Use original Croatian account name with number prefix
                parent_account_name, # Use original Croatian parent account name with number prefix
                account_number,
                parent_account_number,
                is_group,
                account_type,
                root_type,
                "EUR"  # Default currency
            ])

if __name__ == "__main__":
    convert_accounts() 
    

#Third error today was at 13:30
#BrokenPipeError: [Errno 32] Broken pipe
#Possible source of error: erpnext (app
### App Versions
```
{
	"erpnext": "15.60.1",
	"frappe": "15.68.0",
	"helpdesk": "1.7.0"
}
```
### Route
```
Form/Chart of Accounts Importer/Chart of Accounts Importer
```
### Traceback
```
Traceback (most recent call last):
  File "apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.py", line 460, in make_records
    doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
  File "apps/frappe/frappe/model/document.py", line 301, in insert
    self._validate_links()
  File "apps/frappe/frappe/model/document.py", line 975, in _validate_links
    frappe.throw(_("Could not find {0}").format(msg), frappe.LinkValidationError)
  File "apps/frappe/frappe/__init__.py", line 609, in throw
    msgprint(
  File "apps/frappe/frappe/__init__.py", line 574, in msgprint
    _raise_exception()
  File "apps/frappe/frappe/__init__.py", line 525, in _raise_exception
    raise exc
frappe.exceptions.LinkValidationError: Could not find Parent Department: All Departments

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "apps/frappe/frappe/app.py", line 115, in application
    response = frappe.api.handle(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/api/__init__.py", line 49, in handle
    data = endpoint(**arguments)
           ^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/api/v1.py", line 36, in handle_rpc_call
    return frappe.handler.handle()
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/handler.py", line 51, in handle
    data = execute_cmd(cmd)
           ^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/handler.py", line 84, in execute_cmd
    return frappe.call(method, **frappe.form_dict)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/__init__.py", line 1742, in call
    return fn(*args, **newargs)
           ^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/utils/typing_validations.py", line 31, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "apps/erpnext/erpnext/accounts/doctype/chart_of_accounts_importer/chart_of_accounts_importer.py", line 94, in import_coa
    set_default_accounts(company)
  File "apps/erpnext/erpnext/accounts/doctype/chart_of_accounts_importer/chart_of_accounts_importer.py", line 489, in set_default_accounts
    company.save()
  File "apps/frappe/frappe/model/document.py", line 378, in save
    return self._save(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/model/document.py", line 431, in _save
    self.run_post_save_methods()
  File "apps/frappe/frappe/model/document.py", line 1173, in run_post_save_methods
    self.run_method("on_update")
  File "apps/frappe/frappe/model/document.py", line 1007, in run_method
    out = Document.hook(fn)(self, *args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/model/document.py", line 1367, in composer
    return composed(self, method, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/model/document.py", line 1349, in runner
    add_to_return_value(self, fn(self, *args, **kwargs))
                              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/frappe/frappe/model/document.py", line 1004, in fn
    return method_object(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "apps/erpnext/erpnext/setup/doctype/company/company.py", line 261, in on_update
    self.create_default_departments()
  File "apps/erpnext/erpnext/setup/doctype/company/company.py", line 431, in create_default_departments
    make_records(records)
  File "apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.py", line 472, in make_records
    show_document_insert_error()
  File "apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.py", line 476, in show_document_insert_error
    print("Document Insert Error")
BrokenPipeError: [Errno 32] Broken pipe

```
### Request Data
```
{
	"type": "POST",
	"args": {
		"file_name": "/private/files/RRiF-RP2024_converted6b6742.csv",
		"company": "test"
	},
	"freeze": true,
	"freeze_message": "Creating Accounts...",
	"headers": {},
	"error_handlers": {},
	"url": "/api/method/erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer.import_coa",
	"request_id": null
}
```
### Response Data
```
{
	"exception": "BrokenPipeError: [Errno 32] Broken pipe",
	"exc_type": "BrokenPipeError",
	"_exc_source": "erpnext (app)",
	"_server_messages": "[\"{\\\"message\\\": \\\"Set default inventory account for perpetual inventory\\\", \\\"title\\\": \\\"Message\\\", \\\"indicator\\\": \\\"orange\\\", \\\"alert\\\": 1}\"]"
}
```


We tried this fix in convert_accounts.py 

import csv
import re

def truncate_account_name(name, max_length=140):
    """Truncate account name to max_length while preserving uniqueness"""
    if len(name) <= max_length:
        return name
    
    # Remove any extra spaces
    name = ' '.join(name.split())
    
    # If still too long, truncate
    if len(name) > max_length:
        # Try to truncate at a word boundary
        truncated = name[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + '...'
    return name

def determine_account_type(account_name, is_group, account_number):
    """Determine account type using minimal type assignment for maximum compatibility"""
    
    # Default to empty string, which is acceptable in ERPNext
    account_type = ""
    
    # Only parent accounts can be Current Asset or Current Liability
    if is_group == "1" and account_number.endswith('0'):
        # Asset group accounts
        if any(keyword in account_name.lower() for keyword in ['imovina', 'potraživanja']):
            return "Current Asset"
        # Liability group accounts
        elif any(keyword in account_name.lower() for keyword in ['obveze', 'dug']):
            return "Current Liability"
    else:
        # Non-group accounts get simpler type assignments
        if 'potraživanja' in account_name.lower():
            return "Receivable"
        elif 'dobavljač' in account_name.lower() or 'obveze' in account_name.lower():
            return "Payable"
        elif 'banka' in account_name.lower() or 'račun' in account_name.lower():
            return "Bank"
        elif 'novac' in account_name.lower() or 'gotovina' in account_name.lower():
            return "Cash"
        elif 'zalihe' in account_name.lower() or 'inventar' in account_name.lower():
            return "Stock"
        elif 'porez' in account_name.lower() or 'pdv' in account_name.lower():
            return "Tax"
        elif 'amortizacija' in account_name.lower():
            return "Depreciation"
        elif 'prihod' in account_name.lower():
            return "Income Account"
        elif 'trošak' in account_name.lower() or 'rashod' in account_name.lower():
            return "Expense Account"
        elif 'kapital' in account_name.lower() or 'rezultat' in account_name.lower():
            return "Equity"
    
    # Return empty string for all other cases
    return account_type

def determine_root_type(account_type):
    """Determine root type based on account type"""
    if account_type in ["Current Asset", "Fixed Asset", "Bank", "Cash", "Receivable", "Stock"]:
        return "Asset"
    elif account_type in ["Current Liability", "Payable", "Tax"]:
        return "Liability"
    elif account_type == "Equity":
        return "Equity"
    elif account_type in ["Expense Account", "Depreciation"]:
        return "Expense"
    elif account_type == "Income Account":
        return "Income"
    return ""

def is_group_account(account_number):
    """Determine if this is a group account based on account number ending with 0"""
    # Special case for account number 5
    if account_number == "5":
        return True
    return account_number.endswith('0')

def get_parent_account_number(account_number):
    """Get parent account number by removing the last digit"""
    if len(account_number) <= 1:
        return ""
    return account_number[:-1]

def get_root_type(account_number, account_name):
    """Get root type based on first digit of account number and special cases"""
    # Handle special cases explicitly
    if "MJESTA I NOSITELJI TROŠKOVA - U PROIZVODNO-USLUŽNIM DJELATNOSTIMA" in account_name:
        return "Expense"
    if "MJESTA I NOSITELJI TROŠKOVA - U DJELATNOSTI TRGOVINE" in account_name:
        return "Expense"
    
    if not account_number:
        return ""
    
    first_digit = account_number[0]
    
    # Based on Croatian chart of accounts standard classification
    if first_digit in ['0', '1']:
        return "Asset"
    elif first_digit in ['2']:
        return "Liability"
    elif first_digit in ['3']:
        return "Equity" 
    elif first_digit in ['4', '7', '5']:  # Added 5 for cost centers
        return "Expense"
    elif first_digit in ['6', '7']:
        return "Income"
    elif first_digit in ['8']:
        return "Expense"
    elif first_digit in ['9']:
        return "Income"
    
    return ""

def get_account_type(account_number, is_group, root_type, account_name):
    """Get account type based on account pattern and root type"""
    # Handle special cases explicitly
    if "MJESTA I NOSITELJI TROŠKOVA - U PROIZVODNO-USLUŽNIM DJELATNOSTIMA" in account_name:
        return "Expense Account"
    if "MJESTA I NOSITELJI TROŠKOVA - U DJELATNOSTI TRGOVINE" in account_name:
        return "Expense Account"
    
    if not account_number:
        return ""
    
    first_digit = account_number[0]
    
    # For non-group accounts (is_group == "0")
    if is_group == "0":
        if first_digit == '0':
            if account_number.startswith('03'):
                return "Fixed Asset"
            elif account_number.startswith('019') or account_number.startswith('029'):
                return "Depreciation"
            else:
                return "Fixed Asset"
        elif first_digit == '1':
            if account_number.startswith('10'):
                return "Bank"
            else:
                return "Receivable"
        elif first_digit == '2':
            return "Payable"
        elif first_digit == '3':
            return "Equity"
        elif first_digit in ['4', '7', '8', '5']:  # Added 5 for cost centers
            return "Expense Account"
        elif first_digit in ['6', '7', '9']:
            return "Income Account"
    # For group accounts (is_group == "1")
    else:
        if first_digit == '0' or first_digit == '1':
            # Only parent accounts ending with '0' can be Current Asset
            if account_number.endswith('0'):
                return "Current Asset"
            else:
                return "Fixed Asset"
        elif first_digit == '2':
            return "Current Liability"
        elif first_digit == '3':
            return "Equity"
        elif first_digit in ['4', '7', '8', '5']:  # Added 5 for cost centers
            return "Expense Account"
        elif first_digit in ['6', '7', '9']:
            return "Income Account"
    
    return ""

def convert_accounts():
    input_file = 'RRiF-RP2024.csv'
    output_file = 'RRiF-RP2024_converted.csv'
    
    # First pass: collect all accounts to build parent-child relationships
    accounts = {}
    account_order = []
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=';')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                account_number = row[0].strip()
                account_name = row[1].strip()
                accounts[account_number] = account_name
                account_order.append(account_number)
    
    # Fix parent-child relationships for special accounts
    cost_center_parents = {}
    for account_number in accounts:
        if account_number.startswith('5') and len(account_number) > 1:
            if "MJESTA I NOSITELJI TROŠKOVA - U PROIZVODNO-USLUŽNIM DJELATNOSTIMA" in accounts.get('5', ''):
                cost_center_parents[account_number] = "5"
    
    # Create top-level parent accounts based on ERPNext defaults
    top_level_accounts = {
        "Asset": "Application Of Funds(Assets)",
        "Liability": "Sources Of Funds(Liabilities)",
        "Equity": "Equity",
        "Expense": "Expenses",
        "Income": "Income"
    }
    
    # Second pass: write the converted file
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        # Write header
        writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "Account Name",
            "Parent Account",
            "Account Number",
            "Parent Account Number",
            "Is Group",
            "Account Type",
            "Root Type",
            "Account Currency"
        ])
        
        # First write the top-level accounts (ERPNext defaults)
        for root_type, account_name in top_level_accounts.items():
            writer.writerow([
                account_name,
                "",
                "",
                "",
                "1",  # All top level accounts are groups
                "",   # No account type for top-level groups
                root_type,
                "EUR"
            ])
        
        # Keep track of processed accounts to map proper hierarchy
        processed_accounts = set()
        
        # Read and process each line from the original file
        for account_number in account_order:
            # Get original account name
            account_name = accounts[account_number]
            
            # Shorten account names to avoid database errors
            short_name = truncate_account_name(account_name, 60)
            
            # Add account number prefix for clarity and uniqueness
            short_name = f"{account_number}-{short_name}"
            
            # Determine if this is a group account 
            is_group = "1" if is_group_account(account_number) else "0"
            
            # Special cases for account 5
            if account_number == "5":
                is_group = "1"  # Force it to be a group account
            
            # Get parent account number
            parent_account_number = get_parent_account_number(account_number)
            
            # Override parent for special accounts if needed
            if account_number in cost_center_parents:
                parent_account_number = "5"
            
            # Get root type based on account number and name
            root_type = get_root_type(account_number, account_name)
            
            # Use proper parent account name (shortened version)
            if parent_account_number in accounts:
                parent_original_name = accounts[parent_account_number]
                parent_short_name = truncate_account_name(parent_original_name, 60)
                parent_account_name = f"{parent_account_number}-{parent_short_name}"
            else:
                # If no parent in the original chart, link to ERPNext standard hierarchy
                parent_account_name = top_level_accounts.get(root_type, "")
            
            # Handle account types properly
            if is_group == "0":
                if root_type == "Asset":
                    # For specific asset types, assign appropriate types
                    if account_number.startswith('03'):
                        account_type = "Fixed Asset"
                    elif account_number.startswith('10'):
                        account_type = "Bank"
                    elif account_number.startswith('102'):
                        account_type = "Cash"
                    elif account_number.startswith('12'):
                        account_type = "Receivable"
                    elif account_number.startswith('19') or account_number.startswith('29') or account_number.startswith('39'):
                        account_type = "Depreciation"
                    else:
                        account_type = "Fixed Asset"  # Default for other asset accounts
                elif root_type == "Liability":
                    account_type = "Payable"
                elif root_type == "Equity":
                    account_type = "Equity"
                elif root_type == "Expense":
                    account_type = "Expense Account"
                elif root_type == "Income":
                    account_type = "Income Account"
                else:
                    account_type = ""
            else:
                # Group accounts have no account type
                account_type = ""
            
            # Write the converted row
            writer.writerow([
                short_name,
                parent_account_name,
                account_number,
                parent_account_number,
                is_group,
                account_type,
                root_type,
                "EUR"  # Default currency
            ])
            
            processed_accounts.add(account_number)

if __name__ == "__main__":
    convert_accounts() 
    


#It worked and with no errors







