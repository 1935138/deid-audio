import json
import numpy as np
import librosa
import soundfile as sf
import os
from typing import List, Tuple, Dict, Any
from pathlib import Path


def load_processed_json(json_path: str) -> Dict[str, Any]:
    """
    처리된 JSON 파일을 로드합니다.
    
    Args:
        json_path (str): JSON 파일 경로
        
    Returns:
        Dict[str, Any]: JSON 데이터
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_pii_segments(json_data: Dict[str, Any]) -> List[Tuple[float, float]]:
    """
    JSON 데이터에서 is_pii가 true인 단어의 시간 구간을 추출합니다.
    
    Args:
        json_data (Dict[str, Any]): 처리된 JSON 데이터
        
    Returns:
        List[Tuple[float, float]]: PII 구간 리스트 [(start_time, end_time), ...]
    """
    pii_segments = []
    
    for segment in json_data.get('segments', []):
        for word in segment.get('words', []):
            if word.get('is_pii', False):
                start_time = word.get('start', 0.0)
                end_time = word.get('end', 0.0)
                pii_segments.append((start_time, end_time))
                print(f"PII 구간 발견: {start_time:.2f}s - {end_time:.2f}s, 텍스트: '{word.get('word', '')}'")
    
    return pii_segments


def merge_overlapping_segments(segments: List[Tuple[float, float]], 
                              margin: float = 0.1) -> List[Tuple[float, float]]:
    """
    겹치거나 인접한 PII 구간들을 병합합니다.
    
    Args:
        segments (List[Tuple[float, float]]): PII 구간 리스트
        margin (float): 병합을 위한 여백 시간 (초)
        
    Returns:
        List[Tuple[float, float]]: 병합된 구간 리스트
    """
    if not segments:
        return []
    
    # 시작 시간으로 정렬
    sorted_segments = sorted(segments)
    merged = [sorted_segments[0]]
    
    for current_start, current_end in sorted_segments[1:]:
        last_start, last_end = merged[-1]
        
        # 현재 구간이 이전 구간과 겹치거나 margin 내에 있으면 병합
        if current_start <= last_end + margin:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
    
    return merged


def mute_audio_segments(audio_path: str, pii_segments: List[Tuple[float, float]], 
                       output_path: str) -> bool:
    """
    오디오 파일에서 PII 구간을 묵음 처리합니다.
    
    Args:
        audio_path (str): 입력 오디오 파일 경로
        pii_segments (List[Tuple[float, float]]): 묵음 처리할 구간 리스트
        output_path (str): 출력 오디오 파일 경로
        
    Returns:
        bool: 성공 여부
    """
    try:
        # 오디오 파일 로드
        audio, sr = librosa.load(audio_path, sr=None)
        print(f"오디오 로드 완료: {audio_path}")
        print(f"  - 샘플링 레이트: {sr} Hz")
        print(f"  - 길이: {len(audio)} 샘플 ({len(audio)/sr:.2f}초)")
        
        # PII 구간 묵음 처리
        audio_muted = audio.copy()
        total_muted_duration = 0.0
        
        for start_time, end_time in pii_segments:
            # 시간을 샘플 인덱스로 변환
            start_idx = int(start_time * sr)
            end_idx = int(end_time * sr)
            
            # 인덱스 범위 확인
            start_idx = max(0, start_idx)
            end_idx = min(len(audio), end_idx)
            
            if start_idx < end_idx:
                # 해당 구간을 0으로 설정 (묵음 처리)
                audio_muted[start_idx:end_idx] = 0.0
                duration = end_time - start_time
                total_muted_duration += duration
                print(f"  묵음 처리: {start_time:.2f}s - {end_time:.2f}s ({duration:.2f}초)")
        
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 묵음 처리된 오디오 저장
        sf.write(output_path, audio_muted, sr)
        print(f"묵음 처리된 오디오 저장 완료: {output_path}")
        print(f"총 묵음 처리 시간: {total_muted_duration:.2f}초")
        
        return True
        
    except Exception as e:
        print(f"오디오 묵음 처리 중 오류 발생: {e}")
        return False


def mask_text_in_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    JSON 데이터에서 is_pii가 true인 단어를 '***'로 치환합니다.
    
    Args:
        json_data (Dict[str, Any]): 원본 JSON 데이터
        
    Returns:
        Dict[str, Any]: 마스킹된 JSON 데이터
    """
    masked_data = json_data.copy()
    total_masked_count = 0
    
    # 전체 transcript 텍스트 업데이트를 위한 세그먼트 텍스트 수집
    updated_segments_text = []
    
    for segment in masked_data.get('segments', []):
        segment_text_parts = []
        
        for word in segment.get('words', []):
            if word.get('is_pii', False):
                # PII 단어를 '***'로 치환
                original_word = word.get('word', '')
                word['word'] = '***'
                total_masked_count += 1
                print(f"텍스트 마스킹: '{original_word}' → '***'")
                segment_text_parts.append('***')
            else:
                segment_text_parts.append(word.get('word', ''))
        
        # 세그먼트 텍스트 업데이트
        if segment_text_parts:
            segment['text'] = ''.join(segment_text_parts)
            updated_segments_text.append(segment['text'])
    
    # 전체 transcript 업데이트
    if updated_segments_text:
        masked_data['transcript'] = ' '.join(updated_segments_text)
    
    print(f"총 {total_masked_count}개의 PII 텍스트를 마스킹했습니다.")
    
    return masked_data


