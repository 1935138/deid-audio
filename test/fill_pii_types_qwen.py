from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json

def extract_pii_with_qwen(text):
    # Qwen 모델과 토크나이저 로드
    model_name = "Qwen/Qwen3-8B"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        trust_remote_code=True,
        device_map="auto"  # GPU 메모리 자동 관리
    )

    json_example = """
    {
        "이름": [],
        "주민등록번호": [],
        "전화번호": [],
        "거주지": []
    }
    """

    prompt = f"""다음 구급대원과 환자 간의 대화 전사 텍스트에서 환자의 개인정보를 추출해주세요.

    텍스트: {text}

    추출할 개인정보 유형:
    1. 이름
    2. 주민등록번호 
    3. 전화번호
    4. 거주지 주소

    결과는 다음과 같은 JSON 형식으로 출력해주세요:
    {json_example}
    """

    # 입력 텍스트 토크나이징 및 모델 추론
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        inputs.input_ids,
        max_length=512,
        num_return_sequences=1,
        temperature=0.7,  # 생성의 다양성 조절
        do_sample=True,
    )

    # 결과 디코딩 및 JSON 파싱
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    try:
        # JSON 부분만 추출하기 위한 처리
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
        else:
            result = {
            "이름": [],
            "주민등록번호": [],
            "전화번호": [],
            "거주지": []
        }
    except json.JSONDecodeError:
        result = {
            "이름": [],
            "주민등록번호": [],
            "전화번호": [],
            "거주지": []
        }

    return result

if __name__ == "__main__":
    # 테스트용 예시 텍스트
    test_text = """
    환자분 성함이 김영희 맞으신가요? 네, 맞습니다.
    주민등록번호가 901231-2345678 맞으신가요?
    연락처는 010-1234-5678이고, 
    서울시 강남구 테헤란로 123번길 45에 거주하고 계십니다.
    """
    
    result = extract_pii_with_qwen(test_text)
    print(json.dumps(result, ensure_ascii=False, indent=2)) 