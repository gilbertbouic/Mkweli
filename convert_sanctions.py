#!/usr/bin/env python3
"""
MkweliAML Sanctions List Converter
Converts various formats to compatible CSV for import
"""

import xml.etree.ElementTree as ET
import pandas as pd
import sys
import os
from pathlib import Path

def convert_xml_to_csv(xml_file, output_csv):
    """
    Convert XML sanctions list to CSV format
    Handles common XML structures from UN, UK, EU sources
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        data = []
        
        # Try different XML structures
        # Structure 1: UN-style with INDIVIDUAL elements
        for individual in root.findall('.//INDIVIDUAL'):
            entry = {}
            dataid = individual.find('DATAID')
            first_name = individual.find('FIRST_NAME')
            second_name = individual.find('SECOND_NAME')
            third_name = individual.find('THIRD_NAME')
            
            if first_name is not None and second_name is not None:
                full_name = f"{first_name.text if first_name.text else ''} {second_name.text if second_name.text else ''} {third_name.text if third_name is not None and third_name.text else ''}".strip()
                entry['id'] = dataid.text if dataid is not None else f"UN_{len(data)}"
                entry['name'] = full_name
                
                # Get additional info
                comments = individual.find('COMMENTS1')
                entry['additional_info'] = comments.text if comments is not None else 'UN Sanctions List'
                
                data.append(entry)
        
        # Structure 2: Simple item list
        if not data:
            for item in root.findall('.//item'):
                entry = {}
                id_elem = item.find('id')
                name_elem = item.find('name')
                
                if name_elem is not None:
                    entry['id'] = id_elem.text if id_elem is not None else f"ITEM_{len(data)}"
                    entry['name'] = name_elem.text
                    
                    # Try to find reason or description
                    reason_elem = item.find('reason') or item.find('description') or item.find('designation')
                    entry['additional_info'] = reason_elem.text if reason_elem is not None else 'Sanctions List Entry'
                    
                    data.append(entry)
        
        # Structure 3: Try any element with name and id
        if not data:
            for elem in root.findall('.//*'):
                name_elem = elem.find('name')
                id_elem = elem.find('id')
                if name_elem is not None and id_elem is not None:
                    entry = {}
                    entry['id'] = id_elem.text
                    entry['name'] = name_elem.text
                    entry['additional_info'] = 'Converted from XML'
                    data.append(entry)
        
        if data:
            df = pd.DataFrame(data)
            df.to_csv(output_csv, index=False)
            print(f"✅ Successfully converted {len(data)} entries to {output_csv}")
            return True
        else:
            print("❌ No recognizable data structure found in XML file")
            print("💡 Try using online XML to CSV converters:")
            print("   - https://www.convertcsv.com/xml-to-csv.htm")
            print("   - https://codebeautify.org/xml-to-csv")
            return False
            
    except Exception as e:
        print(f"❌ Error converting XML: {str(e)}")
        return False

def convert_excel_to_csv(excel_file, output_csv, sheet_name=0):
    """
    Convert Excel files to CSV format
    """
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Try to identify columns
        name_col = None
        id_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ['name', 'designation', 'title', 'individual']):
                name_col = col
            elif any(term in col_lower for term in ['id', 'reference', 'number', 'dataid']):
                id_col = col
        
        if name_col is None and len(df.columns) > 0:
            name_col = df.columns[0]  # Use first column as name
        
        if id_col is None:
            # Generate IDs
            df['generated_id'] = [f'ROW_{i}' for i in range(len(df))]
            id_col = 'generated_id'
        
        # Create clean dataframe with required columns
        clean_data = []
        for index, row in df.iterrows():
            entry = {
                'id': str(row[id_col]) if id_col in df.columns and pd.notna(row[id_col]) else f'ROW_{index}',
                'name': str(row[name_col]) if name_col in df.columns and pd.notna(row[name_col]) else f'Entry_{index}'
            }
            
            # Build additional info from other columns
            other_info = []
            for col in df.columns:
                if col != name_col and col != id_col and pd.notna(row[col]):
                    other_info.append(f"{col}: {row[col]}")
            
            entry['additional_info'] = ' | '.join(other_info[:3])  # Limit to first 3 fields
            clean_data.append(entry)
        
        clean_df = pd.DataFrame(clean_data)
        clean_df.to_csv(output_csv, index=False)
        print(f"✅ Successfully converted Excel file to {output_csv}")
        print(f"📊 Found {len(clean_df)} entries")
        return True
    except Exception as e:
        print(f"❌ Error converting Excel: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("MkweliAML Sanctions List Converter")
        print("=" * 40)
        print("Converts XML and Excel sanctions lists to CSV format for import")
        print()
        print("Usage: python convert_sanctions.py <input_file> <output_csv>")
        print()
        print("Supported formats:")
        print("  • XML files (.xml) - UN, UK sanctions lists")
        print("  • Excel files (.xls, .xlsx) - Various sources")
        print()
        print("Examples:")
        print("  python convert_sanctions.py un_sanctions.xml un_sanctions.csv")
        print("  python convert_sanctions.py uk_sanctions.xlsx uk_sanctions.csv")
        print()
        print("After conversion, import the CSV file through the MkweliAML web interface.")
        return
    
    input_file = sys.argv[1]
    output_csv = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"❌ Input file {input_file} not found")
        return
    
    file_ext = Path(input_file).suffix.lower()
    
    if file_ext == '.xml':
        print(f"🔄 Converting XML file: {input_file}")
        success = convert_xml_to_csv(input_file, output_csv)
    elif file_ext in ['.xls', '.xlsx']:
        print(f"🔄 Converting Excel file: {input_file}")
        success = convert_excel_to_csv(input_file, output_csv)
    else:
        print(f"❌ Unsupported file format: {file_ext}")
        print("💡 Supported formats: .xml, .xls, .xlsx")
        print("💡 For other formats, use online conversion tools:")
        print("   - PDF to Excel: https://smallpdf.com/pdf-to-excel")
        print("   - ODS to CSV: Use LibreOffice or Google Sheets")
        return
    
    if success:
        print(f"\n🎉 Conversion successful!")
        print(f"📁 Output file: {output_csv}")
        print(f"📋 You can now import {output_csv} into MkweliAML:")
        print("   1. Go to Sanctions Lists page")
        print("   2. Select the appropriate list name")
        print("   3. Choose the converted CSV file")
        print("   4. Click 'Import List'")
    else:
        print(f"\n❌ Conversion failed.")
        print("💡 Try manual conversion using online tools:")

if __name__ == "__main__":
    main()