def process_pii_file(json_path: str, output_dir: str = "output/deid") -> bool:
    """
    PII가 포함된 JSON 파일을 처리하여 음성 묵음 처리와 텍스트 마스킹을 수행합니다.
    
    Args:
        json_path (str): 입력 JSON 파일 경로
        output_dir (str): 출력 디렉토리
        
    Returns:
        bool: 성공 여부
    """
    try:
        print(f"\n=== PII 처리 시작: {json_path} ===")
        
        # JSON 데이터 로드
        json_data = load_processed_json(json_path)
        audio_path = json_data.get('audio_file')
        
        if not audio_path or not os.path.exists(audio_path):
            print(f"오류: 오디오 파일을 찾을 수 없습니다 - {audio_path}")
            return False
        
        # PII 구간 추출
        pii_segments = extract_pii_segments(json_data)
        
        if not pii_segments:
            print("PII 구간이 발견되지 않았습니다.")
            return True
        
        print(f"총 {len(pii_segments)}개의 PII 구간 발견")
        
        # 겹치는 구간 병합
        merged_segments = merge_overlapping_segments(pii_segments)
        print(f"병합 후 {len(merged_segments)}개의 구간")
        
        # 출력 파일 경로 설정
        input_filename = Path(json_path).stem
        output_audio_path = os.path.join(output_dir, "audio", f"{input_filename}_deid.wav")
        output_json_path = os.path.join(output_dir, "json", f"{input_filename}_deid.json")
        
        # 오디오 묵음 처리
        print("\n--- 오디오 묵음 처리 ---")
        audio_success = mute_audio_segments(audio_path, merged_segments, output_audio_path)
        
        # 텍스트 마스킹
        print("\n--- 텍스트 마스킹 ---")
        masked_json_data = mask_text_in_json(json_data)
        
        # 마스킹된 JSON을 오디오 파일 경로로 업데이트
        masked_json_data['audio_file'] = output_audio_path
        
        # 마스킹된 JSON 저장
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(masked_json_data, f, ensure_ascii=False, indent=2)
        
        print(f"마스킹된 JSON 저장 완료: {output_json_path}")
        
        if audio_success:
            print(f"\n✅ PII 처리 완료!")
            print(f"  - 묵음 처리된 오디오: {output_audio_path}")
            print(f"  - 마스킹된 JSON: {output_json_path}")
            return True
        else:
            print(f"\n❌ 오디오 처리 실패")
            return False
            
    except Exception as e:
        print(f"PII 처리 중 오류 발생: {e}")
        return False


def process_directory(input_dir: str, output_dir: str = "output/deid") -> None:
    """
    디렉토리 내의 모든 처리된 JSON 파일에 대해 PII 처리를 수행합니다.
    
    Args:
        input_dir (str): 입력 디렉토리 (processed JSON 파일들이 있는 곳)
        output_dir (str): 출력 디렉토리
    """
    print(f"\n=== 디렉토리 PII 처리 시작: {input_dir} ===")
    
    if not os.path.exists(input_dir):
        print(f"오류: 입력 디렉토리를 찾을 수 없습니다 - {input_dir}")
        return
    
    # JSON 파일 목록 가져오기
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"경고: {input_dir}에 JSON 파일이 없습니다.")
        return
    
    print(f"처리할 JSON 파일 {len(json_files)}개 발견")
    
    success_count = 0
    for json_file in json_files:
        json_path = os.path.join(input_dir, json_file)
        
        try:
            if process_pii_file(json_path, output_dir):
                success_count += 1
        except Exception as e:
            print(f"파일 처리 실패 ({json_file}): {e}")
    
    print(f"\n=== 처리 완료: {success_count}/{len(json_files)}개 성공 ===")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='PII 구간 음성 묵음 처리 및 텍스트 마스킹')
    parser.add_argument('--input', '-i', required=True, 
                       help='입력 JSON 파일 또는 디렉토리 경로')
    parser.add_argument('--output', '-o', default='output/deid',
                       help='출력 디렉토리 (기본값: output/deid)')
    
    args = parser.parse_args()
    
    if os.path.isfile(args.input):
        # 단일 파일 처리
        process_pii_file(args.input, args.output)
    elif os.path.isdir(args.input):
        # 디렉토리 처리
        process_directory(args.input, args.output)
    else:
        print(f"오류: 유효하지 않은 입력 경로 - {args.input}")
