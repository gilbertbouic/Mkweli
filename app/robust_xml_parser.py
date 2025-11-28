"""
Robust XML Parser with comprehensive error handling for sanctions lists
"""
import xml.etree.ElementTree as ET
from lxml import etree
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)

class RobustXMLParser:
    """Robust XML parser with multiple fallback strategies"""
    
    def __init__(self):
        self.parsed_files = {}
    
    def parse_file(self, file_path: Path, source_name: str) -> List[Dict[str, Any]]:
        """Parse XML file with multiple fallback strategies"""
        file_hash = self._get_file_hash(file_path)
        
        # Check if we've already parsed this file (same content)
        if file_hash in self.parsed_files:
            logger.info(f"Using cached parse for {source_name}")
            return self.parsed_files[file_hash]
        
        strategies = [
            self._parse_standard,
            self._parse_lxml_recover,
            self._parse_lxml_html,  # Fallback to HTML parser for really broken XML
        ]
        
        for strategy in strategies:
            try:
                entities = strategy(file_path, source_name)
                if entities:
                    logger.info(f"Strategy {strategy.__name__} succeeded for {source_name}: {len(entities)} entities")
                    self.parsed_files[file_hash] = entities
                    return entities
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed for {source_name}: {e}")
                continue
        
        logger.error(f"All parsing strategies failed for {source_name}")
        return []
    
    def _parse_standard(self, file_path: Path, source_name: str) -> List[Dict[str, Any]]:
        """Standard XML parsing"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        return self._extract_entities(root, source_name, "standard")
    
    def _parse_lxml_recover(self, file_path: Path, source_name: str) -> List[Dict[str, Any]]:
        """lxml with recovery mode"""
        parser = etree.XMLParser(recover=True, huge_tree=True)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()
        return self._extract_entities(root, source_name, "lxml_recover")
    
    def _parse_lxml_html(self, file_path: Path, source_name: str) -> List[Dict[str, Any]]:
        """Fallback to HTML parser for extremely broken XML"""
        parser = etree.HTMLParser()
        tree = etree.parse(file_path, parser)
        root = tree.getroot()
        return self._extract_entities(root, source_name, "lxml_html")
    
    def _extract_entities(self, root, source_name: str, method: str) -> List[Dict[str, Any]]:
        """Extract entities from parsed XML root"""
        entities = []
        
        # UK format
        if 'uk' in source_name.lower():
            for designation in root.findall('.//Designation'):
                entity = self._parse_uk_designation(designation, source_name)
                if entity:
                    entities.append(entity)
        
        # EU format  
        elif 'eu' in source_name.lower():
            # Find sanctionEntity elements by iterating (handles default namespace)
            for elem in root.iter():
                if elem.tag.endswith('}sanctionEntity') or elem.tag == 'sanctionEntity':
                    entity = self._parse_eu_entity(elem, source_name, None)
                    if entity:
                        entities.append(entity)
        
        # UN format
        elif 'un' in source_name.lower():
            entities.extend(self._parse_un_format(root, source_name))
        
        # OFAC format
        elif 'ofac' in source_name.lower():
            # Find entities container
            entities_container = None
            for elem in root.iter():
                if elem.tag.endswith('}entities') or elem.tag == 'entities':
                    entities_container = elem
                    break
            
            if entities_container is not None:
                for entity_elem in entities_container.iter():
                    if entity_elem.tag.endswith('}entity') or entity_elem.tag == 'entity':
                        entity = self._parse_ofac_entry(entity_elem, source_name, None)
                        if entity:
                            entities.append(entity)
        
        # Generic fallback - look for any elements with names
        else:
            entities.extend(self._parse_generic_format(root, source_name))
        
        logger.info(f"Extracted {len(entities)} entities from {source_name} using {method}")
        return entities
    
    def _parse_uk_designation(self, designation, source_name: str) -> Optional[Dict[str, Any]]:
        """Parse UK designation format"""
        try:
            names = []
            for name_elem in designation.findall('.//Name'):
                if name_elem.text and name_elem.text.strip():
                    names.append(name_elem.text.strip())
            
            for name6_elem in designation.findall('.//Name6'):
                if name6_elem.text and name6_elem.text.strip():
                    names.append(name6_elem.text.strip())
            
            if names:
                return {
                    'source': source_name,
                    'list_type': 'UK',
                    'names': names,
                    'primary_name': names[0],
                    'type': 'unknown',
                    'parse_method': 'uk_designation'
                }
        except Exception as e:
            logger.warning(f"Error parsing UK designation: {e}")
        
        return None
    
    def _parse_eu_entity(self, entity_elem, source_name: str, ns) -> Optional[Dict[str, Any]]:
        """Parse EU entity format"""
        try:
            names = []
            entity_type = 'entity'
            
            # Find nameAlias elements and extract wholeName ATTRIBUTE
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
            
            if names:
                return {
                    'source': source_name,
                    'list_type': 'EU',
                    'names': list(set(names)),
                    'primary_name': names[0],
                    'type': entity_type,
                    'parse_method': 'eu_entity'
                }
        except Exception as e:
            logger.warning(f"Error parsing EU entity: {e}")
        
        return None
    
    def _parse_un_format(self, root, source_name: str) -> List[Dict[str, Any]]:
        """Parse UN consolidated format"""
        entities = []
        
        # Individuals
        for individual in root.findall('.//INDIVIDUAL'):
            entity = self._parse_un_individual(individual, source_name)
            if entity:
                entities.append(entity)
        
        # Entities
        for entity_elem in root.findall('.//ENTITY'):
            entity = self._parse_un_entity(entity_elem, source_name)
            if entity:
                entities.append(entity)
        
        return entities
    
    def _parse_un_individual(self, individual, source_name: str) -> Optional[Dict[str, Any]]:
        """Parse UN individual"""
        try:
            names = []
            first_name = self._get_text(individual, './/FIRST_NAME')
            second_name = self._get_text(individual, './/SECOND_NAME')
            
            if first_name and second_name:
                names.append(f"{first_name} {second_name}".strip())
            elif first_name:
                names.append(first_name)
            
            for alias in individual.findall('.//ALIAS_NAME'):
                if alias.text:
                    names.append(alias.text.strip())
            
            if names:
                return {
                    'source': source_name,
                    'list_type': 'UN',
                    'names': names,
                    'primary_name': names[0],
                    'type': 'individual',
                    'parse_method': 'un_individual'
                }
        except Exception as e:
            logger.warning(f"Error parsing UN individual: {e}")
        
        return None
    
    def _parse_un_entity(self, entity_elem, source_name: str) -> Optional[Dict[str, Any]]:
        """Parse UN entity"""
        try:
            name = self._get_text(entity_elem, './/FIRST_NAME')
            if name:
                return {
                    'source': source_name,
                    'list_type': 'UN',
                    'names': [name],
                    'primary_name': name,
                    'type': 'entity',
                    'parse_method': 'un_entity'
                }
        except Exception as e:
            logger.warning(f"Error parsing UN entity: {e}")
        
        return None
    
    def _parse_ofac_entry(self, entity_elem, source_name: str, ns) -> Optional[Dict[str, Any]]:
        """Parse OFAC SDN Enhanced XML entry"""
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
            for gen_elem in entity_elem.iter():
                if gen_elem.tag.endswith('}entityType') or gen_elem.tag == 'entityType':
                    if gen_elem.text:
                        type_text = gen_elem.text.strip().lower()
                        if 'individual' in type_text or 'person' in type_text:
                            entity_type = 'individual'
            
            if names:
                return {
                    'source': source_name,
                    'list_type': 'OFAC',
                    'names': list(set(names)),
                    'primary_name': names[0],
                    'type': entity_type,
                    'parse_method': 'ofac_entry'
                }
        except Exception as e:
            logger.warning(f"Error parsing OFAC entry: {e}")
        
        return None
    
    def _parse_generic_format(self, root, source_name: str) -> List[Dict[str, Any]]:
        """Generic fallback parser"""
        entities = []
        name_elements = root.findall('.//*')
        
        for elem in name_elements:
            try:
                if (elem.text and len(elem.text.strip()) > 2 and 
                    any(keyword in elem.tag.lower() for keyword in ['name', 'title', 'designation'])):
                    
                    name = elem.text.strip()
                    if self._looks_like_entity_name(name):
                        entities.append({
                            'source': source_name,
                            'list_type': 'Generic',
                            'names': [name],
                            'primary_name': name,
                            'type': 'unknown',
                            'parse_method': 'generic_fallback'
                        })
            except Exception as e:
                continue
        
        return entities
    
    def _get_text(self, parent, xpath: str, namespaces=None) -> Optional[str]:
        """Safely get text from element"""
        try:
            elem = parent.find(xpath, namespaces)
            return elem.text.strip() if elem is not None and elem.text else None
        except:
            return None
    
    def _looks_like_entity_name(self, text: str) -> bool:
        """Check if text looks like an entity name"""
        if not text or len(text) < 3:
            return False
        
        excluded_patterns = [r'^\d+$', r'^http', r'^@']
        import re
        for pattern in excluded_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        
        return any(c.isalpha() for c in text)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get file hash for caching"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
