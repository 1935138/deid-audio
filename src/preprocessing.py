import librosa
import soundfile as sf
import noisereduce as nr
import numpy as np
import os
from pathlib import Path
from typing import List
import re
from pydub import AudioSegment
from pydub.utils import make_chunks
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def count_sentences(text: str) -> int:
    """
    텍스트에서 문장의 개수를 세는 함수
    
    Parameters:
        text (str): 분석할 텍스트
    
    Returns:
        int: 문장의 개수
    """
    # 문장 구분자: 마침표, 느낌표, 물음표로 끝나는 경우
    sentences = re.split('[.!?]+', text)
    # 빈 문자열 제거 후 개수 반환
    return len([s for s in sentences if s.strip()])

def should_add_dummy_data(text: str, is_first_chunk: bool) -> bool:
    """
    더미 데이터를 추가해야 하는지 확인하는 함수
    
    Parameters:
        text (str): 분석할 텍스트
        is_first_chunk (bool): 첫 번째 청크인지 여부
    
    Returns:
        bool: 더미 데이터 추가 여부
    """
    # 첫 번째 청크이면서 문장이 5개 이하일 때만 True 반환
    return is_first_chunk and count_sentences(text) <= 5

def normalize_volume(audio_segment: AudioSegment, target_dBFS: float = -20.0) -> AudioSegment:
    """
    오디오의 볼륨을 정규화하는 함수
    
    Parameters:
        audio_segment (AudioSegment): 정규화할 오디오 세그먼트
        target_dBFS (float): 목표 dBFS 값
    
    Returns:
        AudioSegment: 볼륨이 정규화된 오디오 세그먼트
    """
    change_in_dBFS = target_dBFS - audio_segment.dBFS
    normalized_audio = audio_segment.apply_gain(change_in_dBFS)
    
    logging.info(f"볼륨 정규화: {audio_segment.dBFS:.2f} dBFS -> {normalized_audio.dBFS:.2f} dBFS")
    return normalized_audio

def preprocess_audio_pydub(input_path: str, output_path: str, target_dBFS: float = -20.0) -> bool:
    """
    pydub을 사용한 오디오 전처리 (로드 -> 볼륨 정규화 -> 저장)
    
    Parameters:
        input_path (str): 입력 오디오 파일 경로
        output_path (str): 출력 오디오 파일 경로
        target_dBFS (float): 목표 볼륨 레벨 (dBFS)
    
    Returns:
        bool: 처리 성공 여부
    """
    try:
        logging.info(f"pydub으로 오디오 전처리 시작: {input_path}")
        
        # 1. 원본 오디오 로드
        audio = AudioSegment.from_file(input_path)
        
        # 오디오 정보 로깅
        logging.info(f"원본 오디오 정보: {audio.frame_rate}Hz, {audio.channels}ch, {len(audio)}ms, {audio.dBFS:.2f}dBFS")
        
        # 2. 모노로 변환 (필요한 경우)
        if audio.channels > 1:
            audio = audio.set_channels(1)
            logging.info("스테레오를 모노로 변환")
        
        # 3. 샘플레이트 정규화 (16kHz가 일반적)
        if audio.frame_rate != 16000:
            audio = audio.set_frame_rate(16000)
            logging.info(f"샘플레이트를 16kHz로 변환")
        
        # 4. 볼륨 정규화
        normalized_audio = normalize_volume(audio, target_dBFS)
        
        # 5. 저장
        normalized_audio.export(output_path, format="wav")
        logging.info(f"전처리된 오디오 저장 완료: {output_path}")
        
        return True
        
    except Exception as e:
        logging.error(f"pydub 전처리 오류: {str(e)}")
        return False

