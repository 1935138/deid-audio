from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json
import os

@dataclass
class AudioSegment:
    """음성 파일의 세그먼트 정보를 저장하는 클래스"""
    start_time: float
    end_time: float
    text: str
    
class AudioTranscript:
    """음성 파일의 전사 정보를 저장하고 관리하는 클래스"""
    
    def __init__(self, audio_path: str):
        self.audio_path: str = audio_path
        self.file_name: str = os.path.basename(audio_path)
        self.transcript: str = ""
        self.segments: List[AudioSegment] = []
        self.processing_time: float = 0.0
        self.processed_date: datetime = datetime.now()
        
    def add_transcript(self, text: str, processing_time: float = 0.0):
        """전체 전사 텍스트 추가"""
        self.transcript = text
        self.processing_time = processing_time
        self.processed_date = datetime.now()
        
    def add_segment(self, start_time: float, end_time: float, text: str):
        """세그먼트 정보 추가"""
        segment = AudioSegment(start_time, end_time, text)
        self.segments.append(segment)
        
    def save_to_json(self, output_dir: str):
        """전사 정보를 JSON 파일로 저장"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        base_name = os.path.splitext(self.file_name)[0]
        output_path = os.path.join(output_dir, f"{base_name}_transcript.json")
        
        data = {
            "audio_file": self.file_name,
            "transcript": self.transcript,
            "processing_time": self.processing_time,
            "processed_date": self.processed_date.isoformat(),
            "segments": [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "text": seg.text
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
            
            self.segments = []
            for seg_data in data["segments"]:
                self.add_segment(
                    seg_data["start_time"],
                    seg_data["end_time"],
                    seg_data["text"]
                )
                
            return True
        except Exception as e:
            print(f"JSON 파일 로드 실패: {e}")
            return False 