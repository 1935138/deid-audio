from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json

def extract_pii_with_deepseek(text):
    # DeepSeek 모델과 토크나이저 로드
    # model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    model_name = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        trust_remote_code=True,
        device_map="auto"  # GPU 메모리 자동 관리
    )

    json_example = """
    {
        "pii_sentences": [
            {
                "sentence_id": 1,
                "pii_type": "이름"
            },
            {
                "sentence_id": 2,
                "pii_type": "주민등록번호"
            },
            {
                "sentence_id": 3,
                "pii_type": "전화번호"
            }
        ]
    }
    """

    prompt = f"""[INST] 아래는 환자와 의료진의 대화입니다. 각 문장에는 번호가 붙어 있습니다.
문장 중 환자의 개인정보(이름, 주민등록번호, 전화번호, 주소)가 포함된 문장의 번호와 개인정보의 유형 형태로 출력해주세요.

예시: {json_example}

텍스트:
{text}
[/INST]
"""

    # 입력 텍스트 토크나이징 및 모델 추론
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        inputs.input_ids,
        max_length=512,
        num_return_sequences=1,
        temperature=0.0,  # 생성의 다양성 조절
        do_sample=False,
    )

    # 결과 디코딩 및 JSON 파싱
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

if __name__ == "__main__":
    # 테스트용 예시 텍스트
    test_text = """
    [1] 환자분 성함이 김영희 맞으신가요? 
    [2] 네, 맞습니다.
    [3] 주민등록번호가 901231-2345678 맞으신가요?
    [4] 네
    [5] 연락처는 010-1234-5678이고, 
    [6] 환자 혈압 120/80 입니다.
    [7] 호흡 20회.
    [8] 서울시 강남구 테헤란로 123번길 45에 거주하고 계십니다.
    """
    
    result = extract_pii_with_deepseek(test_text)
    print(json.dumps(result, ensure_ascii=False, indent=2)) 