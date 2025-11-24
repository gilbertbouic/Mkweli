import pandas as pd
from fuzzywuzzy import fuzz, process
from thefuzz import process as thefuzz_process
import re
from typing import List, Dict, Any, Tuple, Optional
import logging
from unidecode import unidecode
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class OptimalFuzzyMatcher:
    """
    Optimal fuzzy matching for sanctions screening with multiple strategies
    and configurable thresholds for different use cases
    """
    
    def __init__(self, sanctions_data: List[Dict[str, Any]]):
        self.sanctions_data = sanctions_data
        self.name_index = self._build_name_index()
        self.entity_groups = self._group_entities()
        
    def _build_name_index(self) -> List[Tuple[str, Dict]]:
        """Build index of all names for efficient matching"""
        index = []
        
        for entity in self.sanctions_data:
            for name in entity.get('names', []):
                if name and pd.notna(name):
                    normalized = self._normalize_name(name)
                    if normalized:  # Only add if normalization produces result
                        index.append((normalized, {
                            'original_name': name,
                            'entity': entity,
                            'source': entity.get('source'),
                            'list_type': entity.get('list_type')
                        }))
        
        logger.info(f"Built index with {len(index)} normalized names")
        return index
    
    def _group_entities(self) -> Dict[str, List]:
        """Group entities by their primary identifier"""
        groups = defaultdict(list)
        for entity in self.sanctions_data:
            primary_name = entity.get('primary_name')
            if primary_name:
                groups[primary_name].append(entity)
        return groups
    
    def _normalize_name(self, name: str) -> str:
        """Advanced name normalization for optimal matching"""
        if not name or pd.isna(name):
            return ""
            
        # Basic cleaning
        name = str(name).lower().strip()
        
        # Remove accents and special characters
        name = unidecode(name)
        
        # Remove common legal entities and suffixes with word boundaries
        legal_entities = [
            'ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation',
            'llc', 'gmbh', 'sa', 'nv', 'plc', 'co', 'company', 'group',
            'holding', 'enterprises', 'international', 'global'
        ]
        
        for entity in legal_entities:
            # Use word boundaries to avoid removing parts of words
            name = re.sub(r'\b' + re.escape(entity) + r'\b', '', name)
        
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common stop words that don't help matching
        stop_words = {'the', 'and', 'of', 'for', 'with', 'from', 'to', 'in', 'a', 'an'}
        words = [w for w in name.split() if w not in stop_words and len(w) > 1]
        
        # Sort words for consistent token order (improves token-based matching)
        words_sorted = sorted(words)
        
        return ' '.join(words_sorted)
    
    def match_single_name(self, 
                         search_name: str, 
                         threshold: int = 85,
                         strategy: str = 'optimal') -> List[Dict[str, Any]]:
        """
        Match a single name against sanctions list
        
        Args:
            search_name: Name to search for
            threshold: Minimum match score (0-100)
            strategy: 'optimal', 'strict', 'lenient', or 'company'
        """
        if not search_name or pd.isna(search_name):
            return []
            
        # Apply strategy-specific settings
        threshold, algorithms = self._get_strategy_config(strategy, threshold)
        normalized_search = self._normalize_name(search_name)
        
        if not normalized_search:
            return []
        
        matches = []
        seen_entities = set()
        
        for normalized_db_name, name_info in self.name_index:
            scores = self._calculate_match_scores(normalized_search, normalized_db_name, algorithms)
            weighted_score = self._calculate_weighted_score(scores, strategy)
            
            if weighted_score >= threshold:
                entity_id = id(name_info['entity'])
                if entity_id not in seen_entities:
                    seen_entities.add(entity_id)
                    
                    match_info = {
                        'entity': name_info['entity'],
                        'score': weighted_score,
                        'matched_name': name_info['original_name'],
                        'search_name': search_name,
                        'normalized_search': normalized_search,
                        'strategy': strategy,
                        'detailed_scores': scores
                    }
                    matches.append(match_info)
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def _get_strategy_config(self, strategy: str, base_threshold: int) -> Tuple[int, List[str]]:
        """Get configuration for different matching strategies"""
        strategies = {
            'strict': {
                'threshold': max(base_threshold, 90),
                'algorithms': ['token_sort', 'partial', 'token_set']
            },
            'optimal': {
                'threshold': base_threshold,
                'algorithms': ['token_sort', 'partial', 'ratio', 'token_set']
            },
            'lenient': {
                'threshold': min(base_threshold, 75),
                'algorithms': ['partial', 'token_sort', 'ratio']
            },
            'company': {
                'threshold': base_threshold,
                'algorithms': ['token_sort', 'partial_company', 'token_set']
            }
        }
        
        config = strategies.get(strategy, strategies['optimal'])
        return config['threshold'], config['algorithms']
    
    def _calculate_match_scores(self, search: str, target: str, algorithms: List[str]) -> Dict[str, float]:
        """Calculate multiple fuzzy matching scores"""
        scores = {}
        
        for algorithm in algorithms:
            if algorithm == 'token_sort':
                scores[algorithm] = fuzz.token_sort_ratio(search, target)
            elif algorithm == 'token_set':
                scores[algorithm] = fuzz.token_set_ratio(search, target)
            elif algorithm == 'partial':
                scores[algorithm] = fuzz.partial_ratio(search, target)
            elif algorithm == 'ratio':
                scores[algorithm] = fuzz.ratio(search, target)
            elif algorithm == 'partial_company':
                # Enhanced partial matching for company names
                scores[algorithm] = self._partial_company_match(search, target)
        
        return scores
    
    def _partial_company_match(self, search: str, target: str) -> float:
        """Enhanced partial matching optimized for company names"""
        # Check for acronym matches
        search_acronym = ''.join([word[0] for word in search.split() if word])
        target_acronym = ''.join([word[0] for word in target.split() if word])
        
        if search_acronym and target_acronym and len(search_acronym) > 1:
            acronym_score = fuzz.ratio(search_acronym, target_acronym)
        else:
            acronym_score = 0
        
        # Use the best of partial ratio and acronym score
        partial_score = fuzz.partial_ratio(search, target)
        return max(partial_score, acronym_score * 0.8)  # Weight acronym matches slightly lower
    
    def _calculate_weighted_score(self, scores: Dict[str, float], strategy: str) -> float:
        """Calculate weighted score based on strategy"""
        weights = {
            'strict': {'token_sort': 0.4, 'partial': 0.3, 'token_set': 0.3},
            'optimal': {'token_sort': 0.5, 'partial': 0.2, 'ratio': 0.2, 'token_set': 0.1},
            'lenient': {'partial': 0.6, 'token_sort': 0.3, 'ratio': 0.1},
            'company': {'token_sort': 0.6, 'partial_company': 0.4}
        }
        
        weight_config = weights.get(strategy, weights['optimal'])
        weighted_score = 0
        
        for algorithm, score in scores.items():
            if algorithm in weight_config:
                weighted_score += score * weight_config[algorithm]
        
        return min(100, weighted_score)  # Cap at 100
    
    def batch_screen_entities(self, 
                            entities: List[Dict[str, Any]], 
                            threshold: int = 85,
                            strategy: str = 'optimal') -> Dict[str, List[Dict]]:
        """
        Screen multiple entities at once with different strategies for individuals vs companies
        
        Args:
            entities: List of entities with 'name' and optionally 'type' fields
            threshold: Base threshold
            strategy: Default strategy
        """
        results = {}
        
        for entity in entities:
            entity_name = entity.get('name')
            entity_type = entity.get('type', 'unknown').lower()
            
            # Choose strategy based on entity type
            if entity_type in ['company', 'organization', 'corporation']:
                match_strategy = 'company'
            elif entity_type in ['individual', 'person']:
                match_strategy = 'strict'  # Be more strict with individuals
            else:
                match_strategy = strategy
            
            matches = self.match_single_name(entity_name, threshold, match_strategy)
            if matches:
                results[entity_name] = {
                    'matches': matches,
                    'strategy_used': match_strategy,
                    'entity_type': entity_type
                }
        
        return results
    
    def get_matching_stats(self) -> Dict[str, Any]:
        """Get statistics about the matching system"""
        total_entities = len(self.sanctions_data)
        total_names = len(self.name_index)
        
        # Count by list type
        list_counts = defaultdict(int)
        for entity in self.sanctions_data:
            list_type = entity.get('list_type', 'unknown')
            list_counts[list_type] += 1
        
        return {
            'total_entities': total_entities,
            'total_names': total_names,
            'entities_by_list': dict(list_counts),
            'average_names_per_entity': total_names / total_entities if total_entities > 0 else 0
        }
