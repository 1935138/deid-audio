import json
import requests
from pydantic import BaseModel, Field
from typing import List

class PIISentence(BaseModel):
    sentence_id: int = Field(description="개인정보가 포함된 문장의 번호")
    pii_type: str = Field(description="개인정보의 유형")
    pii_text: str = Field(description="문장 전체가 아니라 개인정보 구간 정확히 추출")

class PIISentences(BaseModel):
    pii_sentences: List[PIISentence]

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
    # 테스트용 예시 텍스트
    test_text = """
    [1] 환자분 성함이요?
    [2] 김철수 김철수
    [3] 주민등록번호가 214-23-2345678 맞으신가요?
    [4] 네
    [5] 연락처는 010-1234-5678이고, 
    [6] 환자 혈압 120/80 입니다.
    [7] 호흡 20회.
    [9] 환자 분 주거지가 어디예요?
    [10] 덕양이요
    [11] 생년월일은요? 990821
    """
    
    result = extract_pii(test_text)
    print(json.dumps(result, ensure_ascii=False, indent=2)) 