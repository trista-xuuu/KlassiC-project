import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class TelegramNotifier:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        if self.token:
             self.url = f"https://api.telegram.org/bot{self.token}/"

    def send_message(self, text: str, is_alert: bool = False):
        if not self.token or not self.chat_id:
            print("[警告] 尚未設定 TELEGRAM_BOT_TOKEN 或 CHAT_ID，略過 Telegram 推播")
            return

        api_url = self.url + "sendMessage"
        
        if is_alert:
             text = "🚨 **緊急公關預警** 🚨\n\n" + text
             
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
             response = requests.post(api_url, data=data)
             if response.status_code == 200:
                  print("[推播] Telegram 訊息發送成功")
             else:
                  print(f"[錯誤] Telegram 發送失敗: {response.text}")
        except Exception as e:
             print(f"[例外] Telegram 推播: {e}")

    def send_document(self, file_path: str):
        if not self.token or not self.chat_id:
             return
             
        api_url = self.url + "sendDocument"
        data = {"chat_id": self.chat_id}
        try:
             with open(file_path, "rb") as f:
                 files = {"document": f}
                 response = requests.post(api_url, data=data, files=files)
                 if response.status_code == 200:
                      print(f"[推播] Telegram 附件 {os.path.basename(file_path)} 傳送成功")
                 else:
                      print(f"[錯誤] Telegram 附件發送失敗: {response.text}")
        except Exception as e:
             print(f"[例外] Telegram 附件傳送: {e}")
