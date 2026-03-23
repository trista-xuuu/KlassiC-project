"""
KlassiC 輿情自動化系統 — 全域設定
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# 路徑設定
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
TEMPLATES_DIR = BASE_DIR / "reporters" / "templates"

load_dotenv(BASE_DIR / ".env")

# 確保 reports 資料夾存在
REPORTS_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────
# API 金鑰
# ──────────────────────────────────────────────
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ──────────────────────────────────────────────
# 搜尋關鍵字
# ──────────────────────────────────────────────
SEARCH_KEYWORDS = [
    "KlassiC 眼鏡",
    "KlassiC 門市",
    "KlassiC 評價",
    "KlassiC 鏡框",
    "KlassiC 價格",
]

# ──────────────────────────────────────────────
# 排程設定
# ──────────────────────────────────────────────
SCHEDULE_TIME = "09:00"  # 台北時間 (Asia/Taipei)
TIMEZONE = "Asia/Taipei"

# ──────────────────────────────────────────────
# LLM 設定
# ──────────────────────────────────────────────
GEMINI_MODEL = "gemini-flash-latest"
SENTIMENT_SYSTEM_PROMPT = """你是一位專業的品牌輿情分析師，專注於分析台灣眼鏡品牌「KlassiC」的網路討論與評價。

請針對以下文本進行情緒分析，並以 JSON 格式回傳結果。回傳格式如下：
{
    "sentiment": "positive | negative | neutral",
    "intensity": "normal | high",
    "summary": "一句話摘要（繁體中文）",
    "topics": ["相關話題標籤"],
    "suggestion": "若為負面情緒，提供一句改善建議；若非負面則為空字串",
    "alert": false
}

分類準則：
- positive：對品牌的正面評價，如設計好看、性價比高、服務好、驗光專業
- negative：對品牌的負面評價，如品質問題、價格偏高、服務差、等候時間久
- neutral：中性描述或僅為資訊分享
- intensity 為 "high" 的條件：文字帶有非常強烈的情緒（憤怒、極度不滿、狂讚等）
- alert 為 true 的條件：intensity 為 high 且 sentiment 為 negative（潛在公關危機）

請務必只回傳純 JSON，不要包含任何其他文字。"""

# ──────────────────────────────────────────────
# Google Maps 門市搜尋
# ──────────────────────────────────────────────
MAPS_SEARCH_QUERY = "KlassiC 眼鏡 門市"
