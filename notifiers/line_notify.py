import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class LineNotifier:
    def __init__(self):
        self.token = config.LINE_NOTIFY_TOKEN
        self.url = "https://notify-api.line.me/api/notify"

    def send(self, message: str, is_alert: bool = False):
        if not self.token:
            print("[警告] 尚未設定 LINE_NOTIFY_TOKEN，略過 LINE 推播")
            return

        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        # 如果是緊急警報，可以在訊息前面再加上明顯的 tag
        if is_alert:
            message = "\n【緊急公關預警】\n" + message

        data = {
            "message": message
        }

        try:
            response = requests.post(self.url, headers=headers, data=data)
            if response.status_code == 200:
                print("[推播] LINE Notify 發送成功")
            else:
                print(f"[錯誤] LINE Notify 發送失敗: {response.status_code} {response.text}")
        except Exception as e:
            print(f"[例外] LINE Notify: {e}")
