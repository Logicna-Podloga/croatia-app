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
    account_name = account_name.lower()
    
    # Special cases
    special_cases = {
        'zalihe sirovina i materijala, rezervnih dijelova i sitnog inventara': ('Stock', 'Asset'),
        'mjesta i nositelji troškova - u proizvodno-uslužnim djelatnostima': ('Expense Account', 'Expense'),
        'mjesta i nositelji troškova - u djelatnosti trgovine': ('Expense Account', 'Expense'),
        'financijski rezultat poslovanja': ('Equity', 'Equity')
    }
    
    # Check for special cases first
    for case, (acc_type, _) in special_cases.items():
        if case in account_name:
            return acc_type
    
    # Asset accounts
    if any(keyword in account_name for keyword in ['potraživanja', 'imovina', 'nekretnina', 'postrojenja', 'oprema', 'zemljište', 'zgrade', 'građevine']):
        # Only parent/group accounts can be "Current Asset"
        if is_group == "1":
            return 'Current Asset'
        else:
            # For child accounts, use more specific types
            if 'amortizacija' in account_name:
                return 'Accumulated Depreciation'
            elif 'usklađenje' in account_name:
                return 'Accumulated Depreciation'
            elif 'pripremi' in account_name:
                return 'Capital Work in Progress'
            elif 'predujmovi' in account_name:
                return 'Bank'
            elif 'kriptovalute' in account_name:
                return 'Bank'
            elif 'softver' in account_name:
                return 'Fixed Asset'
            elif 'zemljište' in account_name:
                return 'Fixed Asset'
            elif 'zgrade' in account_name or 'građevine' in account_name:
                return 'Fixed Asset'
            elif 'postrojenja' in account_name:
                return 'Fixed Asset'
            elif 'oprema' in account_name:
                return 'Fixed Asset'
            elif 'alati' in account_name or 'inventar' in account_name:
                return 'Fixed Asset'
            elif 'vozila' in account_name or 'transportna' in account_name:
                return 'Fixed Asset'
            elif 'zalihe' in account_name:
                return 'Stock'
            elif 'potraživanja' in account_name:
                return 'Receivable'
            return 'Receivable'  # Default for asset child accounts
    
    # Liability accounts
    elif any(keyword in account_name for keyword in ['obveze', 'dug', 'kredit', 'hipoteka', 'založno']):
        # Only parent/group accounts can be "Current Liability"
        if is_group == "1":
            if 'dugoročne' in account_name:
                return 'Liability'
            elif 'kratkoročne' in account_name:
                return 'Current Liability'
            return 'Current Liability'
        else:
            # For child accounts, use more specific types
            if 'dobavljač' in account_name or 'dobavljača' in account_name:
                return 'Payable'
            elif 'porez' in account_name or 'pdv' in account_name:
                return 'Tax'
            return 'Payable'  # Default for liability child accounts
    
    # Equity accounts
    elif any(keyword in account_name for keyword in ['kapital', 'rezerve', 'dobit', 'gubitak', 'rezultat']):
        if 'temeljni' in account_name:
            return 'Equity'
        elif 'rezerve' in account_name:
            return 'Equity'
        elif 'dobit' in account_name or 'rezultat' in account_name:
            return 'Equity'
        return 'Equity'
    
    # Expense accounts
    elif any(keyword in account_name for keyword in ['troškovi', 'rashodi', 'amortizacija', 'izdatci', 'nositelji troškova']):
        if 'amortizacija' in account_name:
            return 'Depreciation'
        elif 'troškovi' in account_name or 'rashodi' in account_name or 'nositelji troškova' in account_name:
            return 'Expense Account'
        return 'Expense Account'
    
    # Income accounts
    elif any(keyword in account_name for keyword in ['prihodi', 'prihod']):
        return 'Income Account'
    
    # Tax accounts
    elif any(keyword in account_name for keyword in ['porez', 'pdv', 'ddv']):
        return 'Tax'
    
    # Default cases based on group status
    if is_group == "1":
        return ''  # Empty for unknown parent accounts
    else:
        return ''  # Empty for unknown child accounts

def determine_root_type(account_type, account_name):
    # Special cases
    special_cases = {
        'zalihe sirovina i materijala, rezervnih dijelova i sitnog inventara': 'Asset',
        'mjesta i nositelji troškova - u proizvodno-uslužnim djelatnostima': 'Expense',
        'mjesta i nositelji troškova - u djelatnosti trgovine': 'Expense',
        'financijski rezultat poslovanja': 'Equity'
    }
    
    account_name = account_name.lower()
    
    # Check for special cases first
    for case, root_type in special_cases.items():
        if case in account_name:
            return root_type
    
    # Standard mappings
    if account_type in ['Fixed Asset', 'Bank', 'Accumulated Depreciation', 'Stock', 'Current Asset', 'Capital Work in Progress', 'Receivable']:
        return 'Asset'
    elif account_type in ['Liability', 'Current Liability', 'Payable']:
        return 'Liability'
    elif account_type in ['Equity']:
        return 'Equity'
    elif account_type in ['Expense Account', 'Depreciation']:
        return 'Expense'
    elif account_type in ['Income Account']:
        return 'Income'
    elif account_type in ['Tax']:
        return 'Liability'
    return ''

def is_group_account(account_number):
    # If the account number ends with 0, it's likely a group account
    return account_number.endswith('0')

def get_parent_account_number(account_number):
    if len(account_number) <= 1:
        return ""
    return account_number[:-1]

def convert_accounts():
    input_file = 'RRiF-RP2024.csv'
    output_file = 'RRiF-RP2024_converted.csv'
    
    # First pass: collect all accounts to build parent-child relationships
    accounts = {}
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=';')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                account_number = row[0].strip()
                account_name = row[1].strip()
                accounts[account_number] = account_name
    
    # Second pass: write the converted file with parent account names
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
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
        
        # Read and process each line
        reader = csv.reader(infile, delimiter=';')
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 2:
                account_number = row[0].strip()
                account_name = row[1].strip()
                
                # Use account number as the name
                name = account_number
                
                # Determine if this is a group account
                is_group = "1" if is_group_account(account_number) else "0"
                
                # Get parent account number and name
                parent_account_number = get_parent_account_number(account_number)
                parent_account_name = parent_account_number if parent_account_number else ""
                
                # Determine account type and root type
                account_type = determine_account_type(account_name, is_group, account_number)
                root_type = determine_root_type(account_type, account_name)
                
                # Write the converted row
                writer.writerow([
                    name,  # Using account number as name
                    parent_account_name,  # Using parent account number as parent name
                    account_number,
                    parent_account_number,
                    is_group,
                    account_type,
                    root_type,
                    "EUR"  # Default currency
                ])

if __name__ == "__main__":
    convert_accounts() 