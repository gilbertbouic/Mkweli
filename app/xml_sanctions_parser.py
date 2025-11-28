import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class UniversalSanctionsParser:
    """Parse multiple XML sanctions list formats into unified structure"""
    
    def __init__(self):
        self.parsed_entities = []
        
    def parse_all_sanctions(self, data_dir: str = "data") -> List[Dict[str, Any]]:
        """Parse all XML sanctions files in directory"""
        data_path = Path(data_dir)
        xml_files = list(data_path.glob('*.xml'))
        
        all_entities = []
        
        for xml_file in xml_files:
            try:
                logger.info(f"Parsing {xml_file.name}")
                entities = self._parse_file(xml_file)
                all_entities.extend(entities)
                logger.info(f"Extracted {len(entities)} entities from {xml_file.name}")
            except Exception as e:
                logger.error(f"Error parsing {xml_file.name}: {e}")
                
        self.parsed_entities = all_entities
        return all_entities
    
    def _parse_file(self, xml_file: Path) -> List[Dict[str, Any]]:
        """Parse individual XML file with format detection"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            filename = xml_file.name.lower()
            
            if 'uk' in filename:
                return self._parse_uk_format(root, str(xml_file.name))
            elif 'eu' in filename:
                return self._parse_eu_format(root, str(xml_file.name))
            elif 'un' in filename:
                return self._parse_un_format(root, str(xml_file.name))
            elif 'ofac' in filename:
                return self._parse_ofac_format(root, str(xml_file.name))
            else:
                return self._parse_auto_detect(root, str(xml_file.name))
                
        except ET.ParseError as e:
            logger.error(f"XML parse error in {xml_file.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading {xml_file.name}: {e}")
            return []
    
    def _parse_uk_format(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Parse UK Designations format"""
        entities = []
        
        # UK format has Designation elements under Designations root
        for designation in root.findall('.//Designation'):
            entity = {
                'source': source,
                'list_type': 'UK',
                'raw_data': {}
            }
            
            names = []
            
            # Extract names from Name elements
            for name_elem in designation.findall('.//Name'):
                if name_elem.text and name_elem.text.strip():
                    names.append(name_elem.text.strip())
            
            # Also check Name6 elements (appears in your debug output)
            for name6_elem in designation.findall('.//Name6'):
                if name6_elem.text and name6_elem.text.strip():
                    names.append(name6_elem.text.strip())
            
            if names:
                entity['names'] = names
                entity['primary_name'] = names[0]
                
                # Extract type (Individual/Entity)
                entity_type_elem = designation.find('.//IndividualEntityShip')
                entity['type'] = entity_type_elem.text.lower() if entity_type_elem is not None else 'unknown'
                
                # Extract other details
                entity['id'] = self._extract_text(designation, './/UniqueID')
                entity['regime'] = self._extract_text(designation, './/RegimeName')
                
                entities.append(entity)
        
        return entities
    
    def _parse_eu_format(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Parse EU consolidated format with namespace"""
        entities = []
        
        # Register namespace
        ns = {'fsd': 'http://eu.europa.ec/fpi/fsd/export'}
        
        # Find sanctionEntity elements - handle default namespace
        entity_elems = []
        for elem in root.iter():
            if elem.tag.endswith('}sanctionEntity') or elem.tag == 'sanctionEntity':
                entity_elems.append(elem)
        
        for sanction_entity in entity_elems:
            entity = {
                'source': source,
                'list_type': 'EU',
                'raw_data': {}
            }
            
            names = []
            entity_type = 'entity'
            
            # Extract names from nameAlias elements - wholeName is an ATTRIBUTE
            for child in sanction_entity.iter():
                if child.tag.endswith('}nameAlias') or child.tag == 'nameAlias':
                    whole_name = child.get('wholeName')
                    if whole_name and whole_name.strip():
                        names.append(whole_name.strip())
            
            # Determine entity type from subjectType
            for child in sanction_entity.iter():
                if child.tag.endswith('}subjectType') or child.tag == 'subjectType':
                    code = child.get('code', '').lower()
                    if 'person' in code:
                        entity_type = 'individual'
            
            if names:
                entity['names'] = list(dict.fromkeys(names))  # Remove duplicates while preserving order
                entity['primary_name'] = names[0]
                entity['type'] = entity_type
                
                # Extract ID
                entity['id'] = sanction_entity.get('logicalId', '')
                
                entities.append(entity)
        
        return entities
    
    def _parse_un_format(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Parse UN consolidated list format"""
        entities = []
        
        # Parse individuals
        individuals_section = root.find('.//INDIVIDUALS')
        if individuals_section is not None:
            for individual in individuals_section.findall('.//INDIVIDUAL'):
                entity = self._parse_un_individual(individual, source)
                if entity:
                    entities.append(entity)
        
        # Parse entities
        entities_section = root.find('.//ENTITIES')
        if entities_section is not None:
            for entity_elem in entities_section.findall('.//ENTITY'):
                entity = self._parse_un_entity(entity_elem, source)
                if entity:
                    entities.append(entity)
                
        return entities
    
    def _parse_un_individual(self, individual: ET.Element, source: str) -> Optional[Dict[str, Any]]:
        """Parse UN individual record"""
        names = []
        
        # Construct full name from components
        first_name = self._extract_text(individual, './/FIRST_NAME')
        second_name = self._extract_text(individual, './/SECOND_NAME')
        third_name = self._extract_text(individual, './/THIRD_NAME')
        
        full_name_parts = []
        if first_name:
            full_name_parts.append(first_name)
        if second_name:
            full_name_parts.append(second_name)
        if third_name:
            full_name_parts.append(third_name)
        
        if full_name_parts:
            names.append(' '.join(full_name_parts))
        
        # Add alias names
        for alias in individual.findall('.//ALIAS_NAME'):
            if alias.text and alias.text.strip():
                names.append(alias.text.strip())
        
        if not names:
            return None
            
        return {
            'source': source,
            'list_type': 'UN',
            'names': names,
            'primary_name': names[0],
            'type': 'individual',
            'countries': [self._extract_text(individual, './/NATIONALITY')],
            'id': self._extract_text(individual, './/DATAID')
        }
    
    def _parse_un_entity(self, entity_elem: ET.Element, source: str) -> Optional[Dict[str, Any]]:
        """Parse UN entity record"""
        names = []
        
        # Primary name
        first_name = self._extract_text(entity_elem, './/FIRST_NAME')
        if first_name:
            names.append(first_name)
        
        # Additional names
        for alias in entity_elem.findall('.//ALIAS_NAME'):
            if alias.text and alias.text.strip():
                names.append(alias.text.strip())
        
        if not names:
            return None
            
        return {
            'source': source,
            'list_type': 'UN',
            'names': names,
            'primary_name': names[0],
            'type': 'entity',
            'countries': [self._extract_text(entity_elem, './/COUNTRY')],
            'id': self._extract_text(entity_elem, './/DATAID')
        }
    
    def _parse_ofac_format(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Parse OFAC SDN Enhanced XML format with namespace"""
        entities = []
        
        # OFAC Enhanced XML uses default namespace
        ns = {'ofac': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML'}
        
        # Find entities container
        entities_container = None
        for elem in root.iter():
            if elem.tag.endswith('}entities') or elem.tag == 'entities':
                entities_container = elem
                break
        
        if entities_container is None:
            return entities
        
        # Find all entity elements
        for entity_elem in entities_container.iter():
            if not (entity_elem.tag.endswith('}entity') or entity_elem.tag == 'entity'):
                continue
            
            entity = {
                'source': source,
                'list_type': 'OFAC',
                'raw_data': {}
            }
            
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
                entity['names'] = list(dict.fromkeys(names))  # Remove duplicates while preserving order
                entity['primary_name'] = names[0]
                entity['type'] = entity_type
                
                # Extract ID
                entity['id'] = entity_elem.get('id', '')
                
                entities.append(entity)
        
        return entities
    
    def _parse_auto_detect(self, root: ET.Element, source: str) -> List[Dict[str, Any]]:
        """Auto-detect and parse unknown XML format"""
        entities = []
        
        # Simple heuristic: look for elements with text that look like names
        for elem in root.iter():
            if (elem.text and 
                len(elem.text.strip()) > 3 and 
                any(keyword in elem.tag.lower() for keyword in ['name', 'title', 'designation'])):
                
                name = elem.text.strip()
                if self._looks_like_entity_name(name):
                    entity = {
                        'source': source,
                        'list_type': 'Generic',
                        'names': [name],
                        'primary_name': name,
                        'type': 'unknown'
                    }
                    entities.append(entity)
        
        return entities
    
    def _looks_like_entity_name(self, text: str) -> bool:
        """Heuristic to check if text looks like an entity name"""
        # Exclude obviously non-name text
        excluded_patterns = [
            r'^\d+$',  # Pure numbers
            r'^http',  # URLs
            r'^@',     # Email-like
        ]
        
        for pattern in excluded_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        
        return len(text) >= 3 and any(c.isalpha() for c in text)
    
    def _extract_text(self, parent: ET.Element, xpath: str, namespaces=None) -> Optional[str]:
        """Extract text from element using XPath"""
        elem = parent.find(xpath, namespaces)
        return elem.text.strip() if elem is not None and elem.text else None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert parsed entities to DataFrame"""
        if not self.parsed_entities:
            return pd.DataFrame()
            
        # Flatten the structure for DataFrame
        flattened = []
        for entity in self.parsed_entities:
            for name in entity.get('names', []):
                flattened.append({
                    'name': name,
                    'primary_name': entity.get('primary_name'),
                    'source': entity.get('source'),
                    'list_type': entity.get('list_type'),
                    'entity_type': entity.get('type', 'unknown'),
                    'entity_id': entity.get('id'),
    'countries': ', '.join([str(c) for c in entity.get('countries', []) if c is not None]) if entity.get('countries') else ''
                })
        
        return pd.DataFrame(flattened)
