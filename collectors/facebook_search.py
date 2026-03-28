import os
import requests
import time
import datetime
from .base import BaseCollector
import config

class FacebookSearchCollector(BaseCollector):
    """
    透過 Apify (danek/facebook-search-ppr) 來搜尋 Facebook 最近的貼文討論。
    """
    def __init__(self):
        super().__init__()
        self.apify_token = os.getenv("APIFY_TOKEN")
        self.actor_id = "danek~facebook-search-ppr"
        
    def _headers(self) -> dict:
        """統一回傳帶有 Bearer Token 的 Header，避免 token 出現在 URL 中"""
        return {"Authorization": f"Bearer {self.apify_token}", "Content-Type": "application/json"}

    def collect(self) -> list:
        if not self.apify_token:
            print("[Facebook] 缺少 APIFY_TOKEN，略過 Facebook 搜尋...")
            return []
            
        # 使用專案本身的關鍵字
        query = config.SEARCH_KEYWORDS[0] if config.SEARCH_KEYWORDS else "KlassiC"
        
        print(f"[Facebook] 正在透過 Apify 搜尋 Facebook 貼文，關鍵字：{query}...")
        
        input_data = {
            "query": query,
            "search_type": "posts",
            "max_posts": 5, 
            "recent_posts": True
        }
        
        results = []
        try:
            # 1. 觸發 Actor 運行 (Token 放在 Header，不放 URL)
            start_url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"
            response = requests.post(start_url, json=input_data, headers=self._headers(), timeout=30)
            response.raise_for_status()
            
            run_info = response.json().get('data', {})
            run_id = run_info.get('id')
            dataset_id = run_info.get('defaultDatasetId')
            
            # 2. 等待完成 (最多等 2 分鐘)
            retries = 0
            while retries < 24:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
                status_resp = requests.get(status_url, headers=self._headers(), timeout=15).json().get('data', {})
                status = status_resp.get('status')
                
                if status == 'SUCCEEDED':
                    break
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    print(f"[Facebook] Apify Actor 執行失敗，狀態：{status}")
                    return []
                    
                time.sleep(5)
                retries += 1
                
            if retries >= 24:
                print("[Facebook] Apify 執行超時 (超過 2 分鐘)，中止提取。")
                return []
                
            # 3. 取得 Dataset 內容
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            items_response = requests.get(dataset_url, headers=self._headers(), timeout=30)
            items = items_response.json()
            
            for item in items:
                text = item.get('text') or item.get('message') or ""
                url = item.get('url') or ""
                
                if len(text.strip()) > 5:
                    results.append({
                        "source": "Facebook (社群)",
                        "title": f"FB社群討論：{text[:15]}...",
                        "content": text,
                        "url": url,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    
            print(f"[Facebook] 成功透過 Apify 抓取 {len(results)} 筆社群討論！")
            
        except Exception as e:
            print(f"[Facebook] 嘗試連接 Apify 失敗：{e}")
            
        return results
