"""
Complete Sanctions Service with all required functions
"""
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
from datetime import datetime, timedelta
import pickle
import os
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class SanctionsService:
    """Main sanctions service"""
    
    def __init__(self, data_dir="data", cache_file="instance/sanctions_cache.pkl"):
        self.data_dir = Path(data_dir)
        self.cache_file = cache_file
        self.sanctions_entities = []
        self.last_loaded = None
        self.file_hashes = {}
        self._load_or_parse_sanctions()
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file to detect changes"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _have_files_changed(self) -> bool:
        """Check if any XML files have changed since last load"""
        xml_files = list(self.data_dir.glob('*.xml'))
        
        if len(xml_files) != len(self.file_hashes):
            return True
        
        for xml_file in xml_files:
            current_hash = self._get_file_hash(xml_file)
            if xml_file.name not in self.file_hashes or self.file_hashes[xml_file.name] != current_hash:
                return True
        
        return False
    
    def _load_or_parse_sanctions(self):
        """Load from cache or parse fresh with file change detection"""
        cache_valid = False
        
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.sanctions_entities = cache_data['entities']
                    self.last_loaded = cache_data['last_loaded']
                    self.file_hashes = cache_data['file_hashes']
                
                if not self._have_files_changed():
                    cache_valid = True
                    logger.info(f"Loaded {len(self.sanctions_entities)} entities from cache")
                else:
                    logger.info("XML files changed, rebuilding cache")
                    
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")
        
        if not cache_valid:
            # Parse fresh
            self.sanctions_entities = self._parse_all_sanctions()
            self.last_loaded = datetime.now()
            
            # Store file hashes for change detection
            self.file_hashes = {}
            xml_files = list(self.data_dir.glob('*.xml'))
            for xml_file in xml_files:
                self.file_hashes[xml_file.name] = self._get_file_hash(xml_file)
            
            # Save to cache
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'entities': self.sanctions_entities,
                    'last_loaded': self.last_loaded,
                    'file_hashes': self.file_hashes
                }, f)
            logger.info(f"Cached {len(self.sanctions_entities)} entities")
    
    def _parse_all_sanctions(self) -> List[Dict[str, Any]]:
        """Parse all XML sanctions files"""
        import xml.etree.ElementTree as ET
        xml_files = list(self.data_dir.glob('*.xml'))
        all_entities = []
        
        for xml_file in xml_files:
            try:
                print(f"📁 Parsing {xml_file.name}...")
                tree = ET.parse(xml_file)
                root = tree.getroot()
                filename = xml_file.name.lower()
                
                if 'uk' in filename:
                    entities = self._parse_uk_format(root, str(xml_file.name))
                elif 'eu' in filename:
                    entities = self._parse_eu_format(root, str(xml_file.name))
                elif 'un' in filename:
                    entities = self._parse_un_format(root, str(xml_file.name))
                elif 'ofac' in filename:
                    entities = self._parse_ofac_format(root, str(xml_file.name))
                else:
                    entities = self._parse_generic(root, str(xml_file.name))
                
                all_entities.extend(entities)
                print(f"   ✅ Extracted {len(entities)} entities from {xml_file.name}")
                
            except Exception as e:
                print(f"   ❌ Error parsing {xml_file.name}: {e}")
                
        return all_entities
    
    def _parse_uk_format(self, root, source: str) -> List[Dict[str, Any]]:
        """Parse UK Designations format"""
        entities = []
        for designation in root.findall('.//Designation'):
            names = []
            for name_elem in designation.findall('.//Name'):
                if name_elem.text and name_elem.text.strip():
                    names.append(name_elem.text.strip())
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
    
    def _parse_eu_format(self, root, source: str) -> List[Dict[str, Any]]:
        """Parse EU consolidated format"""
        entities = []
        ns = {'fsd': 'http://eu.europa.ec/fpi/fsd/export'}
        
        for entity_elem in root.findall('.//fsd:sanctionEntity', ns):
            names = []
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
    
    def _parse_un_format(self, root, source: str) -> List[Dict[str, Any]]:
        """Parse UN consolidated list"""
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
            name = self._get_text(entity_elem, './/FIRST_NAME')
            if name:
                entities.append({
                    'source': source,
                    'list_type': 'UN',
                    'names': [name],
                    'primary_name': name,
                    'type': 'entity'
                })
        
        return entities
    
    def _parse_ofac_format(self, root, source: str) -> List[Dict[str, Any]]:
        """Parse OFAC SDN list"""
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
    
    def _parse_generic(self, root, source: str) -> List[Dict[str, Any]]:
        """Generic fallback parser"""
        entities = []
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
    
    def _get_text(self, parent, xpath: str, namespaces=None) -> Optional[str]:
        elem = parent.find(xpath, namespaces)
        return elem.text.strip() if elem is not None and elem.text else None

