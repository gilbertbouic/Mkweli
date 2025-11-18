import re
import csv
import io
from typing import Tuple, List

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if text is None:
        return ""
    text = str(text).strip()
    # Remove potentially dangerous characters but allow international characters
    text = re.sub(r'[;\"\'<>]', '', text)
    return text

def validate_name(name: str) -> Tuple[bool, str]:
    """Validate client name"""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    if len(name) > 255:
        return False, "Name too long (max 255 characters)"
    if re.search(r'[0-9!@#$%^&*()_+={}\[\]:;<>?/~]', name):
        return False, "Name contains invalid characters"
    return True, ""

def validate_csv_file(file_stream) -> Tuple[bool, str, List]:
    """Validate and parse CSV file"""
    try:
        # Read and decode file
        stream = io.StringIO(file_stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        rows = list(csv_input)
        
        if len(rows) < 2:  # Header + at least one row
            return False, "CSV file must contain at least one data row", []
        
        # Validate header (optional)
        header = rows[0]
        if len(header) < 2:
            return False, "CSV must have at least 2 columns (ID and Name)", []
        
        # Process data rows
        processed_data = []
        for i, row in enumerate(rows[1:], start=1):
            if not any(field.strip() for field in row):
                continue  # Skip empty rows
                
            if len(row) < 2:
                return False, f"Row {i}: Must have at least 2 columns", []
            
            original_id = sanitize_input(row[0])
            full_name = sanitize_input(row[1])
            other_info = ' | '.join([sanitize_input(field) for field in row[2:6]]) if len(row) > 2 else ''
            
            if not full_name:
                return False, f"Row {i}: Name cannot be empty", []
            
            processed_data.append({
                'original_id': original_id or f'ROW_{i}',
                'full_name': full_name,
                'other_info': other_info
            })
        
        return True, f"Successfully processed {len(processed_data)} rows", processed_data
        
    except Exception as e:
        return False, f"Error processing CSV file: {str(e)}", []
