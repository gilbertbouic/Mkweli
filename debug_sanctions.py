#!/usr/bin/env python3
import pandas as pd
import os
import sys
from pathlib import Path

def debug_sanctions_loading():
    data_dir = Path('data')
    
    if not data_dir.exists():
        print("❌ Data directory does not exist!")
        return
    
    files = list(data_dir.iterdir())
    print(f"📁 Found {len(files)} files in data directory:")
    
    for file_path in files:
        print(f"\n🔍 Analyzing: {file_path.name}")
        
        # Check file permissions
        try:
            with open(file_path, 'rb') as f:
                header = f.read(100)
                print(f"   File accessible: ✅")
        except Exception as e:
            print(f"   File accessible: ❌ ({e})")
            continue
        
        # Try to read based on file type
        try:
            if file_path.suffix.lower() == '.csv':
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                        print(f"   CSV read with {encoding}: ✅ {len(df)} rows, {len(df.columns)} cols")
                        print(f"   Columns: {df.columns.tolist()}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print("   ❌ Could not read CSV with any encoding")
                    
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=5)
                print(f"   Excel read: ✅ {len(df)} rows, {len(df.columns)} cols")
                print(f"   Columns: {df.columns.tolist()}")
                
            elif file_path.suffix.lower() == '.ods':
                df = pd.read_excel(file_path, engine='odf', nrows=5)
                print(f"   ODS read: ✅ {len(df)} rows, {len(df.columns)} cols")
                print(f"   Columns: {df.columns.tolist()}")
                
            else:
                print(f"   ⚠️  Unsupported file type: {file_path.suffix}")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

if __name__ == '__main__':
    debug_sanctions.py()
