"""
MongoDB 데이터베이스 유틸리티 함수
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from .connection import get_database
from .models import AudioData, TranscriptionData, PersonalInfoData
import logging

logger = logging.getLogger(__name__)

def get_audio_collection() -> Collection:
    """오디오 컬렉션을 가져옵니다."""
    db = get_database()
    return db.audio_data

def create_indexes():
    """필요한 인덱스를 생성합니다."""
    try:
        collection = get_audio_collection()
        
        # 기본 인덱스들
        collection.create_index("filename", unique=True)
        collection.create_index("file_path", unique=True)
        collection.create_index("created_at")
        collection.create_index("status")
        
        # 전사 데이터 관련 인덱스
        collection.create_index("transcription.personal_info.type")
        collection.create_index("transcription.language")
        
        # 메타데이터 인덱스
        collection.create_index("metadata.speaker_id")
        collection.create_index("metadata.tags")
        
        logger.info("MongoDB 인덱스가 성공적으로 생성되었습니다")
        
    except Exception as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

async def insert_audio_data(audio_data: AudioData) -> str:
    """
    새로운 오디오 데이터를 삽입합니다.
    
    Args:
        audio_data: 삽입할 오디오 데이터
        
    Returns:
        삽입된 문서의 ObjectId (문자열)
    """
    try:
        collection = get_audio_collection()
        
        # Pydantic 모델을 dict로 변환
        audio_dict = audio_data.dict(by_alias=True, exclude_unset=True)
        
        # 현재 시간으로 updated_at 설정
        audio_dict["updated_at"] = datetime.now()
        
        result = collection.insert_one(audio_dict)
        
        logger.info(f"오디오 데이터가 성공적으로 삽입되었습니다: {result.inserted_id}")
        return str(result.inserted_id)
        
    except DuplicateKeyError:
        logger.error(f"중복된 파일명 또는 경로: {audio_data.filename}")
        raise ValueError(f"이미 존재하는 파일입니다: {audio_data.filename}")
    
    except Exception as e:
        logger.error(f"오디오 데이터 삽입 실패: {e}")
        raise

async def get_audio_data(audio_id: str) -> Optional[AudioData]:
    """
    ID로 오디오 데이터를 조회합니다.
    
    Args:
        audio_id: 조회할 오디오 데이터의 ObjectId
        
    Returns:
        AudioData 객체 또는 None
    """
    try:
        collection = get_audio_collection()
        
        document = collection.find_one({"_id": ObjectId(audio_id)})
        
        if document:
            return AudioData(**document)
        return None
        
    except Exception as e:
        logger.error(f"오디오 데이터 조회 실패: {e}")
        raise

async def get_audio_data_by_filename(filename: str) -> Optional[AudioData]:
    """
    파일명으로 오디오 데이터를 조회합니다.
    
    Args:
        filename: 조회할 파일명
        
    Returns:
        AudioData 객체 또는 None
    """
    try:
        collection = get_audio_collection()
        
        document = collection.find_one({"filename": filename})
        
        if document:
            return AudioData(**document)
        return None
        
    except Exception as e:
        logger.error(f"오디오 데이터 조회 실패 (파일명: {filename}): {e}")
        raise

async def update_audio_data(audio_id: str, update_data: Dict[str, Any]) -> bool:
    """
    오디오 데이터를 업데이트합니다.
    
    Args:
        audio_id: 업데이트할 오디오 데이터의 ObjectId
        update_data: 업데이트할 데이터
        
    Returns:
        업데이트 성공 여부
    """
    try:
        collection = get_audio_collection()
        
        # updated_at 필드 추가
        update_data["updated_at"] = datetime.now()
        
        result = collection.update_one(
            {"_id": ObjectId(audio_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"오디오 데이터가 성공적으로 업데이트되었습니다: {audio_id}")
            return True
        else:
            logger.warning(f"업데이트할 오디오 데이터를 찾을 수 없습니다: {audio_id}")
            return False
            
    except Exception as e:
        logger.error(f"오디오 데이터 업데이트 실패: {e}")
        raise

async def update_transcription_data(audio_id: str, transcription: TranscriptionData) -> bool:
    """
    전사 데이터를 업데이트합니다.
    
    Args:
        audio_id: 업데이트할 오디오 데이터의 ObjectId
        transcription: 전사 데이터
        
    Returns:
        업데이트 성공 여부
    """
    try:
        transcription_dict = transcription.dict()
        
        return await update_audio_data(audio_id, {
            "transcription": transcription_dict,
            "status": "transcribed"
        })
        
    except Exception as e:
        logger.error(f"전사 데이터 업데이트 실패: {e}")
        raise

async def add_personal_info(audio_id: str, personal_info_list: List[PersonalInfoData]) -> bool:
    """
    개인정보 데이터를 추가합니다.
    
    Args:
        audio_id: 오디오 데이터의 ObjectId
        personal_info_list: 추가할 개인정보 리스트
        
    Returns:
        추가 성공 여부
    """
    try:
        collection = get_audio_collection()
        
        personal_info_dicts = [pii.dict() for pii in personal_info_list]
        
        result = collection.update_one(
            {"_id": ObjectId(audio_id)},
            {
                "$push": {"transcription.personal_info": {"$each": personal_info_dicts}},
                "$set": {"updated_at": datetime.now(), "status": "processed"}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"개인정보 데이터가 성공적으로 추가되었습니다: {audio_id}")
            return True
        else:
            logger.warning(f"개인정보를 추가할 오디오 데이터를 찾을 수 없습니다: {audio_id}")
            return False
            
    except Exception as e:
        logger.error(f"개인정보 데이터 추가 실패: {e}")
        raise

async def delete_audio_data(audio_id: str) -> bool:
    """
    오디오 데이터를 삭제합니다.
    
    Args:
        audio_id: 삭제할 오디오 데이터의 ObjectId
        
    Returns:
        삭제 성공 여부
    """
    try:
        collection = get_audio_collection()
        
        result = collection.delete_one({"_id": ObjectId(audio_id)})
        
        if result.deleted_count > 0:
            logger.info(f"오디오 데이터가 성공적으로 삭제되었습니다: {audio_id}")
            return True
        else:
            logger.warning(f"삭제할 오디오 데이터를 찾을 수 없습니다: {audio_id}")
            return False
            
    except Exception as e:
        logger.error(f"오디오 데이터 삭제 실패: {e}")
        raise

async def search_audio_data(
    query: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    skip: int = 0,
    sort_field: str = "created_at",
    sort_direction: int = -1
) -> List[AudioData]:
    """
    오디오 데이터를 검색합니다.
    
    Args:
        query: MongoDB 쿼리 딕셔너리
        limit: 반환할 최대 문서 수
        skip: 건너뛸 문서 수 (페이징용)
        sort_field: 정렬 필드
        sort_direction: 정렬 방향 (1: 오름차순, -1: 내림차순)
        
    Returns:
        AudioData 객체 리스트
    """
    try:
        collection = get_audio_collection()
        
        if query is None:
            query = {}
        
        cursor = collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
        
        audio_data_list = []
        for document in cursor:
            audio_data_list.append(AudioData(**document))
        
        logger.info(f"검색 결과: {len(audio_data_list)}개의 오디오 데이터를 찾았습니다")
        return audio_data_list
        
    except Exception as e:
        logger.error(f"오디오 데이터 검색 실패: {e}")
        raise

async def search_by_personal_info_type(pii_type: str) -> List[AudioData]:
    """
    특정 개인정보 유형이 포함된 오디오 데이터를 검색합니다.
    
    Args:
        pii_type: 개인정보 유형 (예: "NAME", "PHONE_NUMBER")
        
    Returns:
        AudioData 객체 리스트
    """
    query = {"transcription.personal_info.type": pii_type}
    return await search_audio_data(query)

async def get_statistics() -> Dict[str, Any]:
    """
    데이터베이스 통계를 반환합니다.
    
    Returns:
        통계 정보 딕셔너리
    """
    try:
        collection = get_audio_collection()
        
        total_count = collection.count_documents({})
        processed_count = collection.count_documents({"status": "processed"})
        transcribed_count = collection.count_documents({"status": "transcribed"})
        uploaded_count = collection.count_documents({"status": "uploaded"})
        
        # 개인정보 유형별 통계
        pipeline = [
            {"$unwind": "$transcription.personal_info"},
            {"$group": {
                "_id": "$transcription.personal_info.type",
                "count": {"$sum": 1}
            }}
        ]
        
        pii_stats = {}
        for result in collection.aggregate(pipeline):
            pii_stats[result["_id"]] = result["count"]
        
        statistics = {
            "total_audio_files": total_count,
            "status_breakdown": {
                "uploaded": uploaded_count,
                "transcribed": transcribed_count,
                "processed": processed_count
            },
            "personal_info_types": pii_stats,
            "last_updated": datetime.now()
        }
        
        logger.info("데이터베이스 통계가 성공적으로 생성되었습니다")
        return statistics
        
    except Exception as e:
        logger.error(f"통계 생성 실패: {e}")
        raise 