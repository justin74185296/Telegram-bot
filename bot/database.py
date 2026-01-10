import json
import logging
import os
from fuzzywuzzy import fuzz, process
from typing import List, Dict, Optional

class LocationDatabase:
    """
    Handles loading and searching of location data from the static JSON file.
    """
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.locations = self._load_data()
        logging.info(f"Loaded {len(self.locations)} locations from database.")

    def _load_data(self) -> List[Dict]:
        """Loads data from JSON file."""
        if not os.path.exists(self.data_path):
            logging.error(f"Data file not found at {self.data_path}")
            return []
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("locations", [])
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return []

    def search(self, query: str, threshold: int = 70, limit: int = 5) -> List[Dict]:
        """
        Searches for locations based on fuzzy matching against multiple fields.
        
        Priority Logic:
        1. Calculate similarity score for sub_area, area, city, country.
        2. Filter by threshold.
        3. Sort by:
           - Score (descending)
           - Has TG contacts (priority)
        """
        results = []
        query = query.lower().strip()

        for loc in self.locations:
            # Calculate scores for different fields
            scores = {
                'sub_area': fuzz.partial_ratio(query, loc.get('sub_area', '').lower()),
                'area': fuzz.partial_ratio(query, loc.get('area', '').lower()),
                'city': fuzz.partial_ratio(query, loc.get('city', '').lower()),
                'country': fuzz.partial_ratio(query, loc.get('country', '').lower()),
                'nickname': fuzz.partial_ratio(query, loc.get('nickname', '').lower())
            }
            
            # Get the maximum score among all fields
            best_score = max(scores.values())
            
            # Determine which field matched best (for potential debug/logging)
            # We add a small boost if the match is in a more specific field (sub_area > area > city)
            # to break ties in scores naturally, though 'score' is main factor.
            final_score = best_score
            
            if best_score >= threshold:
                # Add score to location object for sorting (create a copy to not mutate original)
                result_entry = loc.copy()
                result_entry['_score'] = final_score
                results.append(result_entry)

        # Sorting Logic:
        # 1. Primary Sort: Score (Higher is better)
        # 2. Secondary Sort: Has TG contacts (True > False)
        # We use a tuple for sorting: (score, has_tg_contacts)
        
        def sort_key(x):
            has_tg = len(x.get('tg_contacts', [])) > 0
            return (x['_score'], has_tg)

        results.sort(key=sort_key, reverse=True)
        
        return results[:limit]
