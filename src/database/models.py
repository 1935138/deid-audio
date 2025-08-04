"""
오디오 데이터 모델 정의
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    """MongoDB ObjectId를 Pydantic에서 사용하기 위한 클래스"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class WordData(BaseModel):
    """단어별 전사 데이터"""
    text: str = Field(..., description="전사된 단어")
    start_time: float = Field(..., description="시작 시간(초)")
    end_time: float = Field(..., description="종료 시간(초)")
    confidence: Optional[float] = Field(None, description="신뢰도 점수")

class SentenceData(BaseModel):
    """문장별 전사 데이터"""
    text: str = Field(..., description="전사된 문장")
    start_time: float = Field(..., description="시작 시간(초)")
    end_time: float = Field(..., description="종료 시간(초)")
    words: List[WordData] = Field(default_factory=list, description="단어별 상세 정보")

class PersonalInfoData(BaseModel):
    """개인정보 데이터"""
    type: str = Field(..., description="개인정보 유형 (NAME, PHONE_NUMBER, ADDRESS 등)")
    value: str = Field(..., description="원본 개인정보 값")
    masked_value: str = Field(..., description="비식별화된 값")
    start_time: float = Field(..., description="시작 시간(초)")
    end_time: float = Field(..., description="종료 시간(초)")
    word_index: Optional[int] = Field(None, description="해당 단어의 인덱스")
    sentence_index: Optional[int] = Field(None, description="해당 문장의 인덱스")
    confidence_score: Optional[float] = Field(None, description="탐지 신뢰도")

class TranscriptionData(BaseModel):
    """전사 데이터 전체"""
    sentences: List[SentenceData] = Field(default_factory=list, description="문장별 전사 데이터")
    personal_info: List[PersonalInfoData] = Field(default_factory=list, description="탐지된 개인정보")
    language: Optional[str] = Field("ko", description="언어 코드")
    transcription_engine: Optional[str] = Field("whisper", description="전사 엔진")
    processed_at: datetime = Field(default_factory=datetime.now, description="전사 처리 시간")

class AudioMetadata(BaseModel):
    """오디오 메타데이터"""
    speaker_id: Optional[str] = Field(None, description="화자 ID")
    recording_date: Optional[datetime] = Field(None, description="녹음 날짜")
    sample_rate: Optional[int] = Field(None, description="샘플링 레이트")
    channels: Optional[int] = Field(None, description="채널 수")
    bit_depth: Optional[int] = Field(None, description="비트 깊이")
    tags: List[str] = Field(default_factory=list, description="태그")

class AudioData(BaseModel):
    """오디오 데이터 메인 모델"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    filename: str = Field(..., description="파일명")
    file_path: str = Field(..., description="파일 경로")
    file_size: Optional[int] = Field(None, description="파일 크기(바이트)")
    duration: Optional[float] = Field(None, description="재생 시간(초)")
    format: Optional[str] = Field(None, description="오디오 포맷")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="수정 시간")
    
    # 전사 및 개인정보 데이터
    transcription: Optional[TranscriptionData] = Field(None, description="전사 데이터")
    
    # 메타데이터
    metadata: Optional[AudioMetadata] = Field(None, description="오디오 메타데이터")
    
    # 처리 상태
    status: str = Field(default="uploaded", description="처리 상태 (uploaded, transcribed, processed)")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "filename": "sample_audio.wav",
                "file_path": "/data/sample_audio.wav",
                "duration": 120.5,
                "format": "wav",
                "transcription": {
                    "sentences": [
                        {
                            "text": "안녕하세요, 제 이름은 홍길동입니다.",
                            "start_time": 0.0,
                            "end_time": 3.2,
                            "words": [
                                {"text": "안녕하세요", "start_time": 0.0, "end_time": 1.0},
                                {"text": "제", "start_time": 1.1, "end_time": 1.3},
                                {"text": "이름은", "start_time": 1.4, "end_time": 1.8},
                                {"text": "홍길동입니다", "start_time": 1.9, "end_time": 3.2}
                            ]
                        }
                    ],
                    "personal_info": [
                        {
                            "type": "NAME",
                            "value": "홍길동",
                            "masked_value": "[이름]",
                            "start_time": 1.9,
                            "end_time": 3.2,
                            "word_index": 3,
                            "sentence_index": 0
                        }
                    ]
                },
                "status": "processed"
            }
        } 