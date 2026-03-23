import os
import sys
import datetime
from jinja2 import Environment, FileSystemLoader

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class HtmlReporter:
    def __init__(self):
        self.templates_dir = config.TEMPLATES_DIR
        self.reports_dir = config.REPORTS_DIR
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    def generate(self, records: list, summary_data: dict) -> str:
        """
        將分析結果與摘要帶入 Jinja2 模板，產出 HTML 檔案
        :return: 產出的 HTML 檔案路徑
        """
        template = self.env.get_template("report.html")
        
        # 準備傳給前端的變數
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 統計圖表資料
        counts = summary_data["sentiment_counts"]
        total = sum(counts.values()) or 1
        pie_data = [
            round(counts.get("positive", 0) / total * 100, 1),
            round(counts.get("neutral", 0) / total * 100, 1),
            round(counts.get("negative", 0) / total * 100, 1)
        ]
        
        html_content = template.render(
            today=today,
            total_count=total,
            pie_data=pie_data,
            top_topics=summary_data["top_topics"],
            alerts=summary_data["alerts"],
            records=records
        )
        
        # 存檔今日報告
        file_path = self.reports_dir / f"KlassiC_Report_{today}.html"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # 為了支援 GitHub Pages 永遠顯示最新報告：在根目錄產生一個跳轉用的 index.html
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        index_path = os.path.join(root_dir, "index.html")
        redirect_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=reports/KlassiC_Report_{today}.html">
    <title>正在為您載入 KlassiC 最新輿情報告...</title>
</head>
<body>
    <p>正在為您跳轉至最新報告，若沒有反應請 <a href="reports/KlassiC_Report_{today}.html">點此進入</a>。</p>
</body>
</html>'''
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(redirect_html)
        
        print(f"[報告產出] HTML 報告與首頁跳轉檔已生成於: {file_path}")
        return str(file_path)

    def generate_summary_text(self, summary_data: dict, total_records: int) -> str:
        """
        產生供 LINE / Telegram 推播用的純文字精簡版摘要
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        counts = summary_data["sentiment_counts"]
        
        text = f"📊 【KlassiC 輿情日報】 {today} 📊\n"
        text += f"共分析 {total_records} 則潛在討論與新訊\n"
        text += f"🔹 正面: {counts.get('positive', 0)} 則\n"
        text += f"🔸 中立: {counts.get('neutral', 0)} 則\n"
        text += f"🔺 負面: {counts.get('negative', 0)} 則\n\n"
        
        text += "🔥 【前三名熱門話題】\n"
        if summary_data["top_topics"]:
            for t, cnt in summary_data["top_topics"]:
                text += f"- {t} ({cnt}則)\n"
        else:
            text += "無特別突出的話題\n"
            
        positive_highlights = summary_data.get("positive_highlights", [])
        negative_highlights = summary_data.get("negative_highlights", [])
        if positive_highlights or negative_highlights:
            text += "\n💬 【具代表性輿情原聲帶】\n"
            for ph in positive_highlights:
                text += f"👍 {ph}\n"
            for nh in negative_highlights:
                text += f"👎 {nh}\n"
                
        suggestions = summary_data.get("suggestions", [])
        if suggestions:
            text += "\n💡 【AI 營運改善建議】\n"
            for s in suggestions:
                text += f"- {s}\n"

        if summary_data["alerts"]:
            text += f"\n🚨 **高風險預警:** 偵測到 {len(summary_data['alerts'])} 則激動/負面評論，請立即留意以下公關危機可能：\n"
            for alert in summary_data["alerts"][:2]:
                text += f"❗ {alert['title']} 🔗 {alert.get('url', '無連結')}\n"

        # 加上 GitHub Pages 可被手機一點擊就開起的連結
        text += "\n\n🔗 [完整圖表數據報告]\n👉 點此在手機觀看：https://trista-xuuu.github.io/KlassiC-project/"
        
        return text
