import json
from optparse import Option
import requests
import re
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Set
from audio_transcript_info import AudioTranscriptInfo
from enum import Enum

class PIISentence(BaseModel):
    sentence_id: int = Field(description="개인정보가 포함된 문장의 번호")
    pii_type: Optional[str] = Field(default=None, description="개인정보의 유형; NAME, RRN, PHONE, ADDRESS")
    pii_text: List[str] = Field(description="문장 전체가 아니라 개인정보 구간 정확히 추출")

class PIISentences(BaseModel):
    pii_sentences: List[PIISentence]

def format_transcript_text(json_data):
    json_data = json.loads(json_data)
    segments = json_data['segments']
    formatted_lines = []
    for segment in segments:
        formatted_lines.append(f"[{segment['id']}] {segment['text']}")
    return "\n".join(formatted_lines)

def format_json_file(json_file_path):
    with open(json_file_path, 'r') as file:
        json_data = file.read()
    formatted_text = format_transcript_text(json_data)
    return formatted_text


def de_identification(audio_transcript_info: AudioTranscriptInfo, pii_sentences: PIISentences):
    """
    오디오 전사 정보에서 개인정보를 비식별화 처리
    세그먼트 단위와 단어 단위 모두 정교하게 처리
    """
    for pii_sentence in pii_sentences.pii_sentences:
        for segment in audio_transcript_info.segments:
            if pii_sentence.sentence_id == int(segment.id):
                # 각 PII 텍스트에 대해 처리
                for pii_text in pii_sentence.pii_text:
                    if not pii_text.strip():
                        continue
                    
                    # 1. 세그먼트 텍스트에서 PII 부분만 마스킹
                    segment.text = mask_pii_in_text(segment.text, pii_text)
                    
                    # 2. 단어 단위에서 PII 처리
                    mask_pii_in_words(segment.words, pii_text, pii_sentence.pii_type)
                
                break
    return audio_transcript_info


def mask_pii_in_text(text: str, pii_text: str) -> str:
    """
    텍스트에서 PII 부분만 마스킹하는 함수
    대소문자 구분 없이 처리하고, 공백과 구두점을 고려함
    """
    if not pii_text.strip():
        return text
    
    # 정확한 매칭을 위해 정규식 사용
    # 특수문자를 이스케이프하고 공백을 유연하게 처리
    escaped_pii = re.escape(pii_text.strip())
    pattern = re.sub(r'\\ ', r'\\s*', escaped_pii)  # 공백을 유연하게 매칭
    
    def replace_with_mask(match):
        return "*" * len(match.group())
    
    # 대소문자 구분 없이 매칭
    result = re.sub(pattern, replace_with_mask, text, flags=re.IGNORECASE)
    return result


def mask_pii_in_words(words: List, pii_text: str, pii_type: Optional[str]):
    """
    단어 레벨에서 PII를 마스킹하는 함수
    단어가 여러 개로 분리된 경우를 고려하여 처리
    """
    if not words or not pii_text.strip():
        return
    
    pii_text = pii_text.strip()
    
    # 1. 완전 매칭 우선 처리
    for word in words:
        if word.word.strip().lower() == pii_text.lower():
            word.word = "*" * len(word.word)
            word.pii_type = pii_type
    
    # 2. 부분 매칭 처리 (PII가 단어에 포함된 경우)
    for word in words:
        if pii_text.lower() in word.word.lower() and word.word != "*" * len(word.word):
            word.word = "*" * len(word.word)
            word.pii_type = pii_type
    
    # 3. 연속된 단어들로 구성된 PII 처리 (예: "김철수"가 "김", "철수"로 분리된 경우)
    mask_consecutive_words_for_pii(words, pii_text, pii_type)