def reduce_noise_advanced(input_path: str, output_path: str, 
                         noise_clip_duration: float = 2.0, 
                         target_dBFS: float = -20.0,
                         use_pydub_preprocessing: bool = True) -> bool:
    """
    고급 오디오 전처리: 노이즈 제거 + 볼륨 정규화
    
    Parameters:
        input_path (str): 입력 오디오 파일 경로
        output_path (str): 출력 오디오 파일 경로
        noise_clip_duration (float): 노이즈 샘플로 사용할 오디오 시작 부분의 길이(초)
        target_dBFS (float): 목표 볼륨 레벨 (dBFS)
        use_pydub_preprocessing (bool): pydub을 사용한 전처리 여부
    
    Returns:
        bool: 처리 성공 여부
    """
    try:
        logging.info(f"고급 오디오 전처리 시작: {input_path}")
        
        if use_pydub_preprocessing:
            # 1단계: pydub을 사용한 기본 전처리
            temp_path = output_path.replace('.wav', '_temp.wav')
            if not preprocess_audio_pydub(input_path, temp_path, target_dBFS):
                return False
            input_for_denoise = temp_path
        else:
            input_for_denoise = input_path
        
        # 2단계: librosa + noisereduce를 사용한 노이즈 제거
        logging.info("노이즈 제거 시작 (librosa + noisereduce)")
        
        # 오디오 파일 로드
        audio_data, sample_rate = librosa.load(input_for_denoise, sr=None)
        
        # 오디오 시작 부분에서 노이즈 샘플 추출
        noise_clip = audio_data[:int(noise_clip_duration * sample_rate)]
        
        # 노이즈 제거 수행
        reduced_noise = nr.reduce_noise(
            y=audio_data,
            sr=sample_rate,
            y_noise=noise_clip,
            stationary=True,
            prop_decrease=0.8  # 1.0에서 0.8로 조정하여 과도한 제거 방지
        )
        
        # 3단계: 최종 볼륨 정규화 (pydub 사용)
        logging.info("최종 볼륨 정규화")
        
        # numpy 배열을 AudioSegment로 변환
        # 16-bit PCM으로 변환
        audio_int16 = (reduced_noise * 32767).astype(np.int16)
        
        final_audio = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit = 2 bytes
            channels=1
        )
        
        # 최종 볼륨 정규화
        final_normalized = normalize_volume(final_audio, target_dBFS)
        
        # 4단계: 최종 저장
        final_normalized.export(output_path, format="wav")
        
        # 임시 파일 정리
        if use_pydub_preprocessing and os.path.exists(temp_path):
            os.remove(temp_path)
        
        logging.info(f"고급 전처리 완료: {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"고급 전처리 오류: {str(e)}")
        return False

def reduce_noise(input_path, output_path, noise_clip_duration=2.0):
    """
    기존 노이즈 제거 함수 (하위 호환성 유지)
    """
    return reduce_noise_advanced(input_path, output_path, noise_clip_duration, use_pydub_preprocessing=False)

def process_directory(input_dir: str, output_dir: str, 
                     noise_clip_duration: float = 2.0, 
                     target_dBFS: float = -20.0,
                     use_advanced_processing: bool = True) -> None:
    """
    지정된 디렉토리 내의 모든 오디오 파일에 대해 고급 전처리를 수행하는 함수
    
    Parameters:
        input_dir (str): 입력 오디오 파일들이 있는 디렉토리 경로
        output_dir (str): 처리된 오디오 파일들을 저장할 디렉토리 경로
        noise_clip_duration (float): 노이즈 샘플로 사용할 오디오 시작 부분의 길이(초)
        target_dBFS (float): 목표 볼륨 레벨 (dBFS)
        use_advanced_processing (bool): 고급 전처리 사용 여부
    """
    # 지원하는 오디오 파일 확장자
    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
    
    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 입력 디렉토리의 모든 파일 처리
    input_path = Path(input_dir)
    successful_count = 0
    failed_count = 0
    
    # 오디오 파일 목록 수집
    audio_files = [f for f in input_path.rglob('*') if f.suffix.lower() in AUDIO_EXTENSIONS]
    
    logging.info(f"총 {len(audio_files)}개의 오디오 파일을 처리합니다.")
    logging.info(f"설정: 노이즈 클립 길이={noise_clip_duration}s, 목표 볼륨={target_dBFS}dBFS, 고급 처리={use_advanced_processing}")
    
    for idx, audio_file in enumerate(audio_files):
        # 출력 파일 경로 생성
        relative_path = audio_file.relative_to(input_path)
        output_path = Path(output_dir) / relative_path.with_suffix('.wav')  # 항상 wav로 저장
        
        # 출력 파일의 디렉토리가 없으면 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"\n[{idx + 1}/{len(audio_files)}] 처리 중: {audio_file}")
        
        # 처리 방법 선택
        if use_advanced_processing:
            success = reduce_noise_advanced(
                str(audio_file), 
                str(output_path), 
                noise_clip_duration, 
                target_dBFS
            )
        else:
            success = reduce_noise(str(audio_file), str(output_path), noise_clip_duration)
        
        if success:
            successful_count += 1
            logging.info(f"✅ 성공: {output_path}")
        else:
            failed_count += 1
            logging.error(f"❌ 실패: {audio_file}")
    
    # 처리 결과 출력
    logging.info(f"\n🎯 처리 완료 요약:")
    logging.info(f"✅ 성공: {successful_count} 파일")
    logging.info(f"❌ 실패: {failed_count} 파일")
    logging.info(f"📁 출력 디렉토리: {output_dir}")

def process_single_file(input_path: str, output_path: str, 
                       noise_clip_duration: float = 2.0, 
                       target_dBFS: float = -20.0) -> bool:
    """
    단일 파일에 대한 고급 전처리 수행
    
    Parameters:
        input_path (str): 입력 오디오 파일 경로
        output_path (str): 출력 오디오 파일 경로
        noise_clip_duration (float): 노이즈 샘플 길이 (초)
        target_dBFS (float): 목표 볼륨 레벨
    
    Returns:
        bool: 처리 성공 여부
    """
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    return reduce_noise_advanced(input_path, output_path, noise_clip_duration, target_dBFS)

if __name__ == "__main__":
    # 사용 예시
    import argparse
    
    parser = argparse.ArgumentParser(description='오디오 노이즈 제거 및 볼륨 정규화')
    parser.add_argument('--input', '-i', default='data/raw', help='입력 디렉토리 경로')
    parser.add_argument('--output', '-o', default='data/preprocessed', help='출력 디렉토리 경로')
    parser.add_argument('--noise-duration', '-n', type=float, default=2.0, help='노이즈 샘플 길이 (초)')
    parser.add_argument('--target-volume', '-v', type=float, default=-20.0, help='목표 볼륨 (dBFS)')
    parser.add_argument('--basic', action='store_true', help='기본 처리만 사용 (고급 처리 비활성화)')
    parser.add_argument('--single-file', '-f', help='단일 파일 처리 (입력 파일 경로)')
    parser.add_argument('--single-output', help='단일 파일 출력 경로 (--single-file과 함께 사용)')
    
    args = parser.parse_args()
    
    if args.single_file:
        # 단일 파일 처리
        output_path = args.single_output or args.single_file.replace('.', '_processed.')
        success = process_single_file(
            args.single_file, 
            output_path, 
            args.noise_duration, 
            args.target_volume
        )
        if success:
            print(f"✅ 단일 파일 처리 완료: {output_path}")
        else:
            print(f"❌ 단일 파일 처리 실패: {args.single_file}")
    else:
        # 디렉토리 처리
        process_directory(
            args.input, 
            args.output, 
            args.noise_duration, 
            args.target_volume, 
            not args.basic
        )
    
    # 추가 사용 예시 (주석 처리)
    """
    # 예시 1: 기본 사용
    process_directory("data/raw", "data/preprocessed")
    
    # 예시 2: 커스텀 설정
    process_directory(
        input_dir="data/raw",
        output_dir="data/preprocessed", 
        noise_clip_duration=3.0,
        target_dBFS=-18.0,
        use_advanced_processing=True
    )
    
    # 예시 3: 단일 파일 처리
    process_single_file(
        "input.wav", 
        "output_preprocessed.wav",
        noise_clip_duration=2.0,
        target_dBFS=-20.0
    )
    
    # 예시 4: pydub만 사용한 간단한 전처리
    preprocess_audio_pydub("input.wav", "output_normalized.wav", target_dBFS=-20.0)
    """
