import json
import sys
import os
import time
from typing import List, Dict
import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.has_key = bool(self.api_key)
        if self.has_key:
            genai.configure(api_key=self.api_key)
            # 初始化 Gemini 模型並設定 System Prompt 及 JSON 回傳格式
            self.model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                system_instruction=config.SENTIMENT_SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                )
            )

    def analyze(self, records: List[Dict]) -> List[Dict]:
        """
        將收集來的資料傳給 Gemini 進行情緒與主題分析。
        並將結果組合回去。
        """
        if not self.has_key:
            print("[警告] 尚未設定 GEMINI_API_KEY，回傳預設分析結果")
            # 填入假的分析結果以供測試排版
            for record in records:
                record["analysis"] = {
                    "sentiment": "neutral",
                    "intensity": "normal",
                    "summary": "尚未設定 API 金鑰，使用預設摘要。",
                    "topics": ["無分析"],
                    "suggestion": "",
                    "alert": False
                }
            return records

        analyzed_records = []
        for record in records:
            text_to_analyze = f"標題：{record['title']}\n內文：{record['content']}"
            
            try:
                response = self.model.generate_content(text_to_analyze)
                result_json = response.text
                analysis_result = json.loads(result_json)
                
                # 將分析結果存回 record 內
                record["analysis"] = analysis_result
                analyzed_records.append(record)
                
            except Exception as e:
                print(f"[錯誤] 分析時發生例外: {e}")
                record["analysis"] = {
                    "sentiment": "neutral", "intensity": "normal",
                    "summary": "分析發生錯誤", "topics": [], "suggestion": "", "alert": False
                }
                analyzed_records.append(record)
                
            # 為了避免觸發 Gemini Free Tier 的「每分鐘 15 次」請求限制，強制各暫停 5 秒
            time.sleep(5)

        return analyzed_records

    def summarize_overall(self, records: List[Dict]) -> Dict:
        """根據分析結果統計整體指標"""
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        alerts = []
        all_topics = {}
        
        # 定義要過濾的無意義標籤 (轉小寫比對)
        stop_words = {"klassic", "眼鏡", "品牌", "商品", "門市", "產品"}

        for r in records:
            ans = r.get("analysis", {})
            snt = ans.get("sentiment", "neutral")
            
            if snt in sentiment_counts:
                sentiment_counts[snt] += 1
            else:
                sentiment_counts["neutral"] += 1
                
            if ans.get("alert") is True:
                alerts.append(r)
                
            for t in ans.get("topics", []):
                t_clean = t.strip()
                if t_clean.lower() not in stop_words and len(t_clean) > 1:
                    all_topics[t_clean] = all_topics.get(t_clean, 0) + 1

        # 取前三名的話題
        top_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 收集重點洞察與建議
        positive_highlights = []
        negative_highlights = []
        suggestions = []
        for r in records:
            ans = r.get("analysis", {})
            sentiment = ans.get("sentiment", "neutral")
            intensity = ans.get("intensity", "normal")
            summary = ans.get("summary", "")
            sugg = ans.get("suggestion", "")
            
            if sentiment == "positive" and intensity == "high" and summary:
                positive_highlights.append(summary)
            elif sentiment == "positive" and summary and len(positive_highlights) < 2:
                positive_highlights.append(summary)
                
            if sentiment == "negative" and intensity == "high" and summary:
                negative_highlights.append(summary)
            elif sentiment == "negative" and summary and len(negative_highlights) < 2:
                negative_highlights.append(summary)
                
            if sugg and "無" not in sugg and "不需要" not in sugg and len(sugg) > 5:
                # 排除空字串或無建議的
                if len(suggestions) < 3:
                    suggestions.append(sugg)
        
        return {
            "sentiment_counts": sentiment_counts,
            "alerts": alerts,
            "top_topics": top_topics,
            "positive_highlights": positive_highlights[:2],
            "negative_highlights": negative_highlights[:2],
            "suggestions": list(set(suggestions))[:3]
        }
