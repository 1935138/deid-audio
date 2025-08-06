#!/usr/bin/env python3
"""
오디오 전처리 사용 예시
노이즈 제거 + 볼륨 정규화 기능 시연
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from noise_reduce import (
    preprocess_audio_pydub,
    reduce_noise_advanced,
    process_single_file,
    process_directory
)

def example_1_simple_volume_normalization():
    """
    예시 1: 간단한 볼륨 정규화만 수행
    """
    print("\n=== 예시 1: 간단한 볼륨 정규화 ===")
    
    input_file = "data/raw/sample.wav"
    output_file = "data/normalized/sample_normalized.wav"
    
    # pydub만 사용한 간단한 전처리
    success = preprocess_audio_pydub(
        input_path=input_file,
        output_path=output_file,
        target_dBFS=-20.0  # 목표 볼륨 레벨
    )
    
    if success:
        print(f"✅ 볼륨 정규화 완료: {output_file}")
    else:
        print(f"❌ 처리 실패: {input_file}")

def example_2_full_preprocessing():
    """
    예시 2: 노이즈 제거 + 볼륨 정규화 (고급 처리)
    """
    print("\n=== 예시 2: 노이즈 제거 + 볼륨 정규화 ===")
    
    input_file = "data/raw/sample.wav"
    output_file = "data/preprocessed/sample_full_processed.wav"
    
    # 고급 전처리: 노이즈 제거 + 볼륨 정규화
    success = reduce_noise_advanced(
        input_path=input_file,
        output_path=output_file,
        noise_clip_duration=2.0,  # 노이즈 샘플 길이
        target_dBFS=-20.0,        # 목표 볼륨
        use_pydub_preprocessing=True  # pydub 전처리 사용
    )
    
    if success:
        print(f"✅ 고급 전처리 완료: {output_file}")
    else:
        print(f"❌ 처리 실패: {input_file}")

def example_3_single_file_processing():
    """
    예시 3: 단일 파일 처리 (편의 함수 사용)
    """
    print("\n=== 예시 3: 단일 파일 처리 ===")
    
    input_file = "data/raw/sample.wav"
    output_file = "data/processed/sample_processed.wav"
    
    success = process_single_file(
        input_path=input_file,
        output_path=output_file,
        noise_clip_duration=3.0,  # 더 긴 노이즈 샘플
        target_dBFS=-18.0         # 더 높은 볼륨
    )
    
    if success:
        print(f"✅ 단일 파일 처리 완료: {output_file}")
    else:
        print(f"❌ 처리 실패: {input_file}")

def example_4_directory_processing():
    """
    예시 4: 디렉토리 일괄 처리
    """
    print("\n=== 예시 4: 디렉토리 일괄 처리 ===")
    
    input_dir = "data/raw"
    output_dir = "data/batch_processed"
    
    process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        noise_clip_duration=2.0,
        target_dBFS=-20.0,
        use_advanced_processing=True
    )
    
    print(f"✅ 디렉토리 일괄 처리 완료: {output_dir}")

def example_5_custom_settings():
    """
    예시 5: 커스텀 설정으로 처리
    """
    print("\n=== 예시 5: 커스텀 설정 처리 ===")
    
    # 조용한 환경용 설정 (높은 볼륨, 짧은 노이즈 샘플)
    quiet_settings = {
        "noise_clip_duration": 1.0,
        "target_dBFS": -15.0
    }
    
    # 시끄러운 환경용 설정 (낮은 볼륨, 긴 노이즈 샘플)
    noisy_settings = {
        "noise_clip_duration": 3.0,
        "target_dBFS": -25.0
    }
    
    input_file = "data/raw/sample.wav"
    
    # 조용한 환경용 처리
    success1 = process_single_file(
        input_file, 
        "data/custom/sample_quiet_env.wav",
        **quiet_settings
    )
    
    # 시끄러운 환경용 처리
    success2 = process_single_file(
        input_file,
        "data/custom/sample_noisy_env.wav", 
        **noisy_settings
    )
    
    if success1 and success2:
        print("✅ 커스텀 설정 처리 완료")
    else:
        print("❌ 일부 처리 실패")

def example_6_batch_with_different_formats():
    """
    예시 6: 다양한 포맷 파일 일괄 처리
    """
    print("\n=== 예시 6: 다양한 포맷 일괄 처리 ===")
    
    # 다양한 포맷(.mp3, .wav, .flac 등)이 있는 디렉토리 처리
    # 모든 출력은 .wav로 통일됨
    
    process_directory(
        input_dir="data/mixed_formats",
        output_dir="data/unified_wav",
        noise_clip_duration=2.0,
        target_dBFS=-20.0,
        use_advanced_processing=True
    )
    
    print("✅ 다양한 포맷 일괄 처리 완료 (모두 WAV로 변환)")

if __name__ == "__main__":
    print("🎵 오디오 전처리 예시 실행")
    print("=" * 50)
    
    # 모든 예시 실행
    try:
        example_1_simple_volume_normalization()
        example_2_full_preprocessing()
        example_3_single_file_processing()
        example_4_directory_processing()
        example_5_custom_settings()
        example_6_batch_with_different_formats()
        
        print("\n🎯 모든 예시 실행 완료!")
        
    except FileNotFoundError as e:
        print(f"\n⚠️  파일을 찾을 수 없습니다: {e}")
        print("실제 오디오 파일 경로로 변경하여 테스트하세요.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
