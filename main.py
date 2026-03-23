import argparse
import schedule
import time
import datetime
from typing import List, Dict

import config
from collectors.google_maps import GoogleMapsCollector
from collectors.tavily_search import TavilySearchCollector
from collectors.duckduckgo_search import DuckDuckGoCollector
from analyzers.sentiment import SentimentAnalyzer
from reporters.html_report import HtmlReporter
from notifiers.line_notify import LineNotifier
from notifiers.telegram_notify import TelegramNotifier

def run_pipeline():
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動 KlassiC 輿情監測流水線...")

    # ==========================
    # 1. 搜集資料
    # ==========================
    print(">>> 執行搜集模組...")
    tavily_search = TavilySearchCollector()
    ddg_search = DuckDuckGoCollector()
    google_maps = GoogleMapsCollector()
    
    raw_records = []
    
    # 網路搜尋：首選 Tavily，若無資料則啟動 DuckDuckGo 備用
    tavily_results = tavily_search.collect()
    if tavily_results:
        print(f"[成功] Tavily 首選搜尋取得 {len(tavily_results)} 筆資料。")
        raw_records.extend(tavily_results)
    else:
        print("[警告] Tavily 搜尋無結果或未設定金鑰，啟動備用方案 (DuckDuckGo)...")
        ddg_results = ddg_search.collect()
        if ddg_results:
            print(f"[成功] DuckDuckGo 備用搜尋取得 {len(ddg_results)} 筆資料。")
        raw_records.extend(ddg_results)
        
    # 實體門市評論
    raw_records.extend(google_maps.collect())
    
    if not raw_records:
         print("[提示] 無搜集到任何新資料。系統可能尚未設定 Serper 金鑰?")
         # 若為 Demo / 開發測試用，可以塞一筆假資料
         raw_records = [
             {
                 "source": "假資料來源",
                 "title": "KlassiC 最新聯名款開箱",
                 "content": "我覺得這次的聯名框超好看！",
                 "url": "https://example.com",
                 "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
             }
         ]
         
    print(f"總共搜集到 {len(raw_records)} 筆初步資料。")

    # ==========================
    # 2. LLM 分析與過濾
    # ==========================
    print(">>> 執行 LLM 分析模組...")
    analyzer = SentimentAnalyzer()
    analyzed_records = analyzer.analyze(raw_records)
    summary_data = analyzer.summarize_overall(analyzed_records)

    # ==========================
    # 3. 產出 HTML 報告
    # ==========================
    print(">>> 執行報告產出模組...")
    reporter = HtmlReporter()
    report_path = reporter.generate(analyzed_records, summary_data)
    summary_text = reporter.generate_summary_text(summary_data, len(analyzed_records))

    # ==========================
    # 4. 發送推播
    # ==========================
    print(">>> 執行推播通知模組...")
    line = LineNotifier()
    tg = TelegramNotifier()
    
    # 一般日報通知
    line.send(message=summary_text)
    tg.send_message(text=summary_text)
    tg.send_document(file_path=report_path)

    # ==========================
    # 5. 緊急預警
    # ==========================
    if summary_data["alerts"]:
         print(">>> 偵測到緊急預警，觸發發送！")
         for alert in summary_data["alerts"]:
              # 組合警報文字
              alert_text = f"事件來源：{alert['source']}\n標題：{alert['title']}\n" \
                           f"摘要：{alert['analysis']['summary']}\n" \
                           f"原始連結：{alert['url']}\n"
              line.send(message=alert_text, is_alert=True)
              tg.send_message(text=alert_text, is_alert=True)
              
    print("[完成] 輿情監測流水線執行完畢。\n")

def main():
    parser = argparse.ArgumentParser(description="KlassiC 輿情監測與自動化通報系統")
    parser.add_argument("--now", action="store_true", help="忽略排程，立即強制執行一次完整流程")
    args = parser.parse_args()

    if args.now:
        run_pipeline()
    else:
        print(f"啟動排程系統 (排程設定時間: 每日 {config.SCHEDULE_TIME} 台北時間)")
        schedule.every().day.at(config.SCHEDULE_TIME, config.TIMEZONE).do(run_pipeline)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n排程系統已手動中止。")

if __name__ == "__main__":
    main()
