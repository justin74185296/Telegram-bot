"""
Database Module - 資料庫模組
=============================
此模組負責載入 JSON 資料並執行模糊搜尋匹配。
This module handles JSON data loading and fuzzy search matching.

⚠️ 此 Bot 純粹用於程式學習、資料結構研究與全球地點匹配實驗，嚴禁公開部署或用於任何商業用途。
⚠️ This Bot is purely for programming learning and experiments. Do not deploy publicly.
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from fuzzywuzzy import fuzz, process

# JSON 資料檔案路徑 / Path to JSON data file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "global_locations.json")


class LocationDatabase:
    """
    地點資料庫類別
    Location Database Class
    
    負責載入、儲存和搜尋地點資料。
    Responsible for loading, storing, and searching location data.
    """
    
    def __init__(self, data_path: str = DATA_FILE_PATH):
        """
        初始化資料庫
        Initialize the database
        
        Args:
            data_path: JSON 資料檔案路徑 / Path to JSON data file
        """
        self.data_path = data_path
        self.locations: List[Dict] = []
        self._load_data()
    
    def _load_data(self) -> None:
        """
        從 JSON 檔案載入資料
        Load data from JSON file
        """
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.locations = data.get("locations", [])
                print(f"✅ 成功載入 {len(self.locations)} 筆地點資料")
                print(f"✅ Successfully loaded {len(self.locations)} location records")
        except FileNotFoundError:
            print(f"❌ 找不到資料檔案: {self.data_path}")
            print(f"❌ Data file not found: {self.data_path}")
            self.locations = []
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析錯誤: {e}")
            print(f"❌ JSON parse error: {e}")
            self.locations = []
    
    def _calculate_match_score(self, location: Dict, query: str) -> Tuple[int, int, bool]:
        """
        計算單一地點與查詢字串的匹配分數
        Calculate match score between a location and query string
        
        使用優先級排序：sub_area > area > city > country
        Priority ranking: sub_area > area > city > country
        
        Args:
            location: 地點資料字典 / Location data dictionary
            query: 使用者查詢字串 / User query string
            
        Returns:
            Tuple of (最高分數, 優先級, 是否有TG聯絡方式)
            Tuple of (highest_score, priority_level, has_tg_contacts)
        """
        query_lower = query.lower()
        
        # 定義欄位優先級（數字越小優先級越高）
        # Define field priority (lower number = higher priority)
        fields_priority = [
            ("sub_area", 1),      # 最高優先 / Highest priority
            ("area", 2),          # 次高 / Second
            ("city", 3),          # 第三 / Third
            ("country", 4),       # 最低 / Lowest
            ("nickname", 2),      # 與 area 同級 / Same as area
            ("address_detail", 3) # 與 city 同級 / Same as city
        ]
        
        best_score = 0
        best_priority = 999  # 較大數字表示較低優先級 / Higher number = lower priority
        
        for field_name, priority in fields_priority:
            field_value = location.get(field_name, "")
            if not field_value:
                continue
            
            # 使用多種模糊匹配方法取最高分
            # Use multiple fuzzy matching methods and take the highest score
            scores = [
                fuzz.ratio(query_lower, field_value.lower()),
                fuzz.partial_ratio(query_lower, field_value.lower()),
                fuzz.token_sort_ratio(query_lower, field_value.lower()),
                fuzz.token_set_ratio(query_lower, field_value.lower())
            ]
            max_score = max(scores)
            
            # 更新最佳分數和優先級
            # Update best score and priority
            if max_score > best_score or (max_score == best_score and priority < best_priority):
                best_score = max_score
                best_priority = priority
        
        # 檢查是否有 TG 聯絡方式
        # Check if has TG contacts
        has_tg = bool(location.get("tg_contacts", []))
        
        return (best_score, best_priority, has_tg)
    
    def search(self, query: str, threshold: int = 70, max_results: int = 6) -> List[Dict]:
        """
        搜尋匹配的地點
        Search for matching locations
        
        Args:
            query: 使用者查詢字串 / User query string
            threshold: 最低匹配門檻（預設70%）/ Minimum match threshold (default 70%)
            max_results: 最多回傳結果數（預設6）/ Maximum results to return (default 6)
            
        Returns:
            排序後的匹配地點列表 / Sorted list of matching locations
        """
        if not query or not query.strip():
            return []
        
        query = query.strip()
        results = []
        
        for location in self.locations:
            score, priority, has_tg = self._calculate_match_score(location, query)
            
            # 只保留超過門檻的結果
            # Only keep results above threshold
            if score >= threshold:
                results.append({
                    "location": location,
                    "score": score,
                    "priority": priority,
                    "has_tg": has_tg
                })
        
        # 排序邏輯：分數（降序）> 優先級（升序）> 有TG優先
        # Sorting logic: score (desc) > priority (asc) > has_tg first
        results.sort(key=lambda x: (-x["score"], x["priority"], -int(x["has_tg"])))
        
        # 回傳前 max_results 筆
        # Return top max_results
        return [r["location"] for r in results[:max_results]]
    
    def get_sample_locations(self, count: int = 5) -> List[str]:
        """
        取得範例地點名稱（用於提示使用者）
        Get sample location names (for user hints)
        
        Args:
            count: 要回傳的範例數量 / Number of samples to return
            
        Returns:
            範例地點字串列表 / List of sample location strings
        """
        samples = []
        for loc in self.locations[:count]:
            city = loc.get("city", "")
            area = loc.get("area", "")
            if city and area:
                samples.append(f"{city} {area}")
            elif city:
                samples.append(city)
        return samples
    
    def get_locations_by_region(self, region: str) -> List[Dict]:
        """
        依地區篩選地點
        Filter locations by region
        
        Args:
            region: 地區名稱（asia/europe/americas/other）
            
        Returns:
            該地區的地點列表 / List of locations in the region
        """
        region_mapping = {
            "asia": ["Japan", "China", "Taiwan", "Hong Kong", "Thailand", "Vietnam", 
                     "Singapore", "South Korea", "Indonesia", "Philippines", "Malaysia",
                     "India", "Nepal", "Cambodia", "Myanmar"],
            "europe": ["France", "Italy", "Germany", "Netherlands", "Spain", "UK", 
                       "United Kingdom", "Czech Republic", "Belgium", "Switzerland",
                       "Portugal", "Austria", "Greece", "Poland", "Hungary"],
            "americas": ["USA", "United States", "Canada", "Mexico", "Brazil", 
                         "Argentina", "Peru", "Colombia", "Chile", "Cuba"],
            "other": ["Australia", "Egypt", "Morocco", "South Africa", "Kenya",
                      "UAE", "Turkey", "New Zealand", "Israel"]
        }
        
        region_lower = region.lower()
        if region_lower not in region_mapping:
            return []
        
        countries = region_mapping[region_lower]
        return [loc for loc in self.locations 
                if loc.get("country", "") in countries][:6]


# 建立全域資料庫實例（單例模式）
# Create global database instance (singleton pattern)
_db_instance: Optional[LocationDatabase] = None


def get_database() -> LocationDatabase:
    """
    取得資料庫實例（單例模式）
    Get database instance (singleton pattern)
    
    Returns:
        LocationDatabase 實例 / LocationDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = LocationDatabase()
    return _db_instance
