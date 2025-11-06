import json
import os
import threading
from datetime import datetime
from typing import Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisitorService:
    """访客计数服务类"""
    
    def __init__(self, data_file: str = "visitor_count.json"):
        self.data_file = data_file
        self.visitor_count = 0
        self.lock = threading.Lock()
        self.load_visitor_count()
    
    def load_visitor_count(self) -> None:
        """从JSON文件加载访客计数"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.visitor_count = data.get('count', 0)
                    logger.info(f"加载访客计数: {self.visitor_count}")
            else:
                self.visitor_count = 0
                logger.info("访客计数文件不存在，初始化为0")
        except Exception as e:
            logger.error(f"加载访客计数失败: {e}")
            self.visitor_count = 0
    
    def save_visitor_count(self) -> None:
        """保存访客计数到JSON文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({'count': self.visitor_count}, f, ensure_ascii=False, indent=2)
            logger.info(f"保存访客计数: {self.visitor_count}")
        except Exception as e:
            logger.error(f"保存访客计数失败: {e}")
    
    def get_count(self) -> int:
        """获取当前访客计数"""
        with self.lock:
            return self.visitor_count
    
    def increment_count(self) -> int:
        """增加访客计数"""
        with self.lock:
            self.visitor_count += 1
            self.save_visitor_count()
            logger.info(f"访客计数增加至: {self.visitor_count}")
            return self.visitor_count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        with self.lock:
            return {
                "count": self.visitor_count,
                "last_updated": datetime.now().isoformat(),
                "data_file": self.data_file,
                "status": "active"
            }
    
    def reset_count(self) -> int:
        """重置访客计数"""
        with self.lock:
            self.visitor_count = 0
            self.save_visitor_count()
            logger.info("访客计数已重置为0")
            return self.visitor_count
