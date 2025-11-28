"""
Enhanced Multi-Layered Sanctions Matcher

Implements a 4-layer matching hierarchy:
1. Exact Match (100%) - Direct string comparison after normalization
2. Token-Based Matching (85% threshold) - Token overlap percentage
3. Phonetic Matching (75% threshold) - Handles abbreviations, transliterations
4. Fuzzy String Matching (70% threshold) - Token set ratio fallback

Includes tiered risk scoring based on sanctioning authority:
- Tier 1 (Multilateral Mandate): UN/UNSC - Highest legal legitimacy
- Tier 2 (Key Ally Jurisdiction): OFAC/US, UK, EU - High risk
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from fuzzywuzzy import fuzz
from unidecode import unidecode

logger = logging.getLogger(__name__)


# Risk tier definitions based on sanctioning authority
# Tier 1: Multilateral Mandate (highest legal legitimacy)
# Tier 2: Key Ally Jurisdiction (high risk due to secondary sanctions and global financial exposure)
RISK_TIERS = {
    'UN': {'tier': 1, 'tier_name': 'Tier 1 - Multilateral Mandate', 'weight': 1.0, 'authority': 'United Nations Security Council'},
    'UNSC': {'tier': 1, 'tier_name': 'Tier 1 - Multilateral Mandate', 'weight': 1.0, 'authority': 'United Nations Security Council'},
    'OFAC': {'tier': 2, 'tier_name': 'Tier 2 - Key Ally Jurisdiction', 'weight': 0.9, 'authority': 'OFAC/US Treasury'},
    'US': {'tier': 2, 'tier_name': 'Tier 2 - Key Ally Jurisdiction', 'weight': 0.9, 'authority': 'OFAC/US Treasury'},
    'UK': {'tier': 2, 'tier_name': 'Tier 2 - Key Ally Jurisdiction', 'weight': 0.85, 'authority': 'UK HM Treasury'},
    'EU': {'tier': 2, 'tier_name': 'Tier 2 - Key Ally Jurisdiction', 'weight': 0.85, 'authority': 'European Union'},
}

# Default for unknown sources
DEFAULT_RISK_TIER = {'tier': 3, 'tier_name': 'Tier 3 - Other', 'weight': 0.7, 'authority': 'Other Authority'}


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
    
    def _get_risk_tier(self, list_type: str) -> Dict[str, Any]:
        """
        Get the risk tier information for a given sanctions list type.
        
        Args:
            list_type: The type of sanctions list (UN, OFAC, UK, EU, etc.)
        
        Returns:
            Dictionary with tier information including tier number, name, weight, and authority
        """
        list_type_upper = list_type.upper() if list_type else ''
        return RISK_TIERS.get(list_type_upper, DEFAULT_RISK_TIER)
    
    def _calculate_risk_score(self, match_score: float, list_types: List[str]) -> Dict[str, Any]:
        """
        Calculate the overall risk score based on match score and sanctioning authorities.
        
        Multi-jurisdictional matches are weighted more heavily:
        - Multiple Tier 1 (UN) matches: Highest risk
        - Mix of Tier 1 + Tier 2: Very high risk
        - Multiple Tier 2 matches: High risk
        - Single jurisdiction: Standard risk for that tier
        
        Args:
            match_score: The fuzzy match score (0-100)
            list_types: List of sanctions list types where the match was found
        
        Returns:
            Dictionary with risk score details
        """
        if not list_types:
            # When list_types is empty, we cannot determine multi-jurisdictional status
            # Return None to indicate this status is unknown
            return {
                'risk_score': match_score,
                'risk_level': 'Unknown',
                'authorities': [],
                'tier': 3,
                'is_multi_jurisdictional': None  # None indicates unknown status
            }
        
        # Get unique list types
        unique_lists = list(set(lt.upper() for lt in list_types if lt))
        
        # Get tier info for each list
        tier_info = [self._get_risk_tier(lt) for lt in unique_lists]
        
        # Check for multi-jurisdictional (more than one authority)
        is_multi_jurisdictional = len(unique_lists) > 1
        
        # Calculate weighted score based on tiers
        # Base score starts with the match score
        weighted_score = match_score
        
        # Find the highest tier (lowest number = highest risk)
        highest_tier = min(ti['tier'] for ti in tier_info)
        
        # Apply multiplier for multi-jurisdictional matches
        if is_multi_jurisdictional:
            # Count how many different tiers are involved
            tiers_involved = set(ti['tier'] for ti in tier_info)
            
            if 1 in tiers_involved and len(tiers_involved) > 1:
                # Mix of UN + other jurisdictions: Very high risk multiplier
                weighted_score = min(100, weighted_score * 1.25)
            elif 1 in tiers_involved:
                # Multiple UN sources
                weighted_score = min(100, weighted_score * 1.20)
            else:
                # Multiple Tier 2 jurisdictions (e.g., US + UK + EU)
                weighted_score = min(100, weighted_score * 1.15)
        
        # Determine risk level based on weighted score and tier
        if weighted_score >= 90 and highest_tier == 1:
            risk_level = 'Critical'
        elif weighted_score >= 85 or (weighted_score >= 80 and highest_tier == 1):
            risk_level = 'Very High'
        elif weighted_score >= 75 or is_multi_jurisdictional:
            risk_level = 'High'
        elif weighted_score >= 70:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        # Build authorities list
        authorities = [ti['authority'] for ti in tier_info]
        
        return {
            'risk_score': round(weighted_score, 1),
            'risk_level': risk_level,
            'authorities': authorities,
            'sanctioning_authorities': ', '.join(unique_lists),
            'tier': highest_tier,
            'tier_name': RISK_TIERS.get(unique_lists[0], DEFAULT_RISK_TIER)['tier_name'] if unique_lists else DEFAULT_RISK_TIER['tier_name'],
            'is_multi_jurisdictional': is_multi_jurisdictional
        }

    def find_matches(self, query: str, threshold: int = 70) -> List[Dict[str, Any]]:
        """
        Find all matches for a query using the 4-layer matching hierarchy.
        
        Args:
            query: The name to search for
            threshold: Minimum score threshold (default 70)
        
        Returns:
            List of matches sorted by risk score (highest first), including:
            - matched_name: The name that matched
            - score: The fuzzy match score
            - match_layer: Which matching layer found the match
            - entity: Entity details including source and type
            - sanctioning_authority: The sanctions list where the match was found
            - risk_tier: Risk tier information (Tier 1/2/3)
            - risk_score: Weighted risk score considering jurisdictions
        """
        if not query or not query.strip():
            return []
        
        query_normalized = self._normalize_name(query)
        query_tokens = self._tokenize(query_normalized)
        
        # Collect all matches first, grouped by matched name to detect multi-jurisdictional
        all_matches = []
        name_to_lists = {}  # Track which lists each name appears on
        
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
                list_type = entity.get('list_type', 'Unknown')
                primary_name = entity.get('primary_name', original_name)
                
                # Track which lists this name appears on (for multi-jurisdictional detection)
                normalized_primary = self._normalize_name(primary_name)
                if normalized_primary not in name_to_lists:
                    name_to_lists[normalized_primary] = set()
                name_to_lists[normalized_primary].add(list_type)
                
                # Get risk tier for this list
                risk_tier_info = self._get_risk_tier(list_type)
                
                all_matches.append({
                    'matched_name': original_name,
                    'score': round(score, 1),
                    'match_layer': match_layer,
                    'entity_id': id(entity),
                    'normalized_primary': normalized_primary,
                    'entity': {
                        'source': entity.get('source', 'Unknown'),
                        'list_type': list_type,
                        'type': entity.get('type', 'unknown'),
                        'primary_name': primary_name
                    },
                    'sanctioning_authority': risk_tier_info['authority'],
                    'risk_tier': risk_tier_info['tier'],
                    'risk_tier_name': risk_tier_info['tier_name']
                })
        
        # Deduplicate: keep only the highest-scoring match per entity
        # But also calculate multi-jurisdictional risk scores
        seen_entities = set()
        matches = []
        
        for match in all_matches:
            entity_id = match['entity_id']
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                
                # Get all lists this name appears on
                normalized_primary = match['normalized_primary']
                all_lists = list(name_to_lists.get(normalized_primary, {match['entity']['list_type']}))
                
                # Calculate risk score with multi-jurisdictional weighting
                risk_info = self._calculate_risk_score(match['score'], all_lists)
                
                # Build the final match result
                result = {
                    'matched_name': match['matched_name'],
                    'score': match['score'],
                    'match_layer': match['match_layer'],
                    'entity': match['entity'],
                    'sanctioning_authority': match['sanctioning_authority'],
                    'risk_tier': match['risk_tier'],
                    'risk_tier_name': match['risk_tier_name'],
                    'risk_score': risk_info['risk_score'],
                    'risk_level': risk_info['risk_level'],
                    'is_multi_jurisdictional': risk_info['is_multi_jurisdictional'],
                    'all_sanctioning_authorities': risk_info.get('sanctioning_authorities', match['entity']['list_type'])
                }
                
                matches.append(result)
        
        # Sort by risk score (highest first), then by match score
        matches.sort(key=lambda x: (x['risk_score'], x['score']), reverse=True)
        
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
