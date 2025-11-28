#!/usr/bin/env python3
"""Deep debug XML parsing to find name fields"""

import xml.etree.ElementTree as ET
from pathlib import Path

def deep_debug_xml():
    """Find actual name fields in XML structures"""
    data_dir = Path("data")
    
    for xml_file in data_dir.glob('*.xml'):
        print(f"\n🔍 Deep debugging {xml_file.name}:")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            if 'eu' in xml_file.name.lower():
                # EU specific debugging
                print("   EU Structure Analysis:")
                ns = {'eu': 'http://eu.europa.ec/fpi/fsd/export'}
                
                count = 0
                for entity in root.findall('.//eu:sanctionEntity', ns):
                    if count < 3:  # Only show first 3
                        print(f"   Entity {count}:")
                        
                        # Look for nameAlias
                        for name_alias in entity.findall('.//eu:nameAlias', ns):
                            print(f"     Found nameAlias")
                            for name_elem in name_alias.findall('.//eu:wholeName', ns):
                                if name_elem.text:
                                    print(f"       wholeName: '{name_elem.text.strip()}'")
                            
                            for name_elem in name_alias.findall('.//eu:aliasName', ns):
                                if name_elem.text:
                                    print(f"       aliasName: '{name_elem.text.strip()}'")
                        
                        # Look for subjectType
                        for subj_type in entity.findall('.//eu:subjectType', ns):
                            print(f"     subjectType code: {subj_type.get('code')}")
                    
                    count += 1
                
                print(f"   Total EU entities found: {count}")
            
            elif 'un' in xml_file.name.lower():
                # UN specific debugging (same structure as UK)
                print("   UN Structure Analysis:")
                count = 0
                for designation in root.findall('.//Designation'):
                    if count < 3:  # Only show first 3
                        print(f"   Designation {count}:")
                        
                        # Look for all text elements in designation
                        for elem in designation.iter():
                            if elem.text and elem.text.strip() and len(elem.text.strip()) > 3:
                                if not elem.tag == 'Designation':  # Skip the root designation tag
                                    print(f"     {elem.tag}: '{elem.text.strip()[:60]}...'")
                    
                    count += 1
                print(f"   Total UN designations: {count}")
            
            elif 'ofac' in xml_file.name.lower():
                # OFAC specific debugging
                print("   OFAC Structure Analysis:")
                ns = {'ofac': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML'}
                
                # Find entities element
                entities_elem = root.find('.//ofac:entities', ns)
                if entities_elem is not None:
                    print(f"   Found entities element with {len(entities_elem)} children")
                    
                    count = 0
                    for entity in entities_elem.findall('.//ofac:entity', ns):
                        if count < 2:  # Only show first 2
                            print(f"   Entity {count}:")
                            
                            # Look for names
                            for name_elem in entity.findall('.//ofac:name', ns):
                                print(f"     Found name element")
                                
                                for aka in name_elem.findall('.//ofac:aka', ns):
                                    print(f"       Found aka")
                                    
                                    for primary in aka.findall('.//ofac:primaryDisplayName', ns):
                                        if primary.text:
                                            print(f"         primaryDisplayName: '{primary.text.strip()}'")
                                    
                                    for alias in aka.findall('.//ofac:alias', ns):
                                        if alias.text:
                                            print(f"         alias: '{alias.text.strip()}'")
                            
                            # Look for type
                            for type_elem in entity.findall('.//ofac:type', ns):
                                if type_elem.text:
                                    print(f"     Type: {type_elem.text.strip()}")
                        
                        count += 1
                    
                    print(f"   Total OFAC entities: {count}")
                else:
                    print("   ❌ No entities element found")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    deep_debug_xml()
