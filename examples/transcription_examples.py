#!/usr/bin/env python3
"""
음성 전사 사용 예시
faster-whisper를 이용한 다양한 전사 시나리오 시연
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcription import (
    transcribe_audio,
    process_directory,
    process_single_file,
    load_whisper_model
)

def example_1_single_file_basic():
    """
    예시 1: 기본 단일 파일 전사
    """
    print("\n=== 예시 1: 기본 단일 파일 전사 ===")
    
    input_file = "data/audio/sample.wav"
    output_dir = "output/transcript_basic"
    
    try:
        output_path = transcribe_audio(
            audio_file_path=input_file,
            model_size="medium",        # 중간 크기 모델
            output_dir=output_dir,
            language="ko",              # 한국어
            verbose=True                # 상세 출력
        )
        print(f"✅ 전사 완료: {output_path}")
    except Exception as e:
        print(f"❌ 전사 실패: {e}")

def example_2_english_transcription():
    """
    예시 2: 영어 전사
    """
    print("\n=== 예시 2: 영어 전사 ===")
    
    input_file = "data/audio/english_sample.wav"
    output_dir = "output/transcript_english"
    
    try:
        output_path = transcribe_audio(
            audio_file_path=input_file,
            model_size="large-v3",      # 대형 모델 (정확도 우선)
            output_dir=output_dir,
            language="en",              # 영어
            device="cuda",              # GPU 강제 사용
            verbose=True
        )
        print(f"✅ 영어 전사 완료: {output_path}")
    except Exception as e:
        print(f"❌ 영어 전사 실패: {e}")

def example_3_auto_language_detection():
    """
    예시 3: 자동 언어 감지
    """
    print("\n=== 예시 3: 자동 언어 감지 ===")
    
    input_file = "data/audio/multilingual.wav"
    output_dir = "output/transcript_auto"
    
    try:
        output_path = transcribe_audio(
            audio_file_path=input_file,
            model_size="medium",
            output_dir=output_dir,
            language=None,              # 자동 감지
            verbose=True
        )
        print(f"✅ 자동 감지 전사 완료: {output_path}")
    except Exception as e:
        print(f"❌ 자동 감지 전사 실패: {e}")

def example_4_fast_transcription():
    """
    예시 4: 빠른 전사 (작은 모델)
    """
    print("\n=== 예시 4: 빠른 전사 ===")
    
    input_file = "data/audio/quick_test.wav"
    output_dir = "output/transcript_fast"
    
    try:
        output_path = transcribe_audio(
            audio_file_path=input_file,
            model_size="tiny",          # 최소 모델 (속도 우선)
            output_dir=output_dir,
            language="ko",
            verbose=False               # 조용한 처리
        )
        print(f"✅ 빠른 전사 완료: {output_path}")
    except Exception as e:
        print(f"❌ 빠른 전사 실패: {e}")

def example_5_directory_batch_processing():
    """
    예시 5: 디렉토리 일괄 처리
    """
    print("\n=== 예시 5: 디렉토리 일괄 처리 ===")
    
    input_dir = "data/audio_batch"
    output_dir = "output/transcript_batch"
    
    try:
        process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            model_size="medium",
            language="ko",
            device=None,                # 자동 장치 선택
            audio_extensions=[".wav", ".mp3", ".m4a"]  # 지원 포맷
        )
        print(f"✅ 디렉토리 일괄 처리 완료: {output_dir}")
    except Exception as e:
        print(f"❌ 일괄 처리 실패: {e}")

def example_6_custom_model_reuse():
    """
    예시 6: 모델 재사용 (성능 최적화)
    """
    print("\n=== 예시 6: 모델 재사용 최적화 ===")
    
    # 모델을 한 번만 로드
    try:
        model = load_whisper_model("medium", device="cuda")
        print("🚀 모델 로딩 완료")
        
        # 여러 파일에 동일 모델 사용
        audio_files = [
            "data/audio/file1.wav",
            "data/audio/file2.wav", 
            "data/audio/file3.wav"
        ]
        
        for i, audio_file in enumerate(audio_files, 1):
            try:
                print(f"\n[{i}/{len(audio_files)}] 처리 중: {audio_file}")
                # 실제 구현에서는 transcribe_audio_with_model 사용
                # 여기서는 개념적 예시
                print(f"✅ 파일 {i} 전사 완료")
            except Exception as e:
                print(f"❌ 파일 {i} 전사 실패: {e}")
                
    except Exception as e:
        print(f"❌ 모델 로딩 실패: {e}")

def example_7_mixed_format_processing():
    """
    예시 7: 다양한 포맷 파일 처리
    """
    print("\n=== 예시 7: 다양한 포맷 처리 ===")
    
    files_and_formats = [
        ("data/audio/speech.wav", "WAV 파일"),
        ("data/audio/podcast.mp3", "MP3 파일"),
        ("data/audio/interview.m4a", "M4A 파일"),
        ("data/audio/meeting.flac", "FLAC 파일")
    ]
    
    for audio_file, file_type in files_and_formats:
        try:
            print(f"\n🔄 {file_type} 처리 중...")
            output_path = process_single_file(
                input_path=audio_file,
                output_dir="output/transcript_mixed",
                model_size="medium",
                language="ko"
            )
            print(f"✅ {file_type} 전사 완료: {output_path}")
        except Exception as e:
            print(f"❌ {file_type} 전사 실패: {e}")

def example_8_production_pipeline():
    """
    예시 8: 프로덕션 파이프라인 시뮬레이션
    """
    print("\n=== 예시 8: 프로덕션 파이프라인 ===")
    
    # 1단계: 전처리된 오디오 디렉토리
    preprocessed_dir = "data/preprocessed"
    
    # 2단계: 전사 설정
    transcription_config = {
        "model_size": "large-v3",   # 높은 정확도
        "language": "ko",
        "device": "cuda",           # GPU 사용
        "output_dir": "output/production"
    }
    
    try:
        print("🚀 프로덕션 파이프라인 시작...")
        
        # 디렉토리 일괄 처리
        process_directory(
            input_dir=preprocessed_dir,
            **transcription_config
        )
        
        print("✅ 프로덕션 파이프라인 완료!")
        print(f"📁 결과 위치: {transcription_config['output_dir']}")
        
    except Exception as e:
        print(f"❌ 프로덕션 파이프라인 실패: {e}")

if __name__ == "__main__":
    print("🎙️ 음성 전사 예시 실행")
    print("=" * 50)
    
    # 모든 예시 실행
    try:
        example_1_single_file_basic()
        example_2_english_transcription()
        example_3_auto_language_detection()
        example_4_fast_transcription()
        example_5_directory_batch_processing()
        example_6_custom_model_reuse()
        example_7_mixed_format_processing()
        example_8_production_pipeline()
        
        print("\n🎯 모든 예시 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예시 실행 중 오류: {e}")
        print("실제 오디오 파일 경로로 변경하여 테스트하세요.")
