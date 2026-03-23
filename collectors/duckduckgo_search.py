import sys
import os
import datetime
from typing import List, Dict
from duckduckgo_search import DDGS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from collectors.base import BaseCollector

class DuckDuckGoCollector(BaseCollector):
    def __init__(self):
        self.keywords = config.SEARCH_KEYWORDS

    def collect(self) -> List[Dict]:
        results = []
        print("[提示] 正在使用 DuckDuckGo 進行搜尋...")
        try:
            with DDGS() as ddgs:
                for keyword in self.keywords:
                    # 使用台灣地區進行搜尋以獲取更高相關性的資料
                    search_results = ddgs.text(f"{keyword} region:tw", max_results=3)
                    
                    if not search_results:
                        continue
                        
                    for item in search_results:
                        title = item.get('title', '')
                        content = item.get('body', '')
                        
                        # 基礎關鍵字過濾
                        if "klassic" in title.lower() or "klassic" in content.lower() or "眼鏡" in title:
                            results.append({
                                "source": "DuckDuckGo (備用方案)",
                                "title": title,
                                "content": content,
                                "url": item.get('href', ''),
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
        except Exception as e:
            print(f"[錯誤] DuckDuckGo 搜尋發生例外: {e}")
            
        return results