class OptimalFuzzyMatcher:
    """Optimal fuzzy matching"""
    
    def __init__(self, sanctions_entities):
        self.sanctions_entities = sanctions_entities
        self.all_names = []
        
        # Build name index
        for entity in sanctions_entities:
            for name in entity.get('names', []):
                if name and len(name.strip()) > 1:
                    self.all_names.append((self._normalize_name(name), entity, name))
    
    def _normalize_name(self, name: str) -> str:
        """Advanced name normalization"""
        if not name:
            return ""
        
        # Basic cleaning
        name = str(name).lower().strip()
        name = unidecode(name)  # Remove accents
        
        # Remove legal entities
        legal_entities = ['ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation',
                         'llc', 'gmbh', 'sa', 'nv', 'plc', 'co', 'company', 'group']
        for entity in legal_entities:
            name = re.sub(r'\b' + re.escape(entity) + r'\b', '', name)
        
        # Clean up
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove stop words and sort for consistent matching
        stop_words = {'the', 'and', 'of', 'for', 'with', 'from', 'to', 'in', 'a', 'an'}
        words = [w for w in name.split() if w not in stop_words and len(w) > 1]
        words_sorted = sorted(words)
        
        return ' '.join(words_sorted)
    
    def match_entity(self, search_name: str, entity_type: str = None, threshold: int = 80) -> List[Dict[str, Any]]:
        """Match with optimal strategy"""
        if not search_name:
            return []
        
        normalized_search = self._normalize_name(search_name)
        if not normalized_search:
            return []
        
        # Lower threshold for company/organization matching since names vary more
        effective_threshold = threshold
        if entity_type in ['company', 'organization', 'entity']:
            effective_threshold = min(threshold, 65)
        
        matches = []
        seen_entities = set()
        
        for normalized_db_name, entity, original_name in self.all_names:
            # Entity type filtering - map 'company' to include 'entity' type from sanctions lists
            if entity_type:
                db_type = entity.get('type', '').lower()
                # Companies should match 'entity' type in sanctions data
                if entity_type in ['company', 'organization']:
                    if db_type and db_type not in ['entity', 'unknown', 'company', 'organization']:
                        continue
                elif entity_type == 'individual':
                    if db_type and db_type not in ['individual', 'unknown', 'person']:
                        continue
            
            # Calculate score using multiple strategies
            score1 = fuzz.token_sort_ratio(normalized_search, normalized_db_name)
            score2 = fuzz.token_set_ratio(normalized_search, normalized_db_name)
            score = max(score1, score2)
            
            if score >= effective_threshold:
                entity_id = id(entity)
                if entity_id not in seen_entities:
                    seen_entities.add(entity_id)
                    matches.append({
                        'entity': entity,
                        'score': score,
                        'matched_name': original_name,
                        'search_name': search_name
                    })
        
        # Sort by score and return
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:10]

# Global instances
sanctions_service = None
fuzzy_matcher = None

def init_sanctions_service():
    """Initialize the sanctions service"""
    global sanctions_service, fuzzy_matcher
    sanctions_service = SanctionsService()
    fuzzy_matcher = OptimalFuzzyMatcher(sanctions_service.sanctions_entities)
    return f"Sanctions service initialized with {len(sanctions_service.sanctions_entities)} entities"

def get_sanctions_stats():
    """Get statistics about loaded sanctions"""
    if not sanctions_service:
        return {"error": "Sanctions service not initialized"}
    
    stats = {
        'total_entities': len(sanctions_service.sanctions_entities),
        'last_loaded': sanctions_service.last_loaded.isoformat() if sanctions_service.last_loaded else None,
        'sources': {}
    }
    
    # Count by source
    for entity in sanctions_service.sanctions_entities:
        source = entity['source']
        if source not in stats['sources']:
            stats['sources'][source] = 0
        stats['sources'][source] += 1
    
    return stats

def screen_entity(name: str, entity_type: str = None, threshold: int = 80):
    """Screen a single entity against sanctions"""
    if not fuzzy_matcher:
        return []
    
    return fuzzy_matcher.match_entity(name, entity_type, threshold)


def reload_sanctions_data():
    """Force reload sanctions data"""
    global sanctions_service, fuzzy_matcher
    sanctions_service = SanctionsService()
    fuzzy_matcher = OptimalFuzzyMatcher(sanctions_service.sanctions_entities)
    return f"Reloaded {len(sanctions_service.sanctions_entities)} entities"
