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