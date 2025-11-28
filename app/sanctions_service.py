import os
import re
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SanctionsService:
    def __init__(self, data_dir="data", cache_file="instance/sanctions_cache.pkl"):
        self.data_dir = Path(data_dir)
        self.cache_file = cache_file
        self.sanctions_entities = []
        self.last_loaded = None
        self.file_hashes = {}
        self.all_names = []  # For fuzzy matching optimization
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
            
            # Build name index for fuzzy matching
            self._build_name_index()
    
    def _build_name_index(self):
        """Build optimized index for fuzzy matching"""
        self.all_names = []
        for entity in self.sanctions_entities:
            for name in entity.get('names', []):
                self.all_names.append((name.lower(), entity, name))
    
    def _parse_all_sanctions(self) -> List[Dict[str, Any]]:
        """Parse all XML sanctions files with better error handling"""
        import xml.etree.ElementTree as ET
        xml_files = list(self.data_dir.glob('*.xml'))
        all_entities = []
        
        for xml_file in xml_files:
            try:
                print(f"📁 Parsing {xml_file.name}...")
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Debug: print root tag and some structure
                print(f"   Root tag: {root.tag}")
                if len(root) > 0:
                    print(f"   Child elements: {[child.tag for child in root[:5]]}")
                
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
                # Try generic parser as fallback
                try:
                    entities = self._parse_generic(root, str(xml_file.name))
                    all_entities.extend(entities)
                    print(f"   ⚠️  Fallback extracted {len(entities)} entities from {xml_file.name}")
                except Exception as fallback_e:
                    print(f"   ❌ Fallback also failed for {xml_file.name}: {fallback_e}")
                
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
        """Parse EU consolidated format with correct structure"""
        entities = []
        # EU uses default namespace - must be handled properly
        ns = {'eu': 'http://eu.europa.ec/fpi/fsd/export'}
        
        # First try with namespace prefix
        entity_elems = root.findall('.//eu:sanctionEntity', ns)
        
        # If no entities found with namespace, try without (for non-namespaced XML)
        if not entity_elems:
            entity_elems = root.findall('.//sanctionEntity')
        
        # If still no entities, iterate all children to find sanctionEntity tags
        if not entity_elems:
            for elem in root.iter():
                if elem.tag.endswith('}sanctionEntity') or elem.tag == 'sanctionEntity':
                    entity_elems.append(elem)
        
        for entity_elem in entity_elems:
            names = []
            country = None
            entity_type = 'unknown'
            
            # Find nameAlias elements - handle both namespaced and non-namespaced
            name_aliases = entity_elem.findall('.//eu:nameAlias', ns)
            if not name_aliases:
                name_aliases = entity_elem.findall('.//nameAlias')
            if not name_aliases:
                # Try iterating to find nameAlias tags
                for elem in entity_elem.iter():
                    if elem.tag.endswith('}nameAlias') or elem.tag == 'nameAlias':
                        name_aliases.append(elem)
            
            for name_alias in name_aliases:
                # EU format stores names in the wholeName ATTRIBUTE, not as element text
                whole_name = name_alias.get('wholeName')
                if whole_name and whole_name.strip():
                    name = whole_name.strip()
                    if not self._contains_illegal_content(name):
                        names.append(name)
            
            # Extract country from citizenship element
            citizenship_elems = entity_elem.findall('.//eu:citizenship', ns)
            if not citizenship_elems:
                for elem in entity_elem.iter():
                    if elem.tag.endswith('}citizenship') or elem.tag == 'citizenship':
                        citizenship_elems.append(elem)
            
            for citizenship_elem in citizenship_elems:
                country_desc = citizenship_elem.get('countryDescription')
                if country_desc:
                    country = country_desc.strip()
                    break
            
            # Extract subject type from subjectType element
            subject_elems = entity_elem.findall('.//eu:subjectType', ns)
            if not subject_elems:
                for elem in entity_elem.iter():
                    if elem.tag.endswith('}subjectType') or elem.tag == 'subjectType':
                        subject_elems.append(elem)
            
            for subject_elem in subject_elems:
                code = subject_elem.get('code', '').lower()
                if 'person' in code:
                    entity_type = 'individual'
                elif 'entity' in code or 'organisation' in code:
                    entity_type = 'entity'
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'EU',
                    'names': list(dict.fromkeys(names)),  # Remove duplicates while preserving order
                    'primary_name': names[0],
                    'country': country,
                    'type': entity_type
                })
        
        return entities

    def _parse_un_format(self, root, source: str) -> List[Dict[str, Any]]:
        """Parse UN consolidated list with correct Name6 structure"""
        entities = []
        
        for designation in root.findall('.//Designation'):
            names = []
            country = None
            
            # Extract names from Name6 elements
            for name_elem in designation.findall('.//Name6'):
                if name_elem.text and name_elem.text.strip():
                    name = name_elem.text.strip()
                    if not self._contains_illegal_content(name):
                        names.append(name)
            
            # Extract country from Country elements
            for country_elem in designation.findall('.//Country'):
                if country_elem.text:
                    country = country_elem.text.strip()
            
            # Determine type from IndividualEntityShip
            entity_type = 'unknown'
            for type_elem in designation.findall('.//IndividualEntityShip'):
                if type_elem.text:
                    type_text = type_elem.text.strip().lower()
                    if 'individual' in type_text:
                        entity_type = 'individual'
                    elif 'entity' in type_text:
                        entity_type = 'entity'
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'UN',
                    'names': names,
                    'primary_name': names[0],
                    'country': country,
                    'type': entity_type
                })
        
        return entities

    def _parse_ofac_format(self, root, source: str) -> List[Dict[str, Any]]:
        """Parse OFAC SDN Enhanced XML format"""
        entities = []
        ns = {'ofac': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML'}
        
        # Find entities container - try with namespace first
        entities_container = root.find('.//ofac:entities', ns)
        
        # If not found with namespace, try without or iterate to find
        if entities_container is None:
            entities_container = root.find('.//entities')
        
        if entities_container is None:
            # Try to find entities tag by iterating
            for elem in root.iter():
                if elem.tag.endswith('}entities') or elem.tag == 'entities':
                    entities_container = elem
                    break
        
        if entities_container is None:
            return entities
        
        # Find all entity elements
        entity_elems = entities_container.findall('.//ofac:entity', ns)
        if not entity_elems:
            entity_elems = entities_container.findall('.//entity')
        if not entity_elems:
            for elem in entities_container.iter():
                if elem.tag.endswith('}entity') or elem.tag == 'entity':
                    entity_elems.append(elem)
        
        for entity_elem in entity_elems:
            names = []
            country = None
            entity_type = 'unknown'
            
            # OFAC structure: entity > names > name > translations > translation > formattedFullName
            # Find name elements
            name_elems = []
            for elem in entity_elem.iter():
                if elem.tag.endswith('}name') or elem.tag == 'name':
                    name_elems.append(elem)
            
            for name_elem in name_elems:
                # Find translations > translation > formattedFullName
                for trans_elem in name_elem.iter():
                    if trans_elem.tag.endswith('}translation') or trans_elem.tag == 'translation':
                        # Look for formattedFullName
                        for child in trans_elem:
                            if child.tag.endswith('}formattedFullName') or child.tag == 'formattedFullName':
                                if child.text and child.text.strip():
                                    name = child.text.strip()
                                    if not self._contains_illegal_content(name):
                                        names.append(name)
            
            # Determine entity type from generalInfo > entityType
            for gen_info in entity_elem.iter():
                if gen_info.tag.endswith('}generalInfo') or gen_info.tag == 'generalInfo':
                    for child in gen_info:
                        if child.tag.endswith('}entityType') or child.tag == 'entityType':
                            if child.text:
                                type_text = child.text.strip().lower()
                                if 'individual' in type_text or 'person' in type_text:
                                    entity_type = 'individual'
                                elif 'entity' in type_text or 'organization' in type_text or 'business' in type_text:
                                    entity_type = 'entity'
            
            # Extract country from addresses
            for addr_elem in entity_elem.iter():
                if addr_elem.tag.endswith('}address') or addr_elem.tag == 'address':
                    for child in addr_elem:
                        if child.tag.endswith('}country') or child.tag == 'country':
                            if child.text:
                                country = child.text.strip()
                                break
                    if country:
                        break
            
            if names:
                entities.append({
                    'source': source,
                    'list_type': 'OFAC',
                    'names': list(dict.fromkeys(names)),  # Remove duplicates while preserving order
                    'primary_name': names[0],
                    'country': country,
                    'type': entity_type
                })
        
        return entities
    
    def _contains_illegal_content(self, text: str) -> bool:
        """Filter out potentially illegal or inappropriate content"""
        if not text:
            return True
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            return True
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        if re.search(url_pattern, text):
            return True
        
        # Social media handles
        social_pattern = r'@\w+'
        if re.search(social_pattern, text):
            return True
        
        # Script injection attempts
        script_patterns = [
            r'<script', r'javascript:', r'on\w+\s*=', r'eval\s*\(',
            r'exec\s*\(', r'__import__', r'function\s*\('
        ]
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Extremely short or long names (likely garbage)
        if len(text.strip()) < 2 or len(text.strip()) > 200:
            return True
        
        # Names that are just numbers or symbols
        if not any(c.isalpha() for c in text):
            return True
        
        return False
    
    def _parse_generic(self, root, source: str) -> List[Dict[str, Any]]:
        """Generic fallback parser - improved version"""
        entities = []
        
        # Look for elements that contain substantial text content
        for elem in root.iter():
            if elem.text and len(elem.text.strip()) > 2:
                text = elem.text.strip()
                
                # More permissive name detection
                if (len(text) >= 3 and len(text) <= 200 and  # Reasonable length
                    not text.startswith(('http', 'www.', '@')) and  # Not URLs/emails
                    not re.match(r'^\d+(\.\d+)*$', text) and  # Not version numbers
                    any(c.isalpha() for c in text)):  # Contains letters
                    
                    # Check if element tag suggests it's a name
                    tag_lower = elem.tag.lower()
                    if any(keyword in tag_lower for keyword in [
                        'name', 'title', 'entity', 'individual', 'person', 
                        'organization', 'company', 'designation', 'alias'
                    ]):
                        entities.append({
                            'source': source,
                            'list_type': 'Generic',
                            'names': [text],
                            'primary_name': text,
                            'type': 'unknown'
                        })
        
        # Also try to find structured data with attributes
        for elem in root.iter():
            if elem.attrib:
                name_attrs = ['name', 'title', 'entity', 'fullName', 'displayName']
                for attr in name_attrs:
                    if attr in elem.attrib and elem.attrib[attr].strip():
                        name = elem.attrib[attr].strip()
                        if len(name) >= 3 and len(name) <= 200:
                            entities.append({
                                'source': source,
                                'list_type': 'Generic',
                                'names': [name],
                                'primary_name': name,
                                'type': 'unknown'
                            })
        
        return entities
    
    def _get_text(self, parent, xpath: str, namespaces=None) -> Optional[str]:
        """Extract text from XML element"""
        try:
            elem = parent.find(xpath, namespaces)
            return elem.text.strip() if elem is not None and elem.text else None
        except:
            return None


class OptimalFuzzyMatcher:
    """Optimized fuzzy matching for sanctions screening"""
    
    def __init__(self, sanctions_entities: List[Dict[str, Any]]):
        self.sanctions_entities = sanctions_entities
        self.name_index = []
        self._build_index()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for better matching"""
        if not name:
            return ""
        
        # Convert to lowercase, remove extra spaces, normalize unicode
        normalized = re.sub(r'\s+', ' ', name.lower().strip())
        return normalized
    
    def _tokenize(self, name: str) -> List[str]:
        """Tokenize name into words"""
        return [token for token in re.split(r'\s+', name) if token]
    
    def _build_index(self):
        """Build optimized search index"""
        for entity in self.sanctions_entities:
            for name in entity.get('names', []):
                normalized = self._normalize_name(name)
                tokens = self._tokenize(normalized)
                
                self.name_index.append({
                    'normalized': normalized,
                    'tokens': tokens,
                    'entity': entity,
                    'original_name': name
                })
    
    def _layer1_exact_match(self, query: str, target: str) -> Optional[float]:
        """Exact match layer"""
        if query == target:
            return 100.0
        return None
    
    def _layer2_token_match(self, query_tokens: List[str], target_tokens: List[str]) -> Optional[float]:
        """Token-based matching"""
        if not query_tokens or not target_tokens:
            return None
        
        # Check for complete token overlap
        query_set = set(query_tokens)
        target_set = set(target_tokens)
        
        intersection = query_set.intersection(target_set)
        union = query_set.union(target_set)
        
        if len(intersection) == len(query_set):  # All query tokens found
            return 95.0
        
        # Partial overlap scoring
        if len(intersection) >= 2:
            ratio = len(intersection) / len(union)
            return min(90.0, ratio * 100)
        
        return None
    
    def _layer3_phonetic_match(self, query: str, query_tokens: List[str], 
                              target: str, target_tokens: List[str]) -> Optional[float]:
        """Phonetic matching using soundex-like logic"""
        # Simple phonetic matching - first letters of words
        if len(query_tokens) >= 2 and len(target_tokens) >= 2:
            query_initials = ''.join(word[0] for word in query_tokens if word)
            target_initials = ''.join(word[0] for word in target_tokens if word)
            
            if query_initials == target_initials and len(query_initials) >= 3:
                return 85.0
        
        return None
    
    def _layer4_fuzzy_match(self, query: str, target: str) -> Optional[float]:
        """Final fuzzy matching layer"""
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            return None
        
        # Use fuzzy matching as final fallback
        score = max(
            fuzz.token_sort_ratio(query, target),
            fuzz.token_set_ratio(query, target)
        )
        
        return score if score >= 70 else None
    
    def match_entity(self, search_name: str, entity_type: str = None, threshold: int = 70) -> List[Dict[str, Any]]:
        """Find matches for a given name"""
        
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

def screen_entity(name: str, entity_type: str = None, threshold: int = 70):
    """Screen a single entity against sanctions"""
    if not fuzzy_matcher:
        return []
    
    return fuzzy_matcher.match_entity(name, entity_type, threshold)

def reload_sanctions_data():
    """Force reload sanctions data"""
    global sanctions_service, fuzzy_matcher
    sanctions_service = SanctionsService()
    fuzzy_matcher = OptimalFuzzyMatcher(sanctions_service.sanctions_entities)
    
    # Also reload the enhanced matcher
    try:
        from app.enhanced_matcher import reload_matcher
        reload_matcher()
    except ImportError:
        pass  # Enhanced matcher not available
    
    return f"Reloaded {len(sanctions_service.sanctions_entities)} entities"
