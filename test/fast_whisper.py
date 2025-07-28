import os
from faster_whisper import WhisperModel
import sys
import time
from pathlib import Path

# AudioTranscript 클래스 import를 위한 경로 설정
sys.path.append(str(Path(__file__).parent.parent))
from src.audio_transcript import AudioTranscript

def main():
    """
    faster-whisper를 사용하여 음성 파일을 전사하는 메인 함수
    """
    # 모델 크기 설정 (tiny, base, small, medium, large-v2, large-v3)
    model_size = "medium"
    
    # 모델 로드 (GPU 사용 시도, 실패하면 CPU로 대체)
    print(f"Whisper 모델 ({model_size}) 로딩 중...")
    
    # GPU 먼저 시도
    try:
        print("GPU 모드로 시도 중...")
        model = WhisperModel(model_size, device="cuda", compute_type="int8")
        print("GPU 모드 로딩 완료!")
    except Exception as e:
        print(f"GPU 모드 실패: {e}")
        print("CPU 모드로 대체 중...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("CPU 모드 로딩 완료!")
    
    # 음성 파일 경로 설정
    audio_file_path = "data/202503200800003_amone-relay-prod.wav"  # 실제 음성 파일 경로로 변경
    
    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        print(f"오류: 음성 파일을 찾을 수 없습니다 - {audio_file_path}")
        print("data/ 폴더에 음성 파일을 넣어주세요.")
        return
    
    print(f"음성 파일 전사 시작: {audio_file_path}")
    
    # 전사 시작 시간 기록
    start_time = time.time()
    
    # 음성 파일 전사
    # language="ko" 옵션으로 한국어 전사 최적화 가능
    segments, info = model.transcribe(
        audio_file_path, 
        language="ko",  # 한국어 설정 (None으로 설정시 자동 감지)
        beam_size=5,    # 빔 서치 크기
        word_timestamps=True  # 단어별 타임스탬프 포함
    )
    
    # 처리 시간 계산
    processing_time = time.time() - start_time
    
    print(f"감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
    print(f"전체 길이: {info.duration:.2f}초")
    print(f"처리 시간: {processing_time:.2f}초")
    print("\n=== 전사 결과 ===")
    
    # AudioTranscript 객체 생성
    transcript = AudioTranscript(audio_file_path)
    
    # 전체 텍스트 구성 및 세그먼트 추가
    full_text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        full_text += segment.text + " "
        
        # 세그먼트 추가
        audio_segment = transcript.add_segment(segment.start, segment.end, segment.text)
        
        # 단어별 타임스탬프 추가
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                print(f"  - {word.word} [{word.start:.2f}s-{word.end:.2f}s]")
                audio_segment.add_word(word.word, word.start, word.end)
    
    # 전체 전사 텍스트 및 모델 정보 추가
    model_info = f"faster-whisper-{model_size} (lang: {info.language}, confidence: {info.language_probability:.2f})"
    transcript.add_transcript(full_text.strip(), processing_time, model_info)
    
    # JSON 파일로 저장
    output_dir = "output"
    output_path = transcript.save_to_json(output_dir)
    
    print(f"\n전사 결과가 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    main() 