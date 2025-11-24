#!/usr/bin/env python3
import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSanctionsParser:
    """Simple parser for testing without package structure"""
    
    def parse_all_sanctions(self, data_dir: str = "data") -> List[Dict[str, Any]]:
        """Parse all XML sanctions files"""
        data_path = Path(data_dir)
        xml_files = list(data_path.glob('*.xml'))
        
        all_entities = []
        
        for xml_file in xml_files:
            print(f"📁 Parsing {xml_file.name}...")
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                filename = xml_file.name.lower()
                
                if 'uk' in filename:
                    entities = self._parse_uk_simple(root, str(xml_file.name))
                elif 'eu' in filename:
                    entities = self._parse_eu_simple(root, str(xml_file.name))
                elif 'un' in filename:
                    entities = self._parse_un_simple(root, str(xml_file.name))
                elif 'ofac' in filename:
                    entities = self._parse_ofac_simple(root, str(xml_file.name))
                else:
                    entities = self._parse_generic(root, str(xml_file.name))
                
                all_entities.extend(entities)
                print(f"   ✅ Extracted {len(entities)} entities")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
        return all_entities
    
    def _parse_uk_simple(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Simple UK parser"""
        entities = []
        for designation in root.findall('.//Designation'):
            names = []
            
            # Get names from Name elements
            for name_elem in designation.findall('.//Name'):
                if name_elem.text and name_elem.text.strip():
                    names.append(name_elem.text.strip())
            
            # Also check Name6
            for name6_elem in designation.findall('.//Name6'):
                if name6_elem.text and name6_elem.text.strip():
                    names.append(name6_elem.text.strip())
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'UK',
                    'names': names,
                    'primary_name': names[0],
                    'type': 'unknown'
                })
        
        return entities
    
    def _parse_eu_simple(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Simple EU parser"""
        entities = []
        ns = {'fsd': 'http://eu.europa.ec/fpi/fsd/export'}
        
        for entity_elem in root.findall('.//fsd:sanctionEntity', ns):
            names = []
            
            # Get name from nameAlias
            name_elem = entity_elem.find('.//fsd:nameAlias', ns)
            if name_elem is not None and name_elem.text:
                names.append(name_elem.text.strip())
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'EU',
                    'names': names,
                    'primary_name': names[0],
                    'type': 'entity'
                })
        
        return entities
    
    def _parse_un_simple(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Simple UN parser"""
        entities = []
        
        # Individuals
        for individual in root.findall('.//INDIVIDUAL'):
            names = []
            
            first_name = self._get_text(individual, './/FIRST_NAME')
            second_name = self._get_text(individual, './/SECOND_NAME')
            
            if first_name and second_name:
                names.append(f"{first_name} {second_name}".strip())
            elif first_name:
                names.append(first_name)
            
            # Aliases
            for alias in individual.findall('.//ALIAS_NAME'):
                if alias.text:
                    names.append(alias.text.strip())
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'UN',
                    'names': names,
                    'primary_name': names[0],
                    'type': 'individual'
                })
        
        # Entities
        for entity_elem in root.findall('.//ENTITY'):
            name = self._get_text(entity_elem, './/FIRST_NAME')  # UN uses FIRST_NAME for entities
            if name:
                entities.append({
                    'source': source,
                    'list_type': 'UN',
                    'names': [name],
                    'primary_name': name,
                    'type': 'entity'
                })
        
        return entities
    
    def _parse_ofac_simple(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Simple OFAC parser"""
        entities = []
        ns = {'ofac': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML'}
        
        for sdn_entry in root.findall('.//ofac:sdnEntry', ns):
            names = []
            
            last_name = self._get_text(sdn_entry, './/ofac:lastName', ns)
            if last_name:
                names.append(last_name)
            
            first_name = self._get_text(sdn_entry, './/ofac:firstName', ns)
            if first_name and last_name:
                names.append(f"{first_name} {last_name}")
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'OFAC',
                    'names': names,
                    'primary_name': names[0],
                    'type': 'individual' if first_name else 'entity'
                })
        
        return entities
    
    def _parse_generic(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Generic fallback parser"""
        entities = []
        
        # Look for any elements with "name" in tag and reasonable text
        for elem in root.iter():
            if (elem.text and len(elem.text.strip()) > 2 and 
                any(keyword in elem.tag.lower() for keyword in ['name', 'title'])):
                entities.append({
                    'source': source,
                    'list_type': 'Generic',
                    'names': [elem.text.strip()],
                    'primary_name': elem.text.strip(),
                    'type': 'unknown'
                })
        
        return entities
    
    def _get_text(self, parent: ET.Element, xpath: str, namespaces=None) -> Optional[str]:
        """Helper to get text from element"""
        elem = parent.find(xpath, namespaces)
        return elem.text.strip() if elem is not None and elem.text else None

class SimpleFuzzyMatcher:
    """Simple fuzzy matcher for testing"""
    
    def __init__(self, sanctions_data):
        self.sanctions_data = sanctions_data
        self.all_names = []
        
        for entity in sanctions_data:
            for name in entity.get('names', []):
                self.all_names.append((name, entity))
    
    def match_name(self, search_name, threshold=80):
        """Simple fuzzy matching"""
        from fuzzywuzzy import fuzz
        
        matches = []
        
        for name, entity in self.all_names:
            score = fuzz.token_sort_ratio(search_name.lower(), name.lower())
            if score >= threshold:
                matches.append({
                    'entity': entity,
                    'score': score,
                    'matched_name': name,
                    'search_name': search_name
                })
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches

def main():
    print("🚀 Testing XML Sanctions Parsing...")
    
    # Parse sanctions
    parser = SimpleSanctionsParser()
    sanctions_entities = parser.parse_all_sanctions('data')
    
    print(f"\n📊 Total entities parsed: {len(sanctions_entities)}")
    
    if not sanctions_entities:
        print("❌ No entities parsed!")
        return
    
    # Show sample
    print(f"\n📋 Sample entities:")
    for i, entity in enumerate(sanctions_entities[:5]):
        print(f"  {i+1}. {entity['primary_name']} ({entity['source']})")
        print(f"     All names: {entity['names'][:3]}")  # Show first 3 names
    
    # Test fuzzy matching
    print(f"\n🧪 Testing Fuzzy Matching:")
    matcher = SimpleFuzzyMatcher(sanctions_entities)
    
    test_names = [
        "Example Corporation",
        "John Smith", 
        "HAJI KHAIRULLAH",  # From UK list
        "AEROCARIBBEAN"     # From OFAC list
    ]
    
    for test_name in test_names:
        matches = matcher.match_name(test_name, threshold=70)
        print(f"\n🔍 '{test_name}': {len(matches)} matches")
        for match in matches[:2]:  # Show top 2
            print(f"   - {match['matched_name']} (Score: {match['score']})")
            print(f"     Source: {match['entity']['source']}")

if __name__ == '__main__':
    main()
