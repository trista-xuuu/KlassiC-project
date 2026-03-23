import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class LineNotifier:
    def __init__(self):
        self.access_token = config.LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = config.LINE_USER_ID
        self.url = "https://api.line.me/v2/bot/message/push"

    def send(self, message: str, is_alert: bool = False):
        if not self.access_token or not self.user_id:
            print("[警告] 尚未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID，略過 LINE 推播")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # 如果是緊急警報，可以在訊息前面再加上明顯的 tag
        if is_alert:
            message = "\n【緊急公關預警】\n" + message

        data = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            response = requests.post(self.url, headers=headers, json=data)
            if response.status_code == 200:
                print("[推播] LINE Messaging API 發送成功")
            else:
                print(f"[錯誤] LINE 發送失敗: {response.status_code} {response.text}")
        except Exception as e:
            print(f"[例外] LINE 推播: {e}")
