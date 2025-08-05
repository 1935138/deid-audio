from ten_vad import TenVad
import numpy as np
from typing import List, Tuple, Dict
import librosa
import whisper
import torch

class Detector:
    def __init__(self, 
                 hop_size: int = 256, 
                 threshold: float = 0.5,
                 min_speech_duration: float = 0.3,    # 최소 음성 구간 길이 (초)
                 min_silence_duration: float = 0.3,   # 최소 묵음 구간 길이 (초)
                 max_speech_duration: float = 30.0,   # 최대 음성 구간 길이 (초)
                 window_size: int = 3,                # 컨텍스트 윈도우 크기
                 whisper_model: str = "medium"        # Whisper 모델 크기
                ):
        """
        음성 구간 검출을 위한 Detector 클래스 초기화
        
        Args:
            hop_size (int): VAD 처리를 위한 프레임 크기 (기본값: 256)
            threshold (float): 음성 구간 판단을 위한 임계값 (기본값: 0.5)
            min_speech_duration (float): 최소 음성 구간 길이 (초)
            min_silence_duration (float): 최소 묵음 구간 길이 (초)
            max_speech_duration (float): 최대 음성 구간 길이 (초)
            window_size (int): 컨텍스트 고려를 위한 윈도우 크기
            whisper_model (str): Whisper 모델 크기 ("tiny", "base", "small", "medium", "large")
        """
        self.vad = TenVad(hop_size=hop_size, threshold=threshold)
        self.hop_size = hop_size
        self.min_speech_frames = int(min_speech_duration * 16000 / hop_size)
        self.min_silence_frames = int(min_silence_duration * 16000 / hop_size)
        self.max_speech_frames = int(max_speech_duration * 16000 / hop_size)
        self.window_size = window_size
        
        # Whisper 모델 초기화
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.asr_model = whisper.load_model(whisper_model).to(device)

    def smooth_predictions(self, probabilities: List[float]) -> List[bool]:
        """
        확률값을 스무딩하여 음성 구간을 결정
        
        Args:
            probabilities (List[float]): 각 프레임의 음성 확률값
            
        Returns:
            List[bool]: 스무딩된 음성 구간 판단 결과
        """
        speech_frames = []
        half_window = self.window_size // 2
        
        for i in range(len(probabilities)):
            # 주변 프레임들의 확률값 평균 계산
            start_idx = max(0, i - half_window)
            end_idx = min(len(probabilities), i + half_window + 1)
            avg_prob = sum(probabilities[start_idx:end_idx]) / (end_idx - start_idx)
            speech_frames.append(avg_prob > self.vad.threshold)
            
        return speech_frames
        
    def split_long_segments(self, segments: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        긴 음성 구간을 최대 길이로 분할
        
        Args:
            segments (List[Tuple[float, float]]): 원본 음성 구간 리스트
            
        Returns:
            List[Tuple[float, float]]: 분할된 음성 구간 리스트
        """
        split_segments = []
        max_duration = self.max_speech_frames * self.hop_size / 16000
        
        for start, end in segments:
            duration = end - start
            if duration > max_duration:
                # 구간을 최대 길이로 분할
                num_splits = int(np.ceil(duration / max_duration))
                for i in range(num_splits):
                    split_start = start + i * max_duration
                    split_end = min(split_start + max_duration, end)
                    split_segments.append((split_start, split_end))
            else:
                split_segments.append((start, end))
                
        return split_segments

    def merge_segments(self, segments: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        가까운 음성 구간들을 병합
        
        Args:
            segments (List[Tuple[float, float]]): 원본 음성 구간 리스트
            
        Returns:
            List[Tuple[float, float]]: 병합된 음성 구간 리스트
        """
        if not segments:
            return []
            
        merged = []
        current_start, current_end = segments[0]
        
        for start, end in segments[1:]:
            # 현재 구간과 다음 구간의 간격이 min_silence_duration보다 작으면 병합
            gap_duration = start - current_end
            if gap_duration < (self.min_silence_frames * self.hop_size / 16000):
                current_end = end
            else:
                # 현재 구간의 길이가 최소 길이보다 길면 추가
                if (current_end - current_start) >= (self.min_speech_frames * self.hop_size / 16000):
                    merged.append((current_start, current_end))
                current_start, current_end = start, end
                
        # 마지막 구간 처리
        if (current_end - current_start) >= (self.min_speech_frames * self.hop_size / 16000):
            merged.append((current_start, current_end))
            
        return merged

    def detect_speech(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """
        오디오에서 음성 구간을 검출하는 메서드
        
        Args:
            audio (np.ndarray): 입력 오디오 신호
            sr (int): 오디오의 샘플링 레이트
            
        Returns:
            List[Tuple[float, float]]: 검출된 음성 구간의 시작과 끝 시간(초)을 담은 리스트
        """
        # 16kHz로 리샘플링
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            
        # float32를 int16으로 변환
        if audio.dtype != np.int16:
            audio = (audio * 32767).astype(np.int16)
            
        # 프레임 단위로 처리
        segments = []
        start_frame = None
        probabilities = []
        
        # 각 프레임의 음성 확률 계산
        for i in range(0, len(audio) - self.hop_size + 1, self.hop_size):
            frame = audio[i:i + self.hop_size]
            if len(frame) < self.hop_size:
                break
                
            prob, _ = self.vad.process(frame)
            probabilities.append(prob)
            
        # 확률값 스무딩 및 음성 구간 검출
        speech_frames = self.smooth_predictions(probabilities)
        
        # 음성 구간 검출
        for i, is_speech in enumerate(speech_frames):
            if is_speech and start_frame is None:
                start_frame = i
            elif not is_speech and start_frame is not None:
                segments.append((
                    start_frame * self.hop_size / 16000,
                    i * self.hop_size / 16000
                ))
                start_frame = None
                
        # 마지막 음성 구간 처리
        if start_frame is not None:
            segments.append((
                start_frame * self.hop_size / 16000,
                len(speech_frames) * self.hop_size / 16000
            ))
            
        # 음성 구간 병합
        segments = self.merge_segments(segments)
        
        # 긴 음성 구간 분할
        segments = self.split_long_segments(segments)
            
        return segments

    def transcribe_segments(self, audio: np.ndarray, sr: int, segments: List[Tuple[float, float]]) -> List[Dict]:
        """
        검출된 음성 구간별로 전사 수행
        
        Args:
            audio (np.ndarray): 입력 오디오 신호
            sr (int): 오디오의 샘플링 레이트
            segments (List[Tuple[float, float]]): 음성 구간 리스트
            
        Returns:
            List[Dict]: 각 구간별 전사 결과 (시작 시간, 끝 시간, 텍스트)
        """
        results = []
        
        for i, (start, end) in enumerate(segments, 1):
            # 시간을 샘플 인덱스로 변환
            start_idx = int(start * sr)
            end_idx = int(end * sr)
            
            # 구간 오디오 추출
            segment_audio = audio[start_idx:end_idx]
            
            # Whisper 모델로 전사
            result = self.asr_model.transcribe(
                segment_audio, 
                language="ko",
                task="transcribe"
            )
            
            # 결과 저장
            results.append({
                "segment_id": i,
                "start": start,
                "end": end,
                "duration": end - start,
                "text": result["text"].strip()
            })
            
        return results

    def detect_and_transcribe(self, audio: np.ndarray, sr: int) -> List[Dict]:
        """
        오디오에서 음성 구간을 검출하고 전사를 수행하는 메서드
        
        Args:
            audio (np.ndarray): 입력 오디오 신호
            sr (int): 오디오의 샘플링 레이트
            
        Returns:
            List[Dict]: 검출 및 전사 결과
        """
        # 음성 구간 검출
        segments = self.detect_speech(audio, sr)
        
        # 검출된 구간 전사
        results = self.transcribe_segments(audio, sr, segments)
        
        return results

if __name__ == "__main__":
    detector = Detector(
        threshold=0.4,
        min_speech_duration_ms=1200,
        max_speech_duration_s=30,
        min_silence_duration_ms=2000,
        speech_pad_ms=1000,              # 음성 구간 전후 패딩
        whisper_model="medium",           # Whisper 중형 모델 사용
    )
    
    # 오디오 파일 로드
    audio, sr = librosa.load("data/raw/202103230700001_ai-stt-relay001.wav", sr=None)
    
    # 음성 구간 검출 및 전사 수행
    results = detector.detect_and_transcribe(audio, sr)
    
    # 결과 출력
    print("\n음성 구간 검출 및 전사 결과:")
    print("-" * 50)
    for result in results:
        print(f"[구간 {result['segment_id']}]")
        print(f"시간: {result['start']:.2f}초 ~ {result['end']:.2f}초 (길이: {result['duration']:.2f}초)")
        print(f"전사 결과: {result['text']}")
        print("-" * 50)