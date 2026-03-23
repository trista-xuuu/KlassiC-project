import argparse
import schedule
import time
import datetime
import subprocess
import shutil
import os
from typing import List, Dict

import config
from collectors.google_maps import GoogleMapsCollector
from collectors.tavily_search import TavilySearchCollector
from collectors.duckduckgo_search import DuckDuckGoCollector
from collectors.facebook_search import FacebookSearchCollector
from collectors.dcard_search import DcardCollector
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

    # Facebook 社群貼文 (透過 Apify)
    fb_search = FacebookSearchCollector()
    raw_records.extend(fb_search.collect())
    
    # Dcard 論壇匿名文章
    dcard_search = DcardCollector()
    raw_records.extend(dcard_search.collect())

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
    # 3. 產出 HTML 與 Markdown 報告
    # ==========================
    print(">>> 執行報告產出模組...")
    reporter = HtmlReporter()
    report_path = reporter.generate(analyzed_records, summary_data)
    summary_text = reporter.generate_summary_text(summary_data, len(analyzed_records))
    
    # 產出 Markdown 檔案供 Obsidian 備份使用
    md_filename = f"KlassiC_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.md"
    md_path = config.REPORTS_DIR / md_filename
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 📊 KlassiC 輿情日報\n\n" + summary_text + "\n\n---\n*本報告由 KlassiC 輿情自動化系統產出*")

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
    
    # 產出完畢後，立即執行雲端 (GitHub) 與本地端 (Obsidian) 的雙重備份
    backup_to_obsidian()
    backup_to_github()

def backup_to_github():
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動自動備份任務 (Backup to GitHub)...")
    
    # 建立通知發送實例
    line = LineNotifier()
    tg = TelegramNotifier()
    
    try:
        # 只將 reports 資料夾與 index.html 加進追蹤機制
        subprocess.run(["git", "add", "reports/", "index.html"], check=True)
        
        # 檢查是否有新檔案或變更需要 commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if "reports/" in status.stdout or "index.html" in status.stdout or "R  reports/" in status.stdout or "A  reports/" in status.stdout or "?? reports/" in status.stdout:
            commit_msg = f"docs: auto-backup daily reports {datetime.datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push"], check=True)
            
            # 通知推送
            success_msg = f"📦 【系統通知】\n今日 ({datetime.datetime.now().strftime('%Y-%m-%d')}) 的 KlassiC 輿情報告已經安全且自動地備份至 GitHub 倉庫了！"
            print("[備份成功] 昨日的報表已順利推送上傳至 GitHub！")
            line.send(message=success_msg)
            tg.send_message(text=success_msg)
        else:
            print("[備份略過] 尚未偵測到新的 HTML 報告，無須備份。")
            # 針對空備份可以選擇不吵使用者，或者如果您希望得知無備份狀態也可以在此加入傳送
            
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ 【系統警報】\nGitHub 自動備份任務失敗！\n錯誤原因 Git 指令：\n{e}"
        print(f"[備份失敗] {error_msg}")
        line.send(message=error_msg)
        tg.send_message(text=error_msg)
    except Exception as e:
        except_msg = f"❌ 【系統警報】\nGitHub 備份模組發生異常崩潰：\n{e}"
        print(f"[備份例外] {except_msg}")
        line.send(message=except_msg)
        tg.send_message(text=except_msg)

def backup_to_obsidian():
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動自動備份任務 (Backup to Obsidian)...")
    
    line = LineNotifier()
    tg = TelegramNotifier()
    
    obsidian_path = config.OBSIDIAN_VAULT_PATH
    if not obsidian_path:
        error_msg = "⚠️ 【本地備份警告】\n未能執行 Obsidian 備份，因為 `.env` 中尚未設定 `OBSIDIAN_VAULT_PATH`！"
        print(f"[備份略過] {error_msg}")
        # 不強制發送警告到群組，避免很吵
        return
        
    vault_dir = os.path.join(obsidian_path, "KlassiC_Reports")
    os.makedirs(vault_dir, exist_ok=True)
    
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    md_filename = f"KlassiC_Report_{today_str}.md"
    src_md = config.REPORTS_DIR / md_filename
    
    if not src_md.exists():
        print(f"[備份略過] 在 reports 資料夾下找不到今日的 Markdown 報告: {md_filename}")
        return
        
    try:
        dest_md = os.path.join(vault_dir, md_filename)
        shutil.copy2(src_md, dest_md)
        print(f"[備份成功] 今日報告已匯出至 Obsidian: {dest_md}")
        
        success_msg = f"📓 【本地備份通知】\n今日 ({today_str}) 的輿情報告已經順利備份至您的 Obsidian Vault 中！"
        line.send(message=success_msg)
        tg.send_message(text=success_msg)
    except Exception as e:
        error_msg = f"❌ 【系統警報】\n複製報告至 Obsidian Vault 時發生失敗：\n{e}"
        print(f"[備份例外] {error_msg}")
        line.send(message=error_msg)
        tg.send_message(text=error_msg)

def main():
    parser = argparse.ArgumentParser(description="KlassiC 輿情監測與自動化通報系統")
    parser.add_argument("--now", action="store_true", help="忽略排程，立即強制執行一次完整流程")
    args = parser.parse_args()

    if args.now:
        run_pipeline()
    else:
        print(f"啟動排程系統 (核心任務：每日 {config.SCHEDULE_TIME} 台北時間執行爬蟲、推播並同步備份)")
        schedule.every().day.at(config.SCHEDULE_TIME, config.TIMEZONE).do(run_pipeline)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n排程系統已手動中止。")

if __name__ == "__main__":
    main()
