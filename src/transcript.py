import os
from faster_whisper import WhisperModel, vad
import sys
import time
from pathlib import Path
import argparse

# AudioTranscript 클래스 import를 위한 경로 설정
sys.path.append(str(Path(__file__).parent.parent))
from src.audio_transcript_info import AudioTranscriptInfo


def transcribe_audio(audio_file_path, model_size="medium", output_dir="output/transcript"):
    """
    faster-whisper를 사용하여 음성 파일을 전사하는 함수
    
    Args:
        audio_file_path (str): 전사할 오디오 파일 경로
        model_size (str): Whisper 모델 크기 (tiny, base, small, medium, large-v2, large-v3)
        output_dir (str): 결과 JSON 파일이 저장될 디렉토리
    
    Returns:
        str: 저장된 JSON 파일 경로
    """
    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"오류: 음성 파일을 찾을 수 없습니다 - {audio_file_path}")
    
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
    
    print(f"음성 파일 전사 시작: {audio_file_path}")
    
    # 전사 시작 시간 기록
    start_time = time.time()
    
    # 음성 파일 전사
    # language="ko" 옵션으로 한국어 전사 최적화 가능
    segments, info = model.transcribe(
        audio_file_path, 
        language="ko",  # 한국어 설정 (None으로 설정시 자동 감지)
        beam_size=5,    # 빔 서치 크기
        temperature=0.0,
        patience=1.2,
        word_timestamps=True,  # 단어별 타임스탬프 포함
        vad_filter=True,
        vad_parameters = vad.VadOptions(
            threshold=0.4,
            neg_threshold=0.15,
            min_speech_duration_ms=1200,
            max_speech_duration_s=30,
            min_silence_duration_ms=2000,
            speech_pad_ms=1000
        )
    )
    
    # 처리 시간 계산
    processing_time = time.time() - start_time
    
    print(f"감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
    print(f"전체 길이: {info.duration:.2f}초")
    print(f"처리 시간: {processing_time:.2f}초")
    print("\n=== 전사 결과 ===")
    
    # AudioTranscript 객체 생성
    transcript = AudioTranscriptInfo(audio_file_path)
    
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
    output_path = transcript.save_to_json(output_dir)
    
    print(f"\n전사 결과가 {output_path}에 저장되었습니다.")
    return output_path

def main():
    """
    명령줄에서 오디오 파일 경로를 받아 전사를 수행하는 메인 함수
    """
    parser = argparse.ArgumentParser(
        description="오디오 파일을 Whisper를 사용하여 전사하고 JSON으로 저장합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python src/transcript.py audio.wav
  python src/transcript.py data/recording.wav --model medium --output results/
  python src/transcript.py recording.mp3 --model large-v3
        """
    )
    
    parser.add_argument(
        "audio_file",
        help="전사할 오디오 파일 경로"
    )
    
    parser.add_argument(
        "--model", "-m",
        default="medium",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="사용할 Whisper 모델 크기 (기본값: medium)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="결과 JSON 파일이 저장될 디렉토리 (기본값: output)"
    )
    
    args = parser.parse_args()
    
    try:
        output_path = transcribe_audio(args.audio_file, args.model, args.output)
        print(f"✅ 전사 완료: {output_path}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 전사 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # main()

    for root, dirs, files in os.walk("data/denoised"):
        for file in files:
            if file.endswith(".wav"):
                full_path = os.path.join(root, file)
                print(f"▶ 전사 대상: {full_path}")
                # transcribe_audio(full_path, "medium", "output/transcript")
                # transcribe_audio(full_path, "byoussef/whisper-large-v2-Ko", "output/transcript_byoussef_whisper-large-v2-Ko")
                # transcribe_audio(full_path, "Systran/faster-whisper-large-v3", "output/transcript")
                transcribe_audio(full_path, "medium", "output/transcript")
