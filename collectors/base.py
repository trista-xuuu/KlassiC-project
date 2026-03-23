from abc import ABC, abstractmethod
from typing import List, Dict

class BaseCollector(ABC):
    """資料搜集器基礎類別"""
    
    @abstractmethod
    def collect(self) -> List[Dict]:
        """
        執行資料搜集
        :return: 回傳一個包含字典的結構化資料列表
        格式約定:
        {
            "source": str,  # 來源名稱 (ex: Dcard, Google Search)
            "title": str,   # 標題
            "content": str, # 內文/摘要
            "url": str,     # 連結
            "date": str     # 日期時間字串
        }
        """
        pass
