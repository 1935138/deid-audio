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
    pii_text: str = Field(description="문장 전체가 아니라 개인정보 구간 정확히 추출")
    pii_type: Optional[str] = Field(default=None, description="개인정보 유형: NAME, RRN, PHONE, ADDRESS, BIRTHDAY, SYMPTOM, HOSPITAL")

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
    오디오 전사 정보에서 개인정보를 식별하여 is_pii 플래그 설정
    """
    print(f"  🔍 PII 식별 시작: {len(pii_sentences.pii_sentences)}개의 PII 문장 처리")
    
    for pii_sentence in pii_sentences.pii_sentences:
        print(f"    📍 PII 문장 {pii_sentence.sentence_id}: {pii_sentence.pii_text}")
        
        segment_found = False
        for segment in audio_transcript_info.segments:
            if pii_sentence.sentence_id == int(segment.id):
                print(f"      🎯 세그먼트 {segment.id} 발견: '{segment.text}'")
                segment_found = True
                
                # PII 텍스트 처리
                if pii_sentence.pii_text and pii_sentence.pii_text.strip():
                    print(f"        🔎 PII 텍스트 '{pii_sentence.pii_text}' 처리 중...")
                    # 단어 단위에서 PII 플래그 설정
                    mark_pii_in_words(segment.words, pii_sentence.pii_text)
                
                break
        
        if not segment_found:
            print(f"      ❌ sentence_id {pii_sentence.sentence_id}에 해당하는 세그먼트를 찾을 수 없음!")
            available_ids = [seg.id for seg in audio_transcript_info.segments[:10]]  # 처음 10개만 출력
            print(f"      📋 사용 가능한 segment ID (처음 10개): {available_ids}")
            
            # PII 텍스트와 유사한 내용을 다른 segment에서 찾기
            print(f"      🔍 '{pii_sentence.pii_text}' 와 유사한 내용을 다른 segment에서 찾는 중...")
            found_segment = None
            for seg in audio_transcript_info.segments:
                if pii_sentence.pii_text.lower() in seg.text.lower():
                    print(f"      🎯 유사한 내용 발견! segment {seg.id}: '{seg.text}'")
                    found_segment = seg
                    break
            
            # 자동으로 올바른 segment에서 PII 처리
            if found_segment and pii_sentence.pii_text and pii_sentence.pii_text.strip():
                print(f"      🔧 자동 수정: segment {found_segment.id}에서 PII 처리 진행")
                mark_pii_in_words(found_segment.words, pii_sentence.pii_text)
    return audio_transcript_info


def mark_pii_in_words(words: List, pii_text: str):
    """
    단어 레벨에서 PII를 식별하여 is_pii 플래그 설정
    PII 텍스트가 단어들 사이에서 분리되거나 연결되어 나타날 수 있음을 고려
    """
    if not words or not pii_text.strip():
        print(f"          ❌ 빈 words 또는 빈 pii_text")
        return
    
    pii_text = pii_text.strip()
    print(f"          📋 단어들: {[w.word for w in words]}")
    print(f"          🎯 찾을 PII: '{pii_text}'")
    
    marked_words = []
    
    # PII 텍스트를 정규화 (공백, 특수문자 정리)
    pii_normalized = re.sub(r'[^\w가-힣-]', '', pii_text.lower())
    
    # 전체 세그먼트 텍스트를 하나로 합치기 (단어 경계 무시)
    full_text = ''.join([w.word.strip() for w in words])
    full_text_normalized = re.sub(r'[^\w가-힣-]', '', full_text.lower())
    
    print(f"          🔍 정규화된 PII: '{pii_normalized}'")
    print(f"          🔍 정규화된 전체 텍스트: '{full_text_normalized}'")
    
    # PII가 전체 텍스트에 포함되어 있는지 확인
    if pii_normalized not in full_text_normalized:
        print(f"          ❌ PII가 전체 텍스트에서 발견되지 않음")
        return
    
    # PII의 시작 위치 찾기
    pii_start_pos = full_text_normalized.find(pii_normalized)
    pii_end_pos = pii_start_pos + len(pii_normalized)
    
    print(f"          📍 PII 위치: {pii_start_pos} ~ {pii_end_pos}")
    
    # 각 단어의 위치를 계산하여 PII 범위와 겹치는지 확인
    current_pos = 0
    for word in words:
        word_clean = word.word.strip()
        if not word_clean:
            continue
            
        word_normalized = re.sub(r'[^\w가-힣-]', '', word_clean.lower())
        word_start_pos = current_pos
        word_end_pos = current_pos + len(word_normalized)
        
        # 단어가 PII 범위와 겹치는지 확인
        if (word_start_pos < pii_end_pos and word_end_pos > pii_start_pos):
            word.is_pii = True
            marked_words.append(f"위치매칭: {word.word}")
            print(f"            ✅ '{word.word}' (위치: {word_start_pos}~{word_end_pos}) -> PII 범위와 겹침")
        
        current_pos = word_end_pos
    
    if marked_words:
        print(f"          ✅ PII 플래그 설정됨: {marked_words}")
    else:
        print(f"          ❌ PII 플래그 설정되지 않음")





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
   - 구체적인 증상, 질병명 (SYMPTOM)
   - 병원명, 의료기관명 (HOSPITAL)

⚠️ 중요: sentence_id는 반드시 개인정보가 실제로 등장하는 문장의 번호여야 합니다.
- 질문 문장이 아닌 답변 문장의 ID를 사용하세요
- 예: "성함이 어떻게 되세요?"(질문) → "김철수요"(답변) 인 경우, 답변 문장의 ID를 사용

2. 다음과 같은 경우는 개인정보로 간주하지 마세요:
   - 단순한 건강 수치 정보: 혈압, 맥박, 혈당, 키/몸무게, 체온, 나이, 성별, 혈액형 등
   - 예: "혈압은 130에 90입니다", "나이는 65세입니다" 등의 문장은 제외
   - 항목 이름만 언급된 경우: "전화번호 알려주세요", "성함이 어떻게 되세요?" 등
   - 일반적인 증상: "아파요", "불편해요" 등은 제외하고 구체적인 질병명이나 증상만 포함

3. pii_type 필드는 개인정보의 유형을 나타냅니다: NAME, RRN, PHONE, ADDRESS, BIRTHDAY, SYMPTOM, HOSPITAL

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
[45] 어디 사세요?
[46] 부산시 사하구에 살아요
[47] 성함이 어떻게 되세요?
[48] 김철수요
[49] 주민등록번호는 901231-1234567이에요
[50] 어떤 증상이세요?
[51] 당뇨병이 있어요
[52] 어느 병원에서 치료받으세요?
[53] 서울대병원에서 치료받고 있어요

출력:
{
  "pii_sentences": [
    {
      "sentence_id": 46,
      "pii_text": "부산시 사하구",
      "pii_type": "ADDRESS"
    },
    {
      "sentence_id": 48,
      "pii_text": "김철수",   
      "pii_type": "NAME"
    },
    {
      "sentence_id": 49, 
      "pii_text": "901231-1234567",
      "pii_type": "RRN"
    },
    {
      "sentence_id": 51,
      "pii_text": "당뇨병",
      "pii_type": "SYMPTOM"
    },
    {
      "sentence_id": 53,
      "pii_text": "서울대병원",
      "pii_type": "HOSPITAL"
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

예시 3 - 질문-답변 패턴:
입력:
[200] 환자분 성함이 어떻게 되세요?
[201] 아 전영희이요
[202] 네 전, 영, 희

출력:
{
  "pii_sentences": [
    {
      "sentence_id": 201,
      "pii_text": "전영희",
      "pii_type": "NAME"
    },
    {
      "sentence_id": 202,
      "pii_text": "전, 영, 희",
      "pii_type": "NAME"
    }
  ]
}

주의: 200번 문장은 질문이므로 포함하지 않고, 실제 이름이 나온 201, 202번 문장만 포함

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
        
        print(f"🔍 윈도우 {start_idx}~{start_idx + len(window_segments)}: segment ID {window_segments[0]['id']}~{window_segments[-1]['id']}")
        print(f"  📝 LLM에게 전송하는 텍스트 미리보기:")
        print(f"  {formatted_text[:200]}..." if len(formatted_text) > 200 else f"  {formatted_text}")
        print()
        
        # PII 추출
        result = extract_pii(formatted_text)
        print("🔍 LLM 응답:", result)

        
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
                print(f"  📝 처리 중인 PII: sentence_id={pii_sentence.sentence_id}, pii_text={pii_sentence.pii_text}")
                
                # 빈 문자열 체크
                if not pii_sentence.pii_text or not pii_sentence.pii_text.strip():
                    print(f"    ❌ 빈 pii_text로 인해 스킵")
                    continue

                # 유효한 PII 텍스트 확인
                if not is_valid_pii(pii_sentence.pii_text):
                    print(f"    ❌ 유효하지 않은 PII 텍스트로 인해 스킵: {pii_sentence.pii_text}")
                    continue
                print(f"    ✅ 유효한 PII 텍스트: {pii_sentence.pii_text}")

                # sentence_id가 0인 경우 스킵
                if pii_sentence.sentence_id == 0:
                    print(f"    ❌ sentence_id가 0이라서 스킵")
                    continue

                # 특정 타입 제외
                if pii_sentence.pii_type == "BIRTHDAY":
                    print(f"    ❌ BIRTHDAY 타입이라서 스킵")
                    continue
                if pii_sentence.pii_type == "SYMPTOM":
                    print(f"    ❌ SYMPTOM 타입이라서 스킵")
                    continue
                if pii_sentence.pii_type == "HOSPITAL":
                    print(f"    ❌ HOSPITAL 타입이라서 스킵")
                    continue

                # 중복 sentence_id는 무시하고, 처음 등장한 것만 저장
                if pii_sentence.sentence_id not in all_pii_sentences:
                    all_pii_sentences[pii_sentence.sentence_id] = pii_sentence
                    print(f"    ✅ PII 추가됨: sentence_id={pii_sentence.sentence_id}")
                else:
                    print(f"    ⚠️ 중복 sentence_id로 인해 스킵: {pii_sentence.sentence_id}")
                
        
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

def is_valid_pii(text: str) -> bool:
    """개인정보 텍스트가 유효한지 검사"""
    if not text or not text.strip():
        print(f"        🔍 PII 검증 '{text}': 빈 텍스트 → False")
        return False
    
    text = text.strip()
    print(f"        🔍 PII 검증 '{text}' 시작...")
    
    # 숫자가 포함된 경우 (전화번호, 주민번호, 생년월일 등)
    if any(char.isdigit() for char in text):
        print(f"          ✅ 숫자 포함 → True")
        return True
    
    # 너무 짧은 텍스트 제외 (1글자)
    if len(text) < 2:
        print(f"          ❌ 너무 짧음 (길이: {len(text)}) → False")
        return False
    
    # 완전히 일치하는 무효한 단어들 (이름이 아닌 것들)
    invalid_exact_words = [
        "이름", "성함", "신분", "보호자", "번호", "휴대폰", "환자", "분", 
        "님", "씨", "선생", "의사", "간호사", "어디", "어떻게", "네", "아니",
        "그런", "이런", "저런", "것", "거", "게", "무엇", "언제", "왜"
    ]
    
    # 관계 표현 + "분" 조합 체크
    relations = ['보호자', '아내', '남편', '아들', '딸', '어머니', '아버지', '부모', '환자']
    for relation in relations:
        if f"{relation}분" in text:
            print(f"          ❌ 관계 표현 '{relation}분' 포함 → False")
            return False
    
    # 완전히 일치하는 무효한 단어인 경우만 제외
    if text.strip() in invalid_exact_words:
        print(f"          ❌ 무효한 키워드와 완전 일치 → False")
        return False
    
    # 명백히 이름이 아닌 패턴들 제외
    # 예: "어떻게 되세요", "성함이 뭐예요" 등
    invalid_phrases = ["어떻게", "되세요", "뭐예요", "무엇"]
    for phrase in invalid_phrases:
        if phrase in text:
            print(f"          ❌ 무효한 패턴 '{phrase}' 포함 → False")
            return False
    
    # 그 외의 경우 유효한 것으로 간주
    print(f"          ✅ 기타 유효한 PII → True")
    return True


import os

if __name__ == "__main__":
    output_dir = "output/processed"
    
    # 출력 디렉토리 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for root, dirs, files in os.walk("output/transcript"):
        for file in files:
            # if not file.startswith("202103231200019_ai-stt-relay002"):
                # continue
            if file.endswith(".json"):
                full_path = os.path.join(root, file)
                print(f"▶ 처리 대상: {full_path}")
                
                try:
                    # 1. PII 추출
                    print("  1. PII 추출 중...")
                    pii_sentences = extract_pii_from_json(full_path)
                    print(f"     - 발견된 PII 문장 수: {len(pii_sentences.pii_sentences)}")
                    
                    # 2. AudioTranscriptInfo 객체 생성 및 로드
                    print("  2. 전사 정보 로드 중...")
                    audio_info = AudioTranscriptInfo("dummy_audio_path")
                    
                    if not audio_info.load_from_json(full_path):
                        print("     ❌ JSON 파일 로드 실패")
                        continue
                    
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
                    result_path = processed_audio_info.save_to_json(output_dir)
                    print(f"     ✅ 저장 완료: {result_path}")
                    
                except Exception as e:
                    print(f"     ❌ 파일 처리 중 오류 발생: {e}")
                    continue
                
                print()
