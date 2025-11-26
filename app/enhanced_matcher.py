"""
Enhanced Multi-Layered Sanctions Matcher

Implements a 4-layer matching hierarchy:
1. Exact Match (100%) - Direct string comparison after normalization
2. Token-Based Matching (85% threshold) - Token overlap percentage
3. Phonetic Matching (75% threshold) - Handles abbreviations, transliterations
4. Fuzzy String Matching (70% threshold) - Token set ratio fallback
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from fuzzywuzzy import fuzz
from unidecode import unidecode

logger = logging.getLogger(__name__)


# Common abbreviation mappings for business entities
ABBREVIATION_MAPPINGS = {
    'jsc': ['joint stock company', 'joint-stock company'],
    'llc': ['limited liability company'],
    'ltd': ['limited'],
    'inc': ['incorporated'],
    'corp': ['corporation'],
    'plc': ['public limited company'],
    'gmbh': ['gesellschaft mit beschrankter haftung'],
    'ag': ['aktiengesellschaft'],
    'sa': ['sociedad anonima', 'societe anonyme'],
    'nv': ['naamloze vennootschap'],
    'bv': ['besloten vennootschap'],
    'ooo': ['obshestvo s ogranichennoy otvetstvennostyu'],  # Russian LLC
    'oao': ['otkrytoe aktsionernoe obshestvo'],  # Russian OJSC
    'zao': ['zakrytoe aktsionernoe obshestvo'],  # Russian CJSC
    'pjsc': ['public joint stock company'],
    'cjsc': ['closed joint stock company'],
    'ojsc': ['open joint stock company'],
    'co': ['company'],
    'intl': ['international'],
    'svcs': ['services'],
    'mfg': ['manufacturing'],
    'grp': ['group', 'gruppa'],
    'el': ['electronic', 'electronics', 'electrical'],
}


class EnhancedSanctionsMatcher:
    """
    Multi-layered fuzzy matching service for sanctions screening.
    
    Uses 4 layers of matching with decreasing confidence:
    - Layer 1: Exact match (score 100)
    - Layer 2: Token-based matching (score 85-99)
    - Layer 3: Phonetic/abbreviation matching (score 75-84)
    - Layer 4: Fuzzy string matching (score 70-74)
    """
    
    def __init__(self, sanctions_entities: List[Dict[str, Any]]):
        self.sanctions_entities = sanctions_entities
        self.name_index = []
        self._build_index()
    
    def _build_index(self):
        """Build searchable index of all names from sanctions entities."""
        for entity in self.sanctions_entities:
            names = entity.get('names', [])
            primary_name = entity.get('primary_name', '')
            
            # Add primary name
            if primary_name and len(primary_name.strip()) > 1:
                normalized = self._normalize_name(primary_name)
                tokens = self._tokenize(normalized)
                self.name_index.append({
                    'original_name': primary_name,
                    'normalized': normalized,
                    'tokens': tokens,
                    'entity': entity
                })
            
            # Add all aliases/alternate names
            for name in names:
                if name and name != primary_name and len(name.strip()) > 1:
                    normalized = self._normalize_name(name)
                    tokens = self._tokenize(normalized)
                    self.name_index.append({
                        'original_name': name,
                        'normalized': normalized,
                        'tokens': tokens,
                        'entity': entity
                    })
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name for matching.
        - Convert to lowercase
        - Remove accents (transliterate)
        - Remove punctuation
        - Normalize whitespace
        """
        if not name:
            return ""
        
        # Convert to lowercase and strip
        name = str(name).lower().strip()
        
        # Transliterate non-ASCII characters
        name = unidecode(name)
        
        # Remove punctuation but keep spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Normalize whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def _tokenize(self, name: str) -> set:
        """
        Tokenize a normalized name into a set of words.
        Expands abbreviations for better matching.
        """
        if not name:
            return set()
        
        words = name.split()
        tokens = set()
        
        for word in words:
            # Skip very short words (articles, etc.)
            if len(word) <= 1:
                continue
            
            tokens.add(word)
            
            # Add expanded abbreviations
            if word in ABBREVIATION_MAPPINGS:
                for expansion in ABBREVIATION_MAPPINGS[word]:
                    for exp_word in expansion.split():
                        tokens.add(exp_word)
        
        return tokens
    
    def _layer1_exact_match(self, query_normalized: str, target_normalized: str) -> Optional[float]:
        """
        Layer 1: Exact match after normalization.
        Returns 100.0 if exact match, None otherwise.
        """
        if query_normalized == target_normalized and query_normalized:
            return 100.0
        return None
    
    def _layer2_token_match(self, query_tokens: set, target_tokens: set) -> Optional[float]:
        """
        Layer 2: Token-based matching.
        All query tokens must be present in target.
        Returns score 85-99 based on overlap, None if threshold not met.
        """
        if not query_tokens or not target_tokens:
            return None
        
        # How many query tokens are in target?
        matching_tokens = query_tokens & target_tokens
        
        if not matching_tokens:
            return None
        
        # Calculate match percentage based on query tokens
        query_match_ratio = len(matching_tokens) / len(query_tokens)
        
        # Also consider how much of target is covered
        target_match_ratio = len(matching_tokens) / len(target_tokens)
        
        # Combined score - query match is weighted more heavily
        combined_ratio = (query_match_ratio * 0.7) + (target_match_ratio * 0.3)
        
        # Score range: 85-99
        if combined_ratio >= 0.85:
            # Scale from 85-99 based on ratio
            score = 85 + (combined_ratio - 0.85) * (14 / 0.15)
            return min(99.0, score)
        
        return None
    
    def _layer3_phonetic_match(self, query_normalized: str, query_tokens: set,
                                target_normalized: str, target_tokens: set) -> Optional[float]:
        """
        Layer 3: Phonetic and abbreviation matching.
        Handles transliterations, abbreviations, and phonetically similar names.
        Returns score 75-84, None if threshold not met.
        """
        # Check for partial token matches with abbreviation expansion
        query_expanded = self._expand_abbreviations(query_normalized)
        target_expanded = self._expand_abbreviations(target_normalized)
        
        # Use token_sort_ratio which is good for reordered words
        score = fuzz.token_sort_ratio(query_expanded, target_expanded)
        
        if score >= 75:
            # Scale to 75-84 range
            scaled_score = 75 + ((score - 75) * (9 / 25))
            return min(84.0, scaled_score)
        
        return None
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations in text."""
        words = text.split()
        expanded = []
        
        for word in words:
            if word in ABBREVIATION_MAPPINGS:
                # Use first expansion
                expanded.append(ABBREVIATION_MAPPINGS[word][0])
            else:
                expanded.append(word)
        
        return ' '.join(expanded)
    
    def _layer4_fuzzy_match(self, query_normalized: str, target_normalized: str) -> Optional[float]:
        """
        Layer 4: Fuzzy string matching using token_set_ratio.
        Returns score 70-74, None if threshold not met.
        """
        # token_set_ratio is good for subsets and different orderings
        score = fuzz.token_set_ratio(query_normalized, target_normalized)
        
        if score >= 70:
            # Scale to 70-74 range
            scaled_score = 70 + ((score - 70) * (4 / 30))
            return min(74.0, max(70.0, scaled_score))
        
        return None
    
    def find_matches(self, query: str, threshold: int = 70) -> List[Dict[str, Any]]:
        """
        Find all matches for a query using the 4-layer matching hierarchy.
        
        Args:
            query: The name to search for
            threshold: Minimum score threshold (default 70)
        
        Returns:
            List of matches sorted by score (highest first)
        """
        if not query or not query.strip():
            return []
        
        query_normalized = self._normalize_name(query)
        query_tokens = self._tokenize(query_normalized)
        
        # Collect all matches first, then deduplicate keeping best score
        all_matches = []
        
        for entry in self.name_index:
            target_normalized = entry['normalized']
            target_tokens = entry['tokens']
            entity = entry['entity']
            original_name = entry['original_name']
            
            # Try layers in order of decreasing confidence
            score = None
            match_layer = None
            
            # Layer 1: Exact match
            score = self._layer1_exact_match(query_normalized, target_normalized)
            if score is not None:
                match_layer = 'exact'
            
            # Layer 2: Token match
            if score is None:
                score = self._layer2_token_match(query_tokens, target_tokens)
                if score is not None:
                    match_layer = 'token'
            
            # Layer 3: Phonetic match
            if score is None:
                score = self._layer3_phonetic_match(
                    query_normalized, query_tokens,
                    target_normalized, target_tokens
                )
                if score is not None:
                    match_layer = 'phonetic'
            
            # Layer 4: Fuzzy match
            if score is None:
                score = self._layer4_fuzzy_match(query_normalized, target_normalized)
                if score is not None:
                    match_layer = 'fuzzy'
            
            # Add to all matches if score meets threshold
            if score is not None and score >= threshold:
                all_matches.append({
                    'matched_name': original_name,
                    'score': round(score, 1),
                    'match_layer': match_layer,
                    'entity_id': id(entity),
                    'entity': {
                        'source': entity.get('source', 'Unknown'),
                        'list_type': entity.get('list_type', 'Unknown'),
                        'type': entity.get('type', 'unknown'),
                        'primary_name': entity.get('primary_name', original_name)
                    }
                })
        
        # Sort all matches by score (highest first)
        all_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Deduplicate: keep only the highest-scoring match per entity
        seen_entities = set()
        matches = []
        
        for match in all_matches:
            entity_id = match['entity_id']
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                # Remove entity_id from output (internal use only)
                del match['entity_id']
                matches.append(match)
        
        return matches


# Global matcher instance
_matcher_instance = None


def get_matcher_instance() -> EnhancedSanctionsMatcher:
    """Get or create the global matcher instance."""
    global _matcher_instance
    
    if _matcher_instance is None:
        # Initialize from sanctions service
        from app.sanctions_service import sanctions_service, init_sanctions_service
        
        if sanctions_service is None:
            init_sanctions_service()
        
        # Re-import to get the updated reference after initialization
        from app.sanctions_service import sanctions_service
        _matcher_instance = EnhancedSanctionsMatcher(sanctions_service.sanctions_entities)
    
    return _matcher_instance


def reload_matcher():
    """Force reload of the matcher with fresh sanctions data."""
    global _matcher_instance
    _matcher_instance = None
    return get_matcher_instance()
