import requests
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from collectors.base import BaseCollector
import datetime

class GoogleMapsCollector(BaseCollector):
    def __init__(self):
        self.api_key = config.SERPER_API_KEY
        self.url = "https://google.serper.dev/places"
        self.keyword = config.MAPS_SEARCH_QUERY

    def collect(self) -> List[Dict]:
        if not self.api_key:
            print("[警告] 尚未設定 SERPER_API_KEY，略過 Google Maps 搜集")
            return []

        results = []
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            "q": self.keyword,
            "gl": "tw",
            "hl": "zh-tw"
        }
        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                places = data.get("places", [])
                
                # 從各門市擷取評分與摘要 (因 Places API 沒有提供每則最新評論明細，抓取店鋪總體評語或最新摘要)
                for item in places:
                    title = item.get("title", "")
                    rating = item.get("rating", "N/A")
                    address = item.get("address", "")
                    
                    if "KlassiC" in title or "klassic" in title.lower():
                        results.append({
                            "source": "Google Maps 評價",
                            "title": f"{title} (評分: {rating})",
                            "content": f"地址：{address}。Google Maps 門市總體概覽與最新資訊更新。",
                            "url": "https://maps.google.com/?q=" + title.replace(" ", "+"),
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
        except Exception as e:
            print(f"[錯誤] Google Maps 搜集發生例外: {e}")
        
        return results
