import json
import requests
import re
from pydantic import BaseModel, Field, ValidationError
from typing import List
from audio_transcript_info import AudioTranscriptInfo


class PIISentence(BaseModel):
    sentence_id: int = Field(description="개인정보가 포함된 문장의 번호")
    pii_type: str = Field(description="개인정보의 유형")
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


def mask_pii_in_words(words: List, pii_text: str, pii_type: str):
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


def mask_consecutive_words_for_pii(words: List, pii_text: str, pii_type: str):
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


    prompt = f"""[INST] [INST] 아래는 환자와 의료진의 대화입니다. 각 문장에는 번호가 붙어 있습니다.

당신의 작업은 다음과 같습니다:
1. 전후 문맥을 고려하여 개인정보가 실제로 언급된 문장 찾아내세요. (이름, 주민등록번호, 전화번호, 거주지, 주소, 사는 곳)
   - 질문에 개인정보가 명시되어 있으면 질문에서 추출
   - 응답에 개인정보가 있다면 응답에서 추출

2. pii_text 필드는 문장 전체가 아니라 **개인정보 내용만** 정확히 추출합니다. 다음과 같이 추출하세요:
  - [1] 부산시 사하구에 살아요 → "부산시 사하구"
  - [2] 제 이름은 김철수입니다 → "김철수"
  - [3] 주민등록번호는 901231-1234567이에요 → "901231-1234567"

* 주의사항
  - 텍스트 생성 시 Chinese character 사용 금지

출력은 아래 JSON 스키마를 반드시 따르세요:
{PIISentences.model_json_schema()}

대화 내용:
{text}
[/INST]
"""


    headers = {"Content-Type": "application/json"}

    data = {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
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

if __name__ == "__main__":
    # # 테스트용 예시 텍스트
    # test_text = """
    # [1] 환자분 성함이요?
    # [2] 김철수 김철수
    # [3] 주민등록번호가 214-23-2345678 맞으신가요?
    # [4] 네
    # [5] 연락처는 010-1234-5678이고, 
    # [6] 환자 혈압 120/80 입니다.
    # [7] 호흡 20회.
    # [9] 환자 분 주거지가 어디예요?
    # [10] 덕양이요
    # [11] 생년월일은요? 990821
    # """

    json_file_path = "output/202503200800003_amone-relay-prod_20250731_024228.json"
    formatted_text = format_json_file(json_file_path)
    print(formatted_text[2700:3300])

    # AudioTranscriptInfo 객체 생성 및 JSON 파일 로드
    audio_transcript_info = AudioTranscriptInfo(json_file_path)
    if not audio_transcript_info.load_from_json(json_file_path):
        print("❌ JSON 파일 로드 실패")
        exit(1)
    
    print(f"✅ 로드된 세그먼트 수: {len(audio_transcript_info.segments)}")
    
    result = extract_pii(formatted_text[2700:3300])
    try:
        if isinstance(result, str):
            result = json.loads(result)
        pii_result = PIISentences(**result)
        print("📝 PII 탐지 결과:")
        print(pii_result)

        de_identified_audio_transcript_info = de_identification(audio_transcript_info, pii_result)
        output_path = de_identified_audio_transcript_info.save_to_json("output")
        print(f"✅ 비식별화 완료: {output_path}")


    except (json.JSONDecodeError, ValidationError) as e:
        print("⚠️ 결과 파싱 실패:", e)
        print("LLM 원시 출력:", result)