def mask_consecutive_words_for_pii(words: List, pii_text: str, pii_type: Optional[str]):
    """
    연속된 단어들이 합쳐져서 PII를 구성하는 경우를 처리
    예: "김철수"가 "김", "철수"로 분리된 경우
    """
    if len(words) < 2:
        return
    
    pii_text_cleaned = re.sub(r'\s+', '', pii_text.lower())  # 공백 제거
    
    # 슬라이딩 윈도우 방식으로 연속된 단어들 확인
    for i in range(len(words)):
        for j in range(i + 1, min(i + 5, len(words) + 1)):  # 최대 5개 단어까지 확인
            # 연속된 단어들을 합쳐서 확인
            combined_text = ''.join([w.word.strip() for w in words[i:j]]).lower()
            combined_text = re.sub(r'[^\w가-힣]', '', combined_text)  # 특수문자 제거
            
            if combined_text and combined_text in pii_text_cleaned:
                # 해당 구간의 모든 단어를 마스킹
                for k in range(i, j):
                    if words[k].word.strip() and words[k].word != "*" * len(words[k].word):
                        words[k].word = "*" * len(words[k].word)
                        words[k].pii_type = pii_type
                break


def extract_pii(text):
    vllm_host = "http://localhost:8000"
    # url = f"{vllm_host}/v1/completions"
    url = f"{vllm_host}/v1/chat/completions"

    # System role: 페르소나, 작업 정의, 출력 규칙
    system_message = f"""당신은 의료 대화에서 개인정보를 식별하는 전문가입니다.

작업 정의:
1. 다음 항목 중 하나라도 명시적으로 언급된 문장을 문맥을 고려하여 찾아내세요:
   - 이름 (NAME)
   - 주민등록번호 (RRN)
   - 전화번호 (PHONE)
   - 주소, 거주지, 사는 곳 (ADDRESS)
   - 생년월일, 생년, 생일 (BIRTHDAY)

2. 다음과 같은 경우는 개인정보로 간주하지 마세요:
   - 단순한 건강 수치 정보: 혈압, 혈당, 키/몸무게, 체온, 나이 등
   - 예: "혈압은 130에 90입니다", "나이는 65세입니다" 등의 문장은 제외
   - 항목 이름만 언급된 경우: "전화번호 알려주세요", "성함이 어떻게 되세요?" 등

3. pii_type 필드는 개인정보의 유형을 나타냅니다: NAME, RRN, PHONE, ADDRESS, BIRTHDAY

4. pii_text 필드는 문장 전체가 아니라 **개인정보 내용만** 정확히 추출합니다.

출력 규칙:
- 반드시 아래 JSON 스키마를 준수하세요
- 개인정보가 없다면 빈 배열로 응답: {{"pii_sentences": []}}
- Chinese character 사용 금지

JSON 스키마:
{PIISentences.model_json_schema()}"""

    # Assistant role: Few-shot 예시 (성공 사례와 빈 결과 사례 모두 포함)
    assistant_message = """### 개인정보 추출 예시 ###

예시 1 - 개인정보가 있는 경우:
입력:
[45] 부산시 사하구에 살아요
[46] 제 이름은 김철수입니다  
[47] 주민등록번호는 901231-1234567이에요

출력:
{
  "pii_sentences": [
    {
      "sentence_id": 45,
      "pii_type": "ADDRESS", 
      "pii_text": ["부산시 사하구"]
    },
    {
      "sentence_id": 46,
      "pii_type": "NAME",
      "pii_text": ["김철수"]
    },
    {
      "sentence_id": 47, 
      "pii_type": "RRN",
      "pii_text": ["901231-1234567"]
    }
  ]
}

예시 2 - 개인정보가 없는 경우:
입력:
[100] 혈압이 어떻게 되세요?
[101] 좀 높은 편이에요.
[102] 약을 처방해드릴게요.

출력:
{
  "pii_sentences": []
}

### 예시 종료 ###"""

    # User role: 실제 분석 대상
    user_message = f"""아래는 환자와 의료진의 대화입니다. 각 문장에는 번호가 붙어 있습니다.

대화 내용:
{text}"""

    headers = {"Content-Type": "application/json"}

    data = {
        # "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        # "model": "LGAI-EXAONE/EXAONE-4.0-1.2B",
        "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "assistant", "content": assistant_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1024,
        "temperature": 0,
        "stream": False,
        "response_format": {
            "type": "json_object"
        }
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    try:
        result = result['choices'][0]['message']['content']
    except:
        result = result
    return result

def extract_pii_from_json(json_file_path: str) -> PIISentences:
    """
    JSON 파일에서 PII 정보를 추출합니다.
    50개의 문장씩 슬라이딩 윈도우 방식으로 처리하며,
    시작 인덱스를 45씩 이동하여 5개의 문장이 중복되도록 합니다.
    """
    # JSON 파일 읽기
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)

    segments = json_data['segments']
    all_pii_sentences: Dict[int, PIISentence] = {}  # 중복 제거를 위한 딕셔너리
    
    # 슬라이딩 윈도우로 처리
    window_size = 50
    slide_size = 47
    
    for start_idx in range(0, len(segments), slide_size):
        # 현재 윈도우의 세그먼트들 추출
        window_segments = segments[start_idx:start_idx + window_size]
        if not window_segments:
            break
            
        # 현재 윈도우의 텍스트 생성
        formatted_text = ""
        for segment in window_segments:
            formatted_text += f"[{segment['id']}] {segment['text']}\n"
        
        # PII 추출
        result = extract_pii(formatted_text)
        
        try:
            if isinstance(result, str):
                result = json.loads(result)
            
            # 빈 딕셔너리나 pii_sentences 필드가 없는 경우 처리
            if not result or 'pii_sentences' not in result:
                print(f"⚠️ 윈도우 {start_idx}~{start_idx + window_size} - 빈 결과 또는 잘못된 스키마")
                continue
            
            pii_result = PIISentences(**result)
            
            # 결과를 딕셔너리에 병합 (중복 제거)
            for pii_sentence in pii_result.pii_sentences:
                # 빈 리스트 체크를 먼저 수행
                if len(pii_sentence.pii_text) == 0:
                    continue

                # 유효한 PII 텍스트 확인
                if not is_valid_pii(pii_sentence.pii_type, pii_sentence.pii_text[0]):
                    continue

                # sentence_id가 0인 경우 스킵
                if pii_sentence.sentence_id == 0:
                    continue

                if pii_sentence.pii_type == "BIRTHDAY":
                    continue

                # 중복 sentence_id는 무시하고, 처음 등장한 것만 저장
                if pii_sentence.sentence_id not in all_pii_sentences:
                    all_pii_sentences[pii_sentence.sentence_id] = pii_sentence
                
        
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"⚠️ 윈도우 {start_idx}~{start_idx + window_size} 처리 중 오류 발생:", e)
            print("LLM 원시 출력:", result)
            
            # 오류가 발생한 경우, 빈 PIISentences 객체로 대체하여 계속 진행
            try:
                # 빈 결과로라도 처리를 계속할 수 있도록 함
                if isinstance(result, str) and result.strip() == "{}":
                    print(f"   → 빈 딕셔너리 응답으로 인한 오류, 스킵합니다.")
                else:
                    print(f"   → 예상치 못한 형식의 응답, 스킵합니다.")
            except:
                pass
            continue
    
    # 최종 결과 생성
    final_result = PIISentences(pii_sentences=list(all_pii_sentences.values()))
    return final_result

import re

def is_valid_pii(pii_type: str, text: str) -> bool:
    if pii_type == "PHONE":
        return any(char.isdigit() for char in text) # 숫자 포함 여부
    
    elif pii_type == "RRN":
        return any(char.isdigit() for char in text) # 숫자 포함 여부

    elif pii_type == "BIRTHDAY":
        return any(char.isdigit() for char in text) # 숫자 포함 여부
    
    elif pii_type == "ADDRESS":
        # 시, 구, 동 포함, 5자 이상
        return len(text.strip()) >= 5 and any(word in text for word in ["시", "구", "동", "읍", "면", "리"]) and not any(x in text for x in ["주소", "거주지", "사는 곳"])
    
    elif pii_type == "NAME":
        # 1~4자 한글, "이름", "성함" 같은 표현 제외
        return not any(x in text for x in ["이름", "성함"])

    return False


import os

if __name__ == "__main__":
    for root, dirs, files in os.walk("output/transcript"):
        for file in files:
            if file.endswith(".json"):
                full_path = os.path.join(root, file)
                print(f"▶ 전사 대상: {full_path}")
                result = extract_pii_from_json(full_path)
                print(result)
