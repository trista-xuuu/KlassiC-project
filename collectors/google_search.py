import requests
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from collectors.base import BaseCollector
import datetime

class GoogleSearchCollector(BaseCollector):
    def __init__(self):
        self.api_key = config.SERPER_API_KEY
        self.url = "https://google.serper.dev/search"
        self.keywords = config.SEARCH_KEYWORDS

    def collect(self) -> List[Dict]:
        if not self.api_key:
            print("[警告] 尚未設定 SERPER_API_KEY，略過 Google Search 搜集")
            return []

        results = []
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        # 只取過去 24 小時的資料 (qdr:d)，聚焦台灣 (gl:tw)
        for keyword in self.keywords:
            payload = {
                "q": keyword,
                "gl": "tw",
                "hl": "zh-tw",
                "tbs": "qdr:d" 
            }
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    organic_results = data.get("organic", [])
                    for item in organic_results:
                        # 篩選掉可能不相干的資料，確保結果包含 KlassiC 或眼鏡
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        if "klassic" in title.lower() or "klassic" in snippet.lower() or "眼鏡" in title:
                            results.append({
                                "source": "Google 搜尋",
                                "title": title,
                                "content": snippet,
                                "url": item.get("link", ""),
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
            except Exception as e:
                print(f"[錯誤] Google 搜尋發生例外 ({keyword}): {e}")
        
        return results
