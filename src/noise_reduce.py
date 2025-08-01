import librosa
import soundfile as sf
import noisereduce as nr
import numpy as np
import os
from pathlib import Path
from typing import List
import re

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

def reduce_noise(input_path, output_path, noise_clip_duration=2.0):
    """
    오디오 파일의 노이즈를 제거하는 함수
    
    Parameters:
        input_path (str): 입력 오디오 파일 경로
        output_path (str): 출력 오디오 파일 경로
        noise_clip_duration (float): 노이즈 샘플로 사용할 오디오 시작 부분의 길이(초)
    """
    try:
        # 오디오 파일 로드
        audio_data, sample_rate = librosa.load(input_path, sr=None)
        
        # 오디오 시작 부분에서 노이즈 샘플 추출
        noise_clip = audio_data[:int(noise_clip_duration * sample_rate)]
        
        # 노이즈 제거 수행
        reduced_noise = nr.reduce_noise(
            y=audio_data,
            sr=sample_rate,
            y_noise=noise_clip,
            stationary=True,
            prop_decrease=1.0
        )
        
        # 처리된 오디오 저장
        sf.write(output_path, reduced_noise, sample_rate)
        print(f"노이즈가 제거된 오디오가 {output_path}에 저장되었습니다.")
        return True
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

def process_directory(input_dir, output_dir, noise_clip_duration=2.0):
    """
    지정된 디렉토리 내의 모든 오디오 파일에 대해 노이즈 제거를 수행하는 함수
    
    Parameters:
        input_dir (str): 입력 오디오 파일들이 있는 디렉토리 경로
        output_dir (str): 처리된 오디오 파일들을 저장할 디렉토리 경로
        noise_clip_duration (float): 노이즈 샘플로 사용할 오디오 시작 부분의 길이(초)
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
    
    for idx, audio_file in enumerate(audio_files):
        # 출력 파일 경로 생성
        relative_path = audio_file.relative_to(input_path)
        output_path = Path(output_dir) / relative_path
        
        # 출력 파일의 디렉토리가 없으면 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n처리 중: {audio_file}")
        print(f"청크 번호: {idx + 1}/{len(audio_files)}")
        
        # 노이즈 제거 수행
        if reduce_noise(str(audio_file), str(output_path), noise_clip_duration):
            successful_count += 1
        else:
            failed_count += 1
    
    # 처리 결과 출력
    print(f"\n처리 완료:")
    print(f"성공: {successful_count} 파일")
    print(f"실패: {failed_count} 파일")

if __name__ == "__main__":
    process_directory("data/raw", "data/denoised")
