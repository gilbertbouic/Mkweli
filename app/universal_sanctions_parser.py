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
        """Parse OFAC sanctions format (Enhanced XML format)"""
        entities_parsed = 0
        # OFAC Enhanced XML uses default namespace
        ns = {'ofac': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML'}
        
        # Find entities container
        entities_container = None
        for elem in root.iter():
            if elem.tag.endswith('}entities') or elem.tag == 'entities':
                entities_container = elem
                break
        
        if entities_container is None:
            self.logger.warning(f"No entities container found in OFAC file {source}")
            return
        
        # Find all entity elements
        for entity_elem in entities_container.iter():
            if not (entity_elem.tag.endswith('}entity') or entity_elem.tag == 'entity'):
                continue
            
            try:
                names = []
                entity_type = 'entity'
                
                # OFAC structure: entity > names > name > translations > translation > formattedFullName
                for trans_elem in entity_elem.iter():
                    if trans_elem.tag.endswith('}translation') or trans_elem.tag == 'translation':
                        for child in trans_elem:
                            if child.tag.endswith('}formattedFullName') or child.tag == 'formattedFullName':
                                if child.text and child.text.strip():
                                    names.append(child.text.strip())
                
                # Determine entity type from generalInfo > entityType
                for gen_info in entity_elem.iter():
                    if gen_info.tag.endswith('}entityType') or gen_info.tag == 'entityType':
                        if gen_info.text:
                            type_text = gen_info.text.strip().lower()
                            if 'individual' in type_text or 'person' in type_text:
                                entity_type = 'individual'
                            elif 'entity' in type_text:
                                entity_type = 'entity'
                
                if names:
                    entity = {
                        'source': source,
                        'list_type': 'OFAC',
                        'names': list(dict.fromkeys(names)),  # Remove duplicates while preserving order
                        'primary_name': names[0],
                        'type': entity_type,
                        'id': entity_elem.get('id', '')
                    }
                    
                    self.parsed_entities.append(entity)
                    entities_parsed += 1
                    
            except Exception as e:
                self.logger.warning(f"Error parsing OFAC entry: {e}")
                continue
        
        self.logger.info(f"📊 Parsed {entities_parsed} entities from OFAC file")
    
    def _parse_eu_format(self, root: ET.Element, source: str):
        """Parse EU sanctions format (FSD export format)"""
        entities_parsed = 0
        # EU uses default namespace
        ns = {'eu': 'http://eu.europa.ec/fpi/fsd/export'}
        
        # Find sanctionEntity elements - handle namespaced elements
        entity_elems = []
        for elem in root.iter():
            if elem.tag.endswith('}sanctionEntity') or elem.tag == 'sanctionEntity':
                entity_elems.append(elem)
        
        for entity_elem in entity_elems:
            try:
                names = []
                entity_type = 'entity'
                
                # Find nameAlias elements and extract wholeName attribute
                for child in entity_elem.iter():
                    if child.tag.endswith('}nameAlias') or child.tag == 'nameAlias':
                        whole_name = child.get('wholeName')
                        if whole_name and whole_name.strip():
                            names.append(whole_name.strip())
                
                # Determine entity type from subjectType
                for child in entity_elem.iter():
                    if child.tag.endswith('}subjectType') or child.tag == 'subjectType':
                        code = child.get('code', '').lower()
                        if 'person' in code:
                            entity_type = 'individual'
                        elif 'entity' in code or 'organisation' in code:
                            entity_type = 'entity'
                
                if names:
                    entity = {
                        'source': source,
                        'list_type': 'EU',
                        'names': list(dict.fromkeys(names)),  # Remove duplicates while preserving order
                        'primary_name': names[0],
                        'type': entity_type,
                        'id': entity_elem.get('logicalId', '')
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
