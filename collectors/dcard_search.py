import os
import requests
import time
import datetime
from .base import BaseCollector
import config

class DcardCollector(BaseCollector):
    """
    純 Python 版本的 Dcard 爬蟲，無須 API Key，透過 Dcard 內部搜尋 API 取回年輕世代的真實評論。
    註：因應 Dcard 新版 Cloudflare 阻擋機器人機制，改透過 Apify 的 rag-web-browser 繞過防禦並進行搜尋。
    """
    def __init__(self):
        super().__init__()
        self.apify_token = os.getenv("APIFY_TOKEN")
        self.actor_id = "apify~rag-web-browser"
        
    def collect(self) -> list:
        if not self.apify_token:
            print("[Dcard] 缺少 APIFY_TOKEN，略過 Dcard 搜尋...")
            return []
            
        responses = []
        try:
            # 取第一組關鍵字
            query = config.SEARCH_KEYWORDS[0] if config.SEARCH_KEYWORDS else "KlassiC"
            search_query = f"{query} site:dcard.tw"
            
            print(f"[Dcard] 正在透過 Apify 潛入 Dcard 論壇搜尋，查詢：{search_query}...")
            
            input_data = {
                "query": search_query,
                "maxResults": 3  # 適中筆數
            }
            
            # 1. 觸發 Actor 運行
            start_url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs?token={self.apify_token}"
            response = requests.post(start_url, json=input_data)
            response.raise_for_status()
            
            run_info = response.json().get('data', {})
            run_id = run_info.get('id')
            dataset_id = run_info.get('defaultDatasetId')
            
            # 2. 等待完成 (最多等 2 分鐘)
            retries = 0
            while retries < 24:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={self.apify_token}"
                status_resp = requests.get(status_url).json().get('data', {})
                status = status_resp.get('status')
                
                if status == 'SUCCEEDED':
                    break
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    print(f"[Dcard] Apify Actor 執行失敗，狀態：{status}")
                    return []
                    
                time.sleep(5)
                retries += 1
                
            if retries >= 24:
                print("[Dcard] Apify 執行超時 (超過 2 分鐘)，中止提取。")
                return []
                
            # 3. 取得 Dataset 內容
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={self.apify_token}"
            items_response = requests.get(dataset_url)
            items = items_response.json()
            
            for item in items:
                search_result = item.get('searchResult', {})
                title = search_result.get('title', 'Dcard 標題')
                content = item.get('text', '') or item.get('markdown', '') or search_result.get('description', '')
                url = item.get('url', '') or search_result.get('url', '')
                
                if url and "dcard.tw" in url:
                    # 避免內文過長
                    if len(content) > 500:
                        content = content[:500] + "..."
                        
                    responses.append({
                        "source": "Dcard (社群)",
                        "title": f"Dcard 討論：{title[:50]}...",
                        "content": f"{title}\n{content}",
                        "url": url,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

                    
            print(f"[Dcard] 成功透過 Apify 抓取 {len(responses)} 筆 Dcard 真實討論！")
            
        except Exception as e:
            print(f"[Dcard] 連接 Dcard / Apify 發生錯誤：{e}")
            
        return responses
