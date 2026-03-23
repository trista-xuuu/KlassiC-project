import requests
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from collectors.base import BaseCollector
import datetime

class TavilySearchCollector(BaseCollector):
    def __init__(self):
        self.api_key = config.TAVILY_API_KEY
        self.url = "https://api.tavily.com/search"
        self.keywords = config.SEARCH_KEYWORDS

    def collect(self) -> List[Dict]:
        if not self.api_key:
            print("[警告] 尚未設定 TAVILY_API_KEY，略過 Tavily 搜集")
            return []

        results = []
        headers = {
            "Content-Type": "application/json"
        }

        for keyword in self.keywords:
            payload = {
                "api_key": self.api_key,
                "query": keyword,
                "search_depth": "advanced",
                "max_results": 5,
                "include_images": False
            }
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    search_results = data.get("results", [])
                    for item in search_results:
                        title = item.get("title", "")
                        content = item.get("content", "")
                        
                        # 簡單過濾，確保內容跟 KlassiC / 眼鏡有關
                        if "klassic" in title.lower() or "klassic" in content.lower() or "眼鏡" in title:
                            results.append({
                                "source": "Tavily AI Search",
                                "title": title,
                                "content": content,
                                "url": item.get("url", ""),
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                else:
                    print(f"[錯誤] Tavily API 回應失敗 ({response.status_code}): {response.text}")
            except Exception as e:
                print(f"[錯誤] Tavily 搜集發生例外 ({keyword}): {e}")
        
        return results
