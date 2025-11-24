#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

def debug_xml_sanctions():
    data_dir = Path('data')
    
    if not data_dir.exists():
        print("❌ Data directory does not exist!")
        return
    
    xml_files = list(data_dir.glob('*.xml'))
    print(f"📁 Found {len(xml_files)} XML files:")
    
    for xml_file in xml_files:
        print(f"\n🔍 Analyzing: {xml_file.name}")
        print(f"   Size: {xml_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        try:
            # Parse XML to understand structure
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            print(f"   Root tag: {root.tag}")
            
            # Count direct children
            children = list(root)
            print(f"   Direct children: {len(children)}")
            
            # Show first few child tags
            unique_tags = set()
            for child in children[:10]:
                unique_tags.add(child.tag)
                print(f"     - {child.tag}: {len(list(child))} sub-elements")
            
            print(f"   Unique tags in first 10: {unique_tags}")
            
            # Try to find common sanction elements
            all_elements = list(root.iter())
            print(f"   Total elements: {len(all_elements)}")
            
            # Look for name-like elements
            name_like_tags = set()
            for elem in all_elements[:100]:  # Check first 100 elements
                tag_lower = elem.tag.lower()
                if any(keyword in tag_lower for keyword in ['name', 'title', 'designation', 'entity']):
                    name_like_tags.add(elem.tag)
                    if elem.text and len(elem.text.strip()) > 0:
                        print(f"     Found name-like: {elem.tag} = '{elem.text[:50]}...'")
            
            print(f"   Name-like tags found: {name_like_tags}")
            
        except ET.ParseError as e:
            print(f"   ❌ XML Parse Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    debug_xml_sanctions()
