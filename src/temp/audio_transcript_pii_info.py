from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json
import os
from pydantic import BaseModel

@dataclass
class WordTimestamp:
    """단어별 타임스탬프 정보를 저장하는 클래스"""
    word: str
    start: float
    end: float

@dataclass
class AudioSegmentPII:
    """음성 파일의 세그먼트 정보를 저장하는 클래스 (PII 정보 포함)"""
    id: str
    text: str
    start: float
    end: float
    pii_text: List[str] = None  # 개인정보 텍스트
    pii_type: str = None  # 개인정보 타입 필드
    words: List[WordTimestamp] = None

    def __post_init__(self):
        if self.words is None:
            self.words = []

    def add_word(self, word: str, start: float, end: float):
        """단어 타임스탬프 정보 추가"""
        word_timestamp = WordTimestamp(word, start, end)
        self.words.append(word_timestamp)

class AudioTranscriptPIIInfo:
    """음성 파일의 전사 정보를 저장하고 관리하는 클래스 (PII 정보 포함)"""
    
    def __init__(self, audio_path: str):
        self.audio_path: str = audio_path
        self.file_name: str = os.path.basename(audio_path)
        self.transcript: str = ""
        self.segments: List[AudioSegmentPII] = []
        self.processing_time: float = 0.0
        self.processed_date: datetime = datetime.now()
        self.model_info: Optional[str] = None
        
    def add_transcript(self, text: str, processing_time: float = 0.0, model_info: Optional[str] = None):
        """전체 전사 텍스트 추가"""
        self.transcript = text
        self.processing_time = processing_time
        self.processed_date = datetime.now()
        self.model_info = model_info
        
    def add_segment(self, start: float, end: float, text: str) -> AudioSegmentPII:
        """세그먼트 정보 추가"""
        segment_id = str(len(self.segments) + 1)  # 1부터 시작하는 단순 숫자
        segment = AudioSegmentPII(id=segment_id, text=text, start=start, end=end)
        self.segments.append(segment)
        return segment
        
    def save_to_json(self, output_dir: str):
        """전사 정보를 JSON 파일로 저장"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        base_name = os.path.splitext(self.file_name)[0]
        timestamp = self.processed_date.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"{base_name}_{timestamp}.json")
        
        data = {
            "audio_file": self.file_name,
            "transcript": self.transcript,
            "processing_time": self.processing_time,
            "processed_date": self.processed_date.isoformat(),
            "model_info": self.model_info,
            "segments": [
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "pii_type": seg.pii_type,
                    "pii_text": seg.pii_text,
                    "words": [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "pii_type": word.pii_type
                        }
                        for word in seg.words
                    ] if seg.words else []
                }
                for seg in self.segments
            ]
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return output_path
    
    def load_from_json(self, json_path: str) -> bool:
        """JSON 파일에서 전사 정보 로드"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.file_name = data["audio_file"]
            self.transcript = data["transcript"]
            self.processing_time = data["processing_time"]
            self.processed_date = datetime.fromisoformat(data["processed_date"])
            self.model_info = data.get("model_info")
            
            self.segments = []
            for seg_data in data["segments"]:
                segment = AudioSegmentPII(
                    id=seg_data["id"],
                    text=seg_data["text"],
                    start=seg_data["start"],
                    end=seg_data["end"],
                    pii_type=seg_data.get("pii_type"),
                    pii_text=seg_data.get("pii_text")
                )
                
                # 단어 타임스탬프 정보 로드
                if "words" in seg_data:
                    for word_data in seg_data["words"]:
                        word_timestamp = WordTimestamp(
                            word_data["word"],
                            word_data["start"],
                            word_data["end"],
                            word_data.get("pii_type")
                        )
                        segment.words.append(word_timestamp)
                
                self.segments.append(segment)
                
            return True
        except Exception as e:
            print(f"JSON 파일 로드 실패: {e}")
            return False 