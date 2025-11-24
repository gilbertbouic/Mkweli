#!/usr/bin/env python3
"""
Systematic XML Quality Check for Sanctions Lists
"""
import os
import xml.etree.ElementTree as ET
from lxml import etree
import logging
from pathlib import Path
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_xml_quality(filepath):
    """Comprehensive XML quality check"""
    print(f"\n🔍 Analyzing: {filepath.name}")
    print(f"   Size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Check 1: Basic file structure
    try:
        with open(filepath, 'rb') as f:
            first_lines = [f.readline().decode('utf-8', errors='ignore') for _ in range(5)]
        print("   First 5 lines:")
        for i, line in enumerate(first_lines):
            print(f"     {i+1}: {line.strip()}")
    except Exception as e:
        print(f"   ❌ File read error: {e}")
        return False
    
    # Check 2: Standard XML parsing
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        print(f"   ✅ Standard XML parse: SUCCESS")
        print(f"   Root tag: {root.tag}")
        children = list(root)
        print(f"   Direct children: {len(children)}")
        return True
    except ET.ParseError as e:
        print(f"   ❌ Standard XML parse: FAILED - {e}")
    
    # Check 3: lxml recovery parsing
    try:
        parser = etree.XMLParser(recover=True, huge_tree=True)
        tree = etree.parse(filepath, parser)
        root = tree.getroot()
        print(f"   ✅ lxml recovery parse: SUCCESS")
        print(f"   Root tag: {root.tag}")
        print(f"   ⚠️  File needs XML recovery")
        return False
    except Exception as e:
        print(f"   ❌ lxml recovery parse: FAILED - {e}")
        return False

def parse_xml_recover(src_path, out_path=None, make_backup=True):
    """
    Recover a badly-formed XML file using lxml's recovery parser.
    """
    src_path = Path(src_path)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    if out_path is None:
        out_path = src_path.parent / f"{src_path.stem}.cleaned.xml"

    if make_backup:
        bak_path = src_path.parent / f"{src_path.name}.bak"
        if not bak_path.exists():
            shutil.copy2(src_path, bak_path)
            print(f"   📦 Backup created: {bak_path}")

    parser = etree.XMLParser(recover=True, huge_tree=True, remove_blank_text=True)
    try:
        tree = etree.parse(src_path, parser)
    except Exception as e:
        print(f"   ❌ Recovery parse failed: {e}")
        raise

    # Get the recovered root
    root = tree.getroot()
    
    # Count elements to verify recovery worked
    element_count = len(list(root.iter()))
    print(f"   📊 Recovered elements: {element_count}")

    # Write cleaned XML
    cleaned_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")
    
    with open(out_path, "wb") as f:
        f.write(cleaned_bytes)

    print(f"   ✅ Cleaned XML written: {out_path}")
    return out_path

def test_parsing_after_recovery(original_path, cleaned_path):
    """Test if cleaned file parses correctly"""
    print(f"\n🧪 Testing cleaned file: {cleaned_path.name}")
    
    # Test with standard parser
    try:
        tree = ET.parse(cleaned_path)
        root = tree.getroot()
        children = list(root)
        print(f"   ✅ Standard parse SUCCESS - {len(children)} root children")
        return True
    except ET.ParseError as e:
        print(f"   ❌ Standard parse FAILED: {e}")
        return False

def main():
    print("🚀 Systematic XML Quality Analysis")
    print("=" * 50)
    
    data_dir = Path("data")
    xml_files = list(data_dir.glob("*.xml"))
    
    if not xml_files:
        print("❌ No XML files found in data/ directory")
        return
    
    print(f"📁 Found {len(xml_files)} XML files:")
    
    needs_recovery = []
    
    for xml_file in xml_files:
        is_healthy = check_xml_quality(xml_file)
        if not is_healthy:
            needs_recovery.append(xml_file)
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {len(xml_files)}")
    print(f"   Healthy files: {len(xml_files) - len(needs_recovery)}")
    print(f"   Files needing recovery: {len(needs_recovery)}")
    
    if needs_recovery:
        print(f"\n🛠️  Starting XML Recovery Process...")
        recovered_files = []
        
        for file_path in needs_recovery:
            try:
                print(f"\n🔧 Recovering {file_path.name}...")
                cleaned_path = parse_xml_recover(file_path)
                if test_parsing_after_recovery(file_path, cleaned_path):
                    recovered_files.append((file_path, cleaned_path))
                    print(f"   ✅ Recovery SUCCESSFUL")
                else:
                    print(f"   ❌ Recovery FAILED")
            except Exception as e:
                print(f"   ❌ Recovery ERROR: {e}")
        
        print(f"\n🎯 Recovery Complete:")
        print(f"   Successfully recovered: {len(recovered_files)}/{len(needs_recovery)} files")
        
        # Option to replace original files
        if recovered_files:
            response = input("\nReplace original files with cleaned versions? (y/N): ")
            if response.lower() == 'y':
                for original, cleaned in recovered_files:
                    shutil.move(cleaned, original)
                    print(f"   🔄 Replaced {original.name}")
    
    print(f"\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
