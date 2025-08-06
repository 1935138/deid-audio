import os
from faster_whisper import WhisperModel, vad
import sys
import time
from pathlib import Path
import argparse
import logging
from typing import List, Optional

# AudioTranscript 클래스 import를 위한 경로 설정
sys.path.append(str(Path(__file__).parent.parent))
from src.audio_transcript_info import AudioTranscriptInfo

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def transcribe_audio(audio_file_path: str, 
                    model_size: str = "medium", 
                    output_dir: str = "output/transcript",
                    language: Optional[str] = "ko",
                    device: Optional[str] = None,
                    verbose: bool = True) -> str:
    """
    faster-whisper를 사용하여 음성 파일을 전사하는 함수
    
    Args:
        audio_file_path (str): 전사할 오디오 파일 경로
        model_size (str): Whisper 모델 크기 (tiny, base, small, medium, large-v2, large-v3)
        output_dir (str): 결과 JSON 파일이 저장될 디렉토리
        language (str, optional): 언어 설정 (ko, en, None=자동감지)
        device (str, optional): 장치 설정 (cuda, cpu, None=자동선택)
        verbose (bool): 상세 출력 여부
    
    Returns:
        str: 저장된 JSON 파일 경로
    """
    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"오류: 음성 파일을 찾을 수 없습니다 - {audio_file_path}")
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 모델 로드 (GPU 사용 시도, 실패하면 CPU로 대체)
    logging.info(f"Whisper 모델 ({model_size}) 로딩 중...")
    
    model = load_whisper_model(model_size, device)
    
    if verbose:
        logging.info(f"음성 파일 전사 시작: {audio_file_path}")
    
    # 전사 시작 시간 기록
    start_time = time.time()
    
    # 음성 파일 전사
    segments, info = model.transcribe(
        audio_file_path, 
        language=language,  # 언어 설정
        beam_size=5,        # 빔 서치 크기
        temperature=0.0,
        patience=1.2,
        word_timestamps=True,  # 단어별 타임스탬프 포함
        vad_filter=True,
        vad_parameters=vad.VadOptions(
            threshold=0.3,
            neg_threshold=0.15,
            min_speech_duration_ms=1200,
            max_speech_duration_s=30,
            min_silence_duration_ms=2000,
            speech_pad_ms=1000
        )
    )
    
    # 처리 시간 계산
    processing_time = time.time() - start_time
    
    if verbose:
        logging.info(f"감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
        logging.info(f"전체 길이: {info.duration:.2f}초")
        logging.info(f"처리 시간: {processing_time:.2f}초")
    
    # AudioTranscript 객체 생성
    transcript = AudioTranscriptInfo(audio_file_path)
    
    # 전체 텍스트 구성 및 세그먼트 추가
    full_text = ""
    for segment in segments:
        if verbose:
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        full_text += segment.text + " "
        
        # 세그먼트 추가
        audio_segment = transcript.add_segment(segment.start, segment.end, segment.text)
        
        # 단어별 타임스탬프 추가
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                if verbose:
                    print(f"  - {word.word} [{word.start:.2f}s-{word.end:.2f}s]")
                audio_segment.add_word(word.word, word.start, word.end)
    
    # 전체 전사 텍스트 및 모델 정보 추가
    model_info = f"faster-whisper-{model_size} (lang: {info.language}, confidence: {info.language_probability:.2f})"
    transcript.add_transcript(full_text.strip(), processing_time, model_info)
    
    # JSON 파일로 저장
    output_path = transcript.save_to_json(output_dir)
    
    if verbose:
        logging.info(f"전사 결과가 {output_path}에 저장되었습니다.")
    return output_path

def load_whisper_model(model_size: str, device: Optional[str] = None) -> WhisperModel:
    """
    Whisper 모델을 로드하는 함수
    
    Args:
        model_size (str): 모델 크기
        device (str, optional): 장치 설정
    
    Returns:
        WhisperModel: 로드된 모델
    """
    if device is None:
        # 자동 장치 선택
        try:
            logging.info("GPU 모드로 시도 중...")
            model = WhisperModel(model_size, device="cuda", compute_type="int8")
            logging.info("✅ GPU 모드 로딩 완료!")
            return model
        except Exception as e:
            logging.warning(f"GPU 모드 실패: {e}")
            logging.info("CPU 모드로 대체 중...")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logging.info("✅ CPU 모드 로딩 완료!")
            return model
    else:
        # 지정된 장치 사용
        try:
            compute_type = "int8" if device == "cuda" else "int8"
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logging.info(f"✅ {device.upper()} 모드 로딩 완료!")
            return model
        except Exception as e:
            logging.error(f"모델 로딩 실패: {e}")
            raise

def process_directory(input_dir: str, 
                     output_dir: str = "output/transcript",
                     model_size: str = "medium",
                     language: Optional[str] = "ko",
                     device: Optional[str] = None,
                     audio_extensions: Optional[List[str]] = None) -> None:
    """
    디렉토리 내의 모든 오디오 파일에 대해 전사를 수행하는 함수
    
    Args:
        input_dir (str): 입력 오디오 파일들이 있는 디렉토리
        output_dir (str): 결과 JSON 파일들이 저장될 디렉토리
        model_size (str): Whisper 모델 크기
        language (str, optional): 언어 설정
        device (str, optional): 장치 설정
        audio_extensions (List[str], optional): 지원할 오디오 확장자
    """
    if audio_extensions is None:
        audio_extensions = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
    
    # 입력 디렉토리 확인
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 오디오 파일 목록 수집
    audio_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        logging.warning(f"지원되는 오디오 파일이 없습니다: {input_dir}")
        return
    
    logging.info(f"총 {len(audio_files)}개의 오디오 파일을 처리합니다.")
    logging.info(f"설정: 모델={model_size}, 언어={language}, 장치={device or '자동'}")
    
    # 모델을 한 번만 로드 (성능 최적화)
    model = load_whisper_model(model_size, device)
    
    successful_count = 0
    failed_count = 0
    
    for idx, audio_file in enumerate(audio_files):
        try:
            logging.info(f"\n[{idx + 1}/{len(audio_files)}] 처리 중: {audio_file}")
            
            # 전사 수행 (모델 재로딩 없이)
            output_path = transcribe_audio_with_model(
                audio_file, model, output_dir, model_size, language, verbose=False
            )
            
            successful_count += 1
            logging.info(f"✅ 성공: {output_path}")
            
        except Exception as e:
            failed_count += 1
            logging.error(f"❌ 실패: {audio_file} - {str(e)}")
    
    # 처리 결과 출력
    logging.info(f"\n🎯 처리 완료 요약:")
    logging.info(f"✅ 성공: {successful_count} 파일")
    logging.info(f"❌ 실패: {failed_count} 파일")
    logging.info(f"📁 출력 디렉토리: {output_dir}")

def transcribe_audio_with_model(audio_file_path: str,
                               model: WhisperModel,
                               output_dir: str,
                               model_size: str,
                               language: Optional[str] = "ko",
                               verbose: bool = False) -> str:
    """
    이미 로드된 모델을 사용하여 전사를 수행하는 함수 (성능 최적화용)
    """
    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"오류: 음성 파일을 찾을 수 없습니다 - {audio_file_path}")
    
    # 전사 시작 시간 기록
    start_time = time.time()
    
    # 음성 파일 전사
    segments, info = model.transcribe(
        audio_file_path, 
        language=language,
        beam_size=5,
        temperature=0.0,
        patience=1.2,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=vad.VadOptions(
            threshold=0.3,
            neg_threshold=0.15,
            min_speech_duration_ms=1200,
            max_speech_duration_s=30,
            min_silence_duration_ms=2000,
            speech_pad_ms=1000
        )
    )
    
    # 처리 시간 계산
    processing_time = time.time() - start_time
    
    # AudioTranscript 객체 생성
    transcript = AudioTranscriptInfo(audio_file_path)
    
    # 전체 텍스트 구성 및 세그먼트 추가
    full_text = ""
    for segment in segments:
        full_text += segment.text + " "
        
        # 세그먼트 추가
        audio_segment = transcript.add_segment(segment.start, segment.end, segment.text)
        
        # 단어별 타임스탬프 추가
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                audio_segment.add_word(word.word, word.start, word.end)
    
    # 전체 전사 텍스트 및 모델 정보 추가
    model_info = f"faster-whisper-{model_size} (lang: {info.language}, confidence: {info.language_probability:.2f})"
    transcript.add_transcript(full_text.strip(), processing_time, model_info)
    
    # JSON 파일로 저장
    output_path = transcript.save_to_json(output_dir)
    
    return output_path

