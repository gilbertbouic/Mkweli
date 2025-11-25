# app/universal_sanctions_parser.py
import xml.etree.ElementTree as ET
import pandas as pd
import os
from typing import List, Dict, Any
import logging

class UniversalSanctionsParser:
    """Universal parser that handles multiple sanctions file formats"""
    
    def __init__(self):
        self.parsed_entities = []
        self.logger = logging.getLogger(__name__)
    
    def parse_all_sanctions(self) -> List[Dict]:
        """Parse all sanctions files in the data directory"""
        data_dir = "data"
        self.parsed_entities = []
        
        if not os.path.exists(data_dir):
            self.logger.error(f"Data directory '{data_dir}' not found")
            return self.parsed_entities
        
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            
            try:
                if filename.endswith('.xml'):
                    self._parse_xml_file(file_path)
                elif filename.endswith('.csv'):
                    self._parse_csv_file(file_path)
                elif filename.endswith('.txt'):
                    self._parse_txt_file(file_path)
                else:
                    self.logger.info(f"Skipping unsupported file: {filename}")
            except Exception as e:
                self.logger.error(f"Error parsing {filename}: {str(e)}")
        
        self.logger.info(f"✅ Successfully parsed {len(self.parsed_entities)} total entities")
        return self.parsed_entities
    
    def _parse_xml_file(self, file_path: str):
        """Parse XML file with multiple format detection"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            filename = os.path.basename(file_path)
            
            # Detect file type and parse accordingly
            if 'uk_' in filename.lower():
                self._parse_uk_format(root, filename)
            elif 'eu_' in filename.lower():
                self._parse_eu_format(root, filename)
            elif 'ofac_' in filename.lower():
                self._parse_ofac_format(root, filename)
            elif 'un_' in filename.lower():
                self._parse_un_format(root, filename)
            else:
                self._parse_generic_xml(root, filename)
                
        except Exception as e:
            self.logger.error(f"XML parsing error for {file_path}: {str(e)}")
    
    def _parse_uk_format(self, root: ET.Element, source: str):
        """Parse UK sanctions format"""
        entities_parsed = 0
        # UK format typically has Designations -> Designation
        for designation in root.findall('.//Designation') + root.findall('.//designation'):
            try:
                names = []
                primary_name = ""
                
                # Extract names from various possible elements
                for name_elem in designation.findall('.//Name') + designation.findall('.//name'):
                    if name_elem.text and name_elem.text.strip():
                        names.append(name_elem.text.strip())
                
                for title_elem in designation.findall('.//Title') + designation.findall('.//title'):
                    if title_elem.text and title_elem.text.strip():
                        names.append(title_elem.text.strip())
                
                # Use the first non-empty name as primary
                if names:
                    primary_name = names[0]
                    
                    entity = {
                        'source': source,
                        'list_type': 'UK',
                        'names': names,
                        'primary_name': primary_name,
                        'type': 'entity',
                        'id': designation.get('ID', ''),
                        'regime': self._extract_text(designation, './/RegimeName')
                    }
                    
                    self.parsed_entities.append(entity)
                    entities_parsed += 1
                    
            except Exception as e:
                self.logger.warning(f"Error parsing UK designation: {e}")
                continue
        
        self.logger.info(f"📊 Parsed {entities_parsed} entities from UK file")
    
    def _parse_ofac_format(self, root: ET.Element, source: str):
        """Parse OFAC sanctions format"""
        entities_parsed = 0
        # OFAC format typically has sdnEntries -> sdnEntry
        for entry in root.findall('.//sdnEntry') + root.findall('.//entry'):
            try:
                names = []
                primary_name = ""
                
                # OFAC has firstName, lastName for individuals, title for entities
                first_name = self._extract_text(entry, './/firstName')
                last_name = self._extract_text(entry, './/lastName')
                title = self._extract_text(entry, './/title')
                
                if first_name and last_name:
                    primary_name = f"{first_name} {last_name}".strip()
                    names.append(primary_name)
                elif title:
                    primary_name = title
                    names.append(primary_name)
                
                if primary_name:
                    entity = {
                        'source': source,
                        'list_type': 'OFAC',
                        'names': names,
                        'primary_name': primary_name,
                        'type': 'individual' if first_name else 'entity',
                        'id': entry.get('ID', ''),
                        'address': self._extract_text(entry, './/address')
                    }
                    
                    self.parsed_entities.append(entity)
                    entities_parsed += 1
                    
            except Exception as e:
                self.logger.warning(f"Error parsing OFAC entry: {e}")
                continue
        
        self.logger.info(f"📊 Parsed {entities_parsed} entities from OFAC file")
    
    def _parse_eu_format(self, root: ET.Element, source: str):
        """Parse EU sanctions format"""
        entities_parsed = 0
        # EU format varies, try common patterns
        for party in root.findall('.//party') + root.findall('.//Entity') + root.findall('.//entity'):
            try:
                names = []
                primary_name = ""
                
                # Try different name elements
                name_text = self._extract_text(party, './/name') or self._extract_text(party, './/title')
                if name_text:
                    primary_name = name_text
                    names.append(primary_name)
                
                if primary_name:
                    entity = {
                        'source': source,
                        'list_type': 'EU',
                        'names': names,
                        'primary_name': primary_name,
                        'type': 'entity',
                        'id': party.get('id', ''),
                        'regulation': self._extract_text(party, './/regulation')
                    }
                    
                    self.parsed_entities.append(entity)
                    entities_parsed += 1
                    
            except Exception as e:
                self.logger.warning(f"Error parsing EU party: {e}")
                continue
        
        self.logger.info(f"📊 Parsed {entities_parsed} entities from EU file")
    
    def _parse_un_format(self, root: ET.Element, source: str):
        """Parse UN sanctions format"""
        entities_parsed = 0
        # UN format - try various patterns
        for individual in root.findall('.//INDIVIDUAL') + root.findall('.//individual'):
            try:
                names = []
                primary_name = ""
                
                first_name = self._extract_text(individual, './/FIRST_NAME')
                second_name = self._extract_text(individual, './/SECOND_NAME')
                third_name = self._extract_text(individual, './/THIRD_NAME')
                
                if first_name:
                    full_name = f"{first_name} {second_name or ''} {third_name or ''}".strip()
                    primary_name = full_name
                    names.append(primary_name)
                
                if primary_name:
                    entity = {
                        'source': source,
                        'list_type': 'UN',
                        'names': names,
                        'primary_name': primary_name,
                        'type': 'individual',
                        'id': individual.get('ID', '')
                    }
                    
                    self.parsed_entities.append(entity)
                    entities_parsed += 1
                    
            except Exception as e:
                self.logger.warning(f"Error parsing UN individual: {e}")
                continue
        
        self.logger.info(f"📊 Parsed {entities_parsed} entities from UN file")
    
    def _parse_generic_xml(self, root: ET.Element, source: str):
        """Fallback parser for generic XML formats"""
        entities_parsed = 0
        
        # Try to find any elements that might contain names
        for elem in root.iter():
            if elem.text and len(elem.text.strip()) > 3:  # Reasonable length
                text = elem.text.strip()
                # Skip if it looks like XML tags or garbage
                if not text.startswith('<') and not text.endswith('>') and ' ' in text:
                    entity = {
                        'source': source,
                        'list_type': 'Generic',
                        'names': [text],
                        'primary_name': text,
                        'type': 'entity',
                        'id': elem.get('id', '')
                    }
                    
                    self.parsed_entities.append(entity)
                    entities_parsed += 1
        
        self.logger.info(f"📊 Parsed {entities_parsed} entities from generic XML")
    
    def _parse_csv_file(self, file_path: str):
        """Parse CSV file"""
        try:
            df = pd.read_csv(file_path)
            filename = os.path.basename(file_path)
            
            for _, row in df.iterrows():
                # Try different column names for entity names
                name = None
                for col in ['name', 'Name', 'ENTITY', 'entity', 'TITLE', 'title']:
                    if col in row and pd.notna(row[col]):
                        name = str(row[col]).strip()
                        break
                
                if name and len(name) > 2:
                    entity = {
                        'source': filename,
                        'list_type': 'CSV',
                        'names': [name],
                        'primary_name': name,
                        'type': 'entity'
                    }
                    self.parsed_entities.append(entity)
                    
        except Exception as e:
            self.logger.error(f"CSV parsing error: {e}")
    
    def _parse_txt_file(self, file_path: str):
        """Parse simple text file with one entity per line"""
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and len(line) > 2 and not line.startswith('#'):
                        entity = {
                            'source': filename,
                            'list_type': 'TXT',
                            'names': [line],
                            'primary_name': line,
                            'type': 'entity'
                        }
                        self.parsed_entities.append(entity)
        except Exception as e:
            self.logger.error(f"TXT parsing error: {e}")
    
    def _extract_text(self, element: ET.Element, xpath: str) -> str:
        """Extract text from XML element using XPath"""
        try:
            found = element.find(xpath)
            if found is not None and found.text:
                return found.text.strip()
        except:
            pass
        return ""
    
    def get_all_entities(self) -> List[Dict]:
        """Get all parsed entities"""
        return self.parsed_entities
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert parsed entities to DataFrame"""
        if not self.parsed_entities:
            return pd.DataFrame()
        
        return pd.DataFrame(self.parsed_entities)
