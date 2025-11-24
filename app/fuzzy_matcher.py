import pandas as pd
from fuzzywuzzy import fuzz, process
import re
from typing import List, Dict, Any, Tuple
import logging
from unidecode import unidecode

logger = logging.getLogger(__name__)

class AdvancedFuzzyMatcher:
    def __init__(self, sanctions_data: List[Dict[str, Any]]):
        self.sanctions_data = sanctions_data
        self.preprocessed_names = self._preprocess_names()
        
    def _preprocess_names(self) -> List[Tuple[str, Dict]]:
        """Preprocess all sanction list names for efficient matching"""
        processed = []
        
        for entity in self.sanctions_data:
            name = entity.get('name')
            if name and pd.notna(name):
                # Store both original and preprocessed
                processed.append((self._normalize_name(name), entity))
                
        return processed
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for better matching"""
        if not name or pd.isna(name):
            return ""
            
        # Convert to lowercase
        name = name.lower()
        
        # Remove accents and special characters
        name = unidecode(name)
        
        # Remove common company suffixes
        suffixes = ['ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation', 
                   'llc', 'gmbh', 'sa', 'nv', 'plc', 'co', 'company']
        
        for suffix in suffixes:
            name = re.sub(r'\b' + re.escape(suffix) + r'\b', '', name)
        
        # Remove extra spaces and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common words that don't help matching
        common_words = ['the', 'and', 'of', 'for', 'with', 'from', 'to']
        words = name.split()
        words = [w for w in words if w not in common_words and len(w) > 1]
        
        return ' '.join(words)
    
    def match_entity(self, search_name: str, threshold: int = 80) -> List[Dict[str, Any]]:
        """Match a search name against sanctions list"""
        if not search_name or pd.isna(search_name):
            return []
            
        normalized_search = self._normalize_name(search_name)
        
        matches = []
        
        for normalized_db_name, entity in self.preprocessed_names:
            # Use multiple matching strategies
            ratio = fuzz.token_sort_ratio(normalized_search, normalized_db_name)
            partial_ratio = fuzz.partial_ratio(normalized_search, normalized_db_name)
            
            # Weighted score (token sort ratio is generally more reliable)
            weighted_score = (ratio * 0.7) + (partial_ratio * 0.3)
            
            if weighted_score >= threshold:
                matches.append({
                    'entity': entity,
                    'score': weighted_score,
                    'match_details': {
                        'token_sort_ratio': ratio,
                        'partial_ratio': partial_ratio,
                        'search_name': search_name,
                        'matched_name': entity.get('name'),
                        'normalized_search': normalized_search,
                        'normalized_match': normalized_db_name
                    }
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def batch_match(self, entities: List[str], threshold: int = 80) -> Dict[str, List]:
        """Match multiple entities at once"""
        results = {}
        
        for entity in entities:
            matches = self.match_entity(entity, threshold)
            if matches:
                results[entity] = matches
                
        return results

class EnhancedFuzzyMatcher(AdvancedFuzzyMatcher):
    """Enhanced matcher with additional strategies"""
    
    def __init__(self, sanctions_data: List[Dict[str, Any]]):
        super().__init__(sanctions_data)
        self._build_name_variations()
    
    def _build_name_variations(self):
        """Build common name variations for better matching"""
        self.name_variations = []
        
        for normalized, entity in self.preprocessed_names:
            original_name = entity.get('name', '')
            if original_name:
                # Add original name variations
                variations = self._generate_variations(original_name)
                for var in variations:
                    self.name_variations.append((self._normalize_name(var), entity))
    
    def _generate_variations(self, name: str) -> List[str]:
        """Generate common name variations"""
        variations = [name]
        
        # Remove punctuation variations
        variations.append(re.sub(r'[^\w\s]', ' ', name))
        
        # Common acronym patterns
        words = name.split()
        if len(words) > 1:
            # Last word first (common in some naming conventions)
            variations.append(f"{words[-1]} {''.join(words[:-1])}")
            
        return variations
    
    def match_entity_enhanced(self, search_name: str, threshold: int = 75) -> List[Dict[str, Any]]:
        """Enhanced matching with name variations"""
        base_matches = super().match_entity(search_name, threshold)
        
        # Also check against name variations
        normalized_search = self._normalize_name(search_name)
        variation_matches = []
        
        for normalized_var, entity in self.name_variations:
            ratio = fuzz.token_sort_ratio(normalized_search, normalized_var)
            if ratio >= threshold:
                variation_matches.append({
                    'entity': entity,
                    'score': ratio,
                    'match_type': 'variation',
                    'match_details': {
                        'ratio': ratio,
                        'search_name': search_name,
                        'matched_variation': normalized_var,
                        'original_name': entity.get('name')
                    }
                })
        
        # Combine and deduplicate matches
        all_matches = base_matches + variation_matches
        seen_entities = set()
        unique_matches = []
        
        for match in all_matches:
            entity_id = id(match['entity'])
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                unique_matches.append(match)
        
        unique_matches.sort(key=lambda x: x['score'], reverse=True)
        return unique_matches
