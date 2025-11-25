# Replace the entire app/robust_sanctions_parser.py file:
import xml.etree.ElementTree as ET
import pandas as pd
import os
import re
from typing import List, Dict, Any
import logging

class RobustSanctionsParser:
    """Robust parser that specifically handles each sanctions format"""
    
    def __init__(self):
        self.parsed_entities = []
        self.logger = logging.getLogger(__name__)
    
    def parse_all_sanctions(self) -> List[Dict]:
        """Parse all sanctions files with format-specific parsers"""
        data_dir = "data"
        self.parsed_entities = []
        
        if not os.path.exists(data_dir):
            self.logger.error(f"Data directory '{data_dir}' not found")
            return self.parsed_entities
        
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            
            try:
                if filename.endswith('.xml'):
                    entities_count = self._parse_xml_with_format_detection(file_path)
                    self.logger.info(f"📊 {filename}: {entities_count} entities")
                else:
                    self.logger.info(f"Skipping non-XML file: {filename}")
            except Exception as e:
                self.logger.error(f"Error parsing {filename}: {str(e)}")
        
        self.logger.info(f"✅ Successfully parsed {len(self.parsed_entities)} total entities")
        return self.parsed_entities
    
    def _parse_xml_with_format_detection(self, file_path: str) -> int:
        """Parse XML file with specific format detection"""
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            filename = os.path.basename(file_path)
            
            initial_count = len(self.parsed_entities)
            
            # Try multiple parsing strategies
            strategies = [
                self._parse_ofac_specific,
                self._parse_uk_specific, 
                self._parse_eu_specific,
                self._parse_un_specific,
                self._parse_generic_deep
            ]
            
            for strategy in strategies:
                try:
                    strategy(root, filename)
                    # If we found entities, break
                    if len(self.parsed_entities) > initial_count:
                        break
                except Exception as e:
                    continue
            
            return len(self.parsed_entities) - initial_count
            
        except Exception as e:
            self.logger.error(f"XML parsing error for {file_path}: {str(e)}")
            return 0
    
    def _parse_ofac_specific(self, root: ET.Element, source: str):
        """Parse OFAC-specific format (SDN list)"""
        # OFAC format: sdnList -> sdnEntry -> lastName, firstName, title
        namespace = self._detect_namespace(root)
        
        for entry in root.findall(f'.//{namespace}sdnEntry') + root.findall('.//sdnEntry'):
            try:
                # Get individual names
                first_name = self._get_element_text(entry, f'{namespace}firstName')
                last_name = self._get_element_text(entry, f'{namespace}lastName')
                
                # Get entity names
                title = self._get_element_text(entry, f'{namespace}title')
                
                primary_name = ""
                entity_type = "individual"
                
                if first_name and last_name:
                    primary_name = f"{first_name} {last_name}".strip()
                elif title:
                    primary_name = title
                    entity_type = "entity"
                elif last_name:
                    primary_name = last_name
                
                if primary_name and len(primary_name) > 2:
                    entity = {
                        'source': source,
                        'list_type': 'OFAC',
                        'primary_name': primary_name,
                        'type': entity_type,
                        'id': entry.get('ID', ''),
                        'programs': [p.text for p in entry.findall(f'{namespace}program') if p.text],
                        'addresses': [a.text for a in entry.findall(f'{namespace}address') if a.text]
                    }
                    self.parsed_entities.append(entity)
                    
            except Exception as e:
                continue
    
    def _parse_uk_specific(self, root: ET.Element, source: str):
        """Parse UK-specific format"""
        # UK format: Designations -> Designation -> Name, Title
        for designation in root.findall('.//Designation') + root.findall('.//designation'):
            try:
                names = []
                
                # Try multiple name elements
                for name_elem in designation.findall('.//Name'):
                    if name_elem.text and name_elem.text.strip():
                        names.append(name_elem.text.strip())
                
                for title_elem in designation.findall('.//Title'):
                    if title_elem.text and title_elem.text.strip():
                        names.append(title_elem.text.strip())
                
                for name_elem in designation.findall('.//name'):
                    if name_elem.text and name_elem.text.strip():
                        names.append(name_elem.text.strip())
                
                # Use the longest name as primary (usually most complete)
                if names:
                    primary_name = max(names, key=len)
                    
                    entity = {
                        'source': source,
                        'list_type': 'UK',
                        'primary_name': primary_name,
                        'names': names,
                        'type': 'entity',
                        'id': designation.get('ID', ''),
                        'regime': self._get_element_text(designation, './/RegimeName')
                    }
                    self.parsed_entities.append(entity)
                    
            except Exception as e:
                continue
    
    def _parse_eu_specific(self, root: ET.Element, source: str):
        """Parse EU-specific format - more targeted approach"""
        # EU format: look for specific entity name elements
        name_elements = [
            './/firstName',
            './/lastName', 
            './/name',
            './/title',
            './/entityName',
            './/organizationName',
            './/companyName'
        ]
        
        for elem in root.iter():
            # Skip elements that are clearly not entity names
            if elem.tag in ['remark', 'description', 'address', 'comment', 'note']:
                continue
                
            # Look for text that looks like entity names
            if elem.text and elem.text.strip():
                text = elem.text.strip()
                
                # Skip if it's clearly descriptive text
                if self._is_descriptive_text(text):
                    continue
                    
                # Check if parent or grandparent suggests this is a name
                if self._is_likely_entity_name(elem, text):
                    entity = {
                        'source': source,
                        'list_type': 'EU',
                        'primary_name': text,
                        'type': 'entity',
                        'id': elem.get('id', '')
                    }
                    self.parsed_entities.append(entity)

    def _is_descriptive_text(self, text: str) -> bool:
        """Check if text is descriptive rather than an entity name"""
        if len(text) > 100:
            return True
        
        descriptive_indicators = [
            'principal place of business',
            'place of registration',
            'date of birth',
            'passport number',
            'address:',
            'tel:',
            'fax:',
            'email:',
            'associated individual',
            'photo available',
            'husband',
            'wife',
            'daughter',
            'son'
        ]
        
        if any(indicator in text.lower() for indicator in descriptive_indicators):
            return True
        
        # Multiple sentences suggest descriptive text
        if text.count('.') > 2:
            return True
        
        return False

    def _is_likely_entity_name(self, element: ET.Element, text: str) -> bool:
        """Check if element context suggests this is an entity name"""
        # Check element tag
        name_tags = ['name', 'firstName', 'lastName', 'title', 'entity', 'organization', 'company']
        if any(tag in element.tag.lower() for tag in name_tags):
            return True
        
        # Check parent tags
        parent = element.getparent()
        if parent is not None:
            parent_tags = ['entity', 'organization', 'company', 'individual', 'party', 'subject']
            if any(tag in parent.tag.lower() for tag in parent_tags):
                return True
        
        # Text characteristics of entity names
        if (2 <= len(text) <= 50 and  # Reasonable length
            not text.isdigit() and    # Not just numbers
            ' ' in text and           # Contains spaces (multi-word)
            not text.startswith('http')):  # Not a URL
            return True
        
        return False
    
    def _parse_un_specific(self, root: ET.Element, source: str):
        """Parse UN-specific format"""
        # UN format: INDIVIDUALS -> INDIVIDUAL -> FIRST_NAME, SECOND_NAME
        for individual in root.findall('.//INDIVIDUAL'):
            try:
                first_name = self._get_element_text(individual, './/FIRST_NAME')
                second_name = self._get_element_text(individual, './/SECOND_NAME')
                
                if first_name or second_name:
                    name_parts = [first_name, second_name]
                    primary_name = " ".join([p for p in name_parts if p]).strip()
                    
                    if primary_name:
                        entity = {
                            'source': source,
                            'list_type': 'UN',
                            'primary_name': primary_name,
                            'type': 'individual',
                            'id': individual.get('ID', ''),
                            'designation': self._get_element_text(individual, './/DESIGNATION')
                        }
                        self.parsed_entities.append(entity)
                        
            except Exception as e:
                continue
    
    def _parse_generic_deep(self, root: ET.Element, source: str):
        """Deep search for any text that looks like entity names"""
        # Look for any text content that could be an entity name
        visited_texts = set()
        
        for elem in root.iter():
            if elem.text and elem.text.strip():
                text = elem.text.strip()
                
                # Basic heuristics for entity names
                if (len(text) > 3 and 
                    text not in visited_texts and
                    not text.startswith('<') and
                    ' ' in text and  # Likely a multi-word name
                    not text.isnumeric() and
                    not re.match(r'^\d+$', text)):
                    
                    visited_texts.add(text)
                    
                    entity = {
                        'source': source,
                        'list_type': 'Generic',
                        'primary_name': text,
                        'type': 'entity'
                    }
                    self.parsed_entities.append(entity)
    
    def _detect_namespace(self, root: ET.Element) -> str:
        """Detect XML namespace"""
        if '}' in root.tag:
            return root.tag.split('}')[0] + '}'
        return ''
    
    def _get_element_text(self, parent: ET.Element, xpath: str) -> str:
        """Safely get text from element"""
        try:
            elem = parent.find(xpath)
            if elem is not None and elem.text:
                return elem.text.strip()
        except:
            pass
        return ""
    
    def get_all_entities(self) -> List[Dict]:
        """Get all parsed entities"""
        return self.parsed_entities
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame"""
        if not self.parsed_entities:
            return pd.DataFrame()
        return pd.DataFrame(self.parsed_entities)