def process_single_file(input_path: str,
                       output_dir: str = "output/transcript",
                       model_size: str = "medium",
                       language: Optional[str] = "ko",
                       device: Optional[str] = None) -> str:
    """
    단일 파일에 대한 전사 수행
    
    Args:
        input_path (str): 입력 오디오 파일 경로
        output_dir (str): 출력 디렉토리
        model_size (str): 모델 크기
        language (str, optional): 언어 설정
        device (str, optional): 장치 설정
    
    Returns:
        str: 저장된 JSON 파일 경로
    """
    return transcribe_audio(input_path, model_size, output_dir, language, device, verbose=True)

def main():
    """
    명령줄에서 오디오 파일/디렉토리를 받아 전사를 수행하는 메인 함수
    """
    parser = argparse.ArgumentParser(
        description="오디오 파일을 Whisper를 사용하여 전사하고 JSON으로 저장합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 단일 파일 처리
  python src/transcription.py --single-file audio.wav
  python src/transcription.py -f recording.wav --model medium --output results/
  
  # 디렉토리 일괄 처리
  python src/transcription.py --input data/audio --output output/transcripts
  python src/transcription.py -i data/ -o results/ --model large-v3 --language en
        """
    )
    
    # 입력 방식 선택
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--single-file", "-f",
        help="전사할 단일 오디오 파일 경로"
    )
    input_group.add_argument(
        "--input", "-i",
        help="전사할 오디오 파일들이 있는 디렉토리 경로"
    )
    
    # 모델 설정
    parser.add_argument(
        "--model", "-m",
        default="medium",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="사용할 Whisper 모델 크기 (기본값: medium)"
    )
    
    # 출력 설정
    parser.add_argument(
        "--output", "-o",
        default="output/transcript",
        help="결과 JSON 파일이 저장될 디렉토리 (기본값: output/transcript)"
    )
    
    # 언어 설정
    parser.add_argument(
        "--language", "-l",
        default="ko",
        help="언어 설정 (ko, en, None=자동감지, 기본값: ko)"
    )
    
    # 장치 설정
    parser.add_argument(
        "--device", "-d",
        choices=["cuda", "cpu"],
        help="사용할 장치 (cuda, cpu, 기본값: 자동선택)"
    )
    
    # 오디오 확장자 설정
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".wav", ".mp3", ".flac", ".m4a", ".ogg"],
        help="지원할 오디오 확장자 (기본값: .wav .mp3 .flac .m4a .ogg)"
    )
    
    # 상세 출력 설정
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세한 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 언어 설정 처리
    language = None if args.language.lower() == "none" else args.language
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.single_file:
            # 단일 파일 처리
            output_path = process_single_file(
                args.single_file,
                args.output,
                args.model,
                language,
                args.device
            )
            print(f"✅ 전사 완료: {output_path}")
            
        elif args.input:
            # 디렉토리 처리
            process_directory(
                args.input,
                args.output,
                args.model,
                language,
                args.device,
                args.extensions
            )
            print(f"✅ 디렉토리 처리 완료: {args.output}")
            
    except FileNotFoundError as e:
        logging.error(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ 전사 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 명령행 인터페이스 활성화
    main()
    
    # 기존 코드는 주석 처리하고 사용 예시로 이동
    """
    # 예시: 디렉토리 일괄 처리
    process_directory(
        input_dir="data/denoised",
        output_dir="output/transcript",
        model_size="medium",
        language="ko"
    )
    
    # 예시: 단일 파일 처리
    process_single_file(
        input_path="audio.wav",
        output_dir="output/transcript",
        model_size="medium"
    )
    """
