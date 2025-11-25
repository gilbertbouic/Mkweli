"""
Advanced Fuzzy Matching for Sanctions Screening
"""
from thefuzz import fuzz, process as thefuzz_process
import re
from typing import List, Dict, Any

class OptimalFuzzyMatcher:
    def __init__(self, sanctions_data: List[Dict]):
        self.sanctions_data = sanctions_data
        # Use primary_name as the main name field
        self.name_key = 'primary_name'
        
        if sanctions_data:
            # Filter out garbage entities during initialization
            self.clean_entities = self._filter_garbage_entities(sanctions_data)
            self.names = [entity[self.name_key].lower().strip() 
                         for entity in self.clean_entities 
                         if entity.get(self.name_key)]
            print(f"✅ Cleaned {len(self.clean_entities)} entities (removed {len(sanctions_data) - len(self.clean_entities)} garbage entries)")
        else:
            self.clean_entities = []
            self.names = []
    
    def _filter_garbage_entities(self, entities: List[Dict]) -> List[Dict]:
        """Filter out garbage entities that are parsing artifacts"""
        clean_entities = []
        
        # Common garbage patterns to exclude
        garbage_patterns = [
            r'^[A-Za-z]$',  # Single letters
            r'^[0-9]$',     # Single digits
            r'^\W+$',       # Only symbols
            r'^.{1,2}$',    # 1-2 character strings
        ]
        
        # Common stop words and garbage terms
        garbage_terms = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'as', 'is', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'it', 'its', 'they', 'them',
            'their', 'this', 'that', 'these', 'those', 'from', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out',
            'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
        
        for entity in entities:
            primary_name = entity.get(self.name_key, '')
            
            # Skip if no name
            if not primary_name or not primary_name.strip():
                continue
            
            name_clean = primary_name.strip()
            
            # Skip if it matches garbage patterns
            is_garbage = False
            for pattern in garbage_patterns:
                if re.match(pattern, name_clean):
                    is_garbage = True
                    break
            
            # Skip common stop words
            if name_clean.lower() in garbage_terms:
                is_garbage = True
            
            # Skip names that are too short and not meaningful
            if len(name_clean) <= 2:
                is_garbage = True
            
            # Skip names that are mostly symbols or numbers
            symbol_count = sum(1 for char in name_clean if not char.isalnum() and not char.isspace())
            if symbol_count > len(name_clean) * 0.5:  # More than 50% symbols
                is_garbage = True
            
            # Skip very long text that's likely descriptive paragraphs
            if len(name_clean) > 100:
                is_garbage = True
            
            # Skip text that contains multiple sentences or paragraph markers
            if re.search(r'[.!?]\s+[A-Z]', name_clean):  # Multiple sentences
                is_garbage = True
            
            # Skip text that looks like addresses or descriptions
            descriptive_indicators = [
                'principal place of business',
                'place of registration', 
                'associated individual',
                'photo available',
                'date of birth',
                'passport number',
                'address:',
                'tel:',
                'fax:',
                'email:'
            ]
            
            if any(indicator in name_clean.lower() for indicator in descriptive_indicators):
                is_garbage = True
            
            if not is_garbage:
                clean_entities.append(entity)
        
        return clean_entities
    
    def find_matches(self, name: str, threshold: int = 75, limit: int = 10) -> List[Dict]:
        """Find fuzzy matches with multiple matching strategies"""
        if not name or not name.strip() or not self.names:
            return []
        
        name_clean = name.lower().strip()
        all_matches = []
        
        # Strategy 1: Direct fuzzy matching
        try:
            direct_matches = thefuzz_process.extract(name_clean, self.names, limit=limit*2, scorer=fuzz.token_sort_ratio)
            all_matches.extend(direct_matches)
        except Exception as e:
            print(f"⚠️ Direct matching error: {e}")
        
        # Strategy 2: Partial matching for substrings
        try:
            partial_matches = thefuzz_process.extract(name_clean, self.names, limit=limit, scorer=fuzz.partial_ratio)
            all_matches.extend(partial_matches)
        except Exception as e:
            print(f"⚠️ Partial matching error: {e}")
        
        # Strategy 3: Token set ratio (order independent)
        try:
            token_matches = thefuzz_process.extract(name_clean, self.names, limit=limit, scorer=fuzz.token_set_ratio)
            all_matches.extend(token_matches)
        except Exception as e:
            print(f"⚠️ Token matching error: {e}")
        
        # Remove duplicates and filter by threshold
        unique_matches = {}
        for match_name, score in all_matches:
            if (score >= threshold and 
                match_name not in unique_matches and
                len(match_name) > 2):  # Additional length filter
                unique_matches[match_name] = score
        
        # Convert to result format
        results = []
        for match_name, score in unique_matches.items():
            # Find the original entity data
            original_entity = next(
                (entity for entity in self.clean_entities 
                 if entity.get(self.name_key, '').lower().strip() == match_name),
                None
            )
            
            if original_entity:
                results.append({
                    'name': original_entity.get(self.name_key, 'Unknown'),
                    'primary_name': original_entity.get(self.name_key, 'Unknown'),
                    'score': score,
                    'source': original_entity.get('source', 'Unknown'),
                    'type': original_entity.get('type', 'Entity'),
                    'countries': original_entity.get('countries', []),
                    'id': original_entity.get('id', ''),
                    'list_type': original_entity.get('list_type', '')
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_matching_stats(self):
        """Get statistics about the matching system"""
        return {
            'total_entities': len(self.sanctions_data),
            'clean_entities': len(self.clean_entities),
            'garbage_removed': len(self.sanctions_data) - len(self.clean_entities),
            'unique_names': len(self.names),
            'matching_strategies': ['token_sort_ratio', 'partial_ratio', 'token_set_ratio']
        }
