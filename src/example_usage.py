#!/usr/bin/env python3
"""
de_identification 함수 사용 예시
"""

import os
from audio_transcript_info import AudioTranscriptInfo
from extract_v0_2 import extract_pii_from_json, de_identification

def process_transcript_file(json_file_path: str, output_dir: str = "output/processed"):
    """
    전사 파일에서 PII를 식별하고 is_pii 플래그를 설정하는 함수
    
    Args:
        json_file_path: 전사된 JSON 파일 경로
        output_dir: 처리된 결과를 저장할 디렉토리
    """
    
    print(f"▶ 처리 대상: {json_file_path}")
    
    # 1. JSON 파일에서 PII 추출
    print("  1. PII 추출 중...")
    pii_sentences = extract_pii_from_json(json_file_path)
    print(f"     - 발견된 PII 문장 수: {len(pii_sentences.pii_sentences)}")
    
    # 2. AudioTranscriptInfo 객체 생성 및 데이터 로드
    print("  2. 전사 정보 로드 중...")
    audio_info = AudioTranscriptInfo("dummy_audio_path")  # 실제 오디오 파일 경로는 JSON에서 로드됨
    
    if not audio_info.load_from_json(json_file_path):
        print("     ❌ JSON 파일 로드 실패")
        return None
    
    print(f"     - 세그먼트 수: {len(audio_info.segments)}")
    
    # 3. PII 식별 및 is_pii 플래그 설정
    print("  3. PII 플래그 설정 중...")
    processed_audio_info = de_identification(audio_info, pii_sentences)
    
    # PII가 설정된 단어 개수 확인
    pii_word_count = 0
    for segment in processed_audio_info.segments:
        for word in segment.words:
            if word.is_pii:
                pii_word_count += 1
    
    print(f"     - PII 플래그가 설정된 단어 수: {pii_word_count}")
    
    # 4. 결과 저장
    print("  4. 결과 저장 중...")
    output_path = processed_audio_info.save_to_json(output_dir)
    print(f"     ✅ 저장 완료: {output_path}")
    
    return output_path

def process_all_transcripts(input_dir: str = "output/transcript", output_dir: str = "output/processed"):
    """
    디렉토리 내의 모든 전사 파일을 처리
    """
    if not os.path.exists(input_dir):
        print(f"❌ 입력 디렉토리가 존재하지 않습니다: {input_dir}")
        return
    
    processed_files = []
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".json"):
                full_path = os.path.join(root, file)
                try:
                    result_path = process_transcript_file(full_path, output_dir)
                    if result_path:
                        processed_files.append(result_path)
                except Exception as e:
                    print(f"❌ 파일 처리 중 오류 발생 ({full_path}): {e}")
    
    print(f"\n📊 처리 완료: {len(processed_files)}개 파일")
    for path in processed_files:
        print(f"   - {path}")

if __name__ == "__main__":
    # 단일 파일 처리 예시
    # process_transcript_file("output/transcript/sample.json")
    
    # 전체 디렉토리 처리 예시
    process_all_transcripts()