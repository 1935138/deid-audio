"""
MongoDB 연결 관리 모듈
"""
import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
import logging

# 환경변수 로드
load_dotenv("config.env")

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """MongoDB 연결 관리 클래스"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("MONGODB_DATABASE", "deid_audio_db")
    
    def connect(self) -> Database:
        """MongoDB에 연결하고 데이터베이스 객체를 반환합니다."""
        try:
            if self.client is None:
                self.client = MongoClient(self.mongodb_url)
                # 연결 테스트
                self.client.admin.command('ping')
                logger.info(f"MongoDB에 성공적으로 연결되었습니다: {self.mongodb_url}")
            
            if self.database is None:
                self.database = self.client[self.database_name]
                logger.info(f"데이터베이스 '{self.database_name}' 에 연결되었습니다")
            
            return self.database
        
        except Exception as e:
            logger.error(f"MongoDB 연결 실패: {e}")
            raise ConnectionError(f"MongoDB 연결에 실패했습니다: {e}")
    
    def close(self):
        """MongoDB 연결을 종료합니다."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            logger.info("MongoDB 연결이 종료되었습니다")

# 전역 연결 인스턴스
_db_connection = DatabaseConnection()

def get_database() -> Database:
    """데이터베이스 연결을 가져옵니다."""
    return _db_connection.connect()

def close_connection():
    """데이터베이스 연결을 종료합니다."""
    _db_connection.close() 