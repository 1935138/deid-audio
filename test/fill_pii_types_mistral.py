from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json

def detect_pii_1(text, segment_text, tokenizer, model):
    prompt = f"""<s>[INST] 다음 텍스트에서 개인정보(이름, 주민등록번호, 전화번호, 주소 등)가 포함되어 있는지 확인하고,
포함되어 있다면 어떤 종류의 개인정보인지 알려주세요.
* 질문 문장(예: "주민등록번호가 어떻게 되세요?")은 개인정보로 간주하지 않습니다.

개인정보 유형 예시:
- 이름
- 주민등록번호
- 전화번호
- 주소
- 기타 민감한 개인정보

전체 전사 텍스트:
{text}

세그먼트 텍스트:
{segment_text}


* 개인정보가 포함된 경우 해당하는 유형만 리스트로 반환해주세요. 개인정보가 없다면 빈 리스트를 반환해주세요.
예시: ["이름", "전화번호"]
[/INST]"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95,
        "do_sample": True,
        "pad_token_id": tokenizer.pad_token_id,
    }

    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_config)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response.split("[/INST]")[-1].strip()
    
    try:
        # 응답을 리스트로 파싱
        pii_types = eval(response)  # 안전한 환경에서만 사용
        return pii_types if isinstance(pii_types, list) else []
    except:
        return []


def detect_pii_2(text, segment_text, tokenizer, model):
    json_example = """
    {
    "names": ["이름1", "이름2"],
    "resident_numbers": ["주민번호1"],
    "phone_numbers": ["전화번호1"],
    "locations": ["위치1"]
    }
    """

    prompt = f"""[INST] 다음 구급대원과 환자 간의 대화 전사 텍스트에서 환자의 개인정보를 추출해주세요.

    추출할 개인정보 유형:
    1. 이름 (성명)
    2. 주민등록번호 
    3. 전화번호
    4. 거주지 주소

    텍스트: {text}

    결과를 다음 JSON 형식으로 출력해주세요:
    {json_example}
    [/INST]"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95,
        "do_sample": True,
        "pad_token_id": tokenizer.pad_token_id,
    }

    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_config)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response.split("[/INST]")[-1].strip()
    
    try:
        # 응답을 리스트로 파싱
        pii_types = eval(response)  # 안전한 환경에서만 사용
        return pii_types if isinstance(pii_types, list) else []
    except:
        return []

def detect_pii_3(text, segment_text, tokenizer, model):
    json_example = """
    {
    "names": ["이름1", "이름2"],
    "resident_numbers": ["주민번호1"],
    "phone_numbers": ["전화번호1"],
    "locations": ["위치1"]
    }
    """

    prompt = f"""[INST] 다음 구급대원과 환자 간의 대화 전사 텍스트에서 환자의 개인정보를 추출해주세요.

    추출할 개인정보 유형:
    1. 이름 (성명)
    2. 주민등록번호 
    3. 전화번호
    4. 거주지 주소

    텍스트: {text}

    결과를 다음 JSON 형식으로 출력해주세요:
    {json_example}
    [/INST]"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95,
        "do_sample": True,
        "pad_token_id": tokenizer.pad_token_id,
    }

    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_config)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response.split("[/INST]")[-1].strip()
    
    try:
        # 응답을 리스트로 파싱
        pii_types = eval(response)  # 안전한 환경에서만 사용
        return pii_types if isinstance(pii_types, list) else []
    except:
        return []


def detect_pii_4(text, tokenizer, model):
    json_example = """
    {
    "names": ["이름1", "이름2"],
    "resident_numbers": ["주민번호1"],
    "phone_numbers": ["전화번호1"],
    "locations": ["위치1"]
    }
    """

    prompt = f"""[INST] 다음 구급대원과 환자 간의 대화 전사 텍스트에서 환자의 개인정보를 추출해주세요.

    추출할 개인정보 유형:
    1. 이름 (성명)
    2. 주민등록번호 
    3. 전화번호
    4. 거주지 주소

    텍스트: {text}

    결과를 다음 JSON 형식으로 출력해주세요:
    {json_example}
    [/INST]"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95,
        "do_sample": True,
        "pad_token_id": tokenizer.pad_token_id,
    }

    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_config)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response.split("[/INST]")[-1].strip()
    
    try:
        # 응답을 리스트로 파싱
        pii_types = eval(response)  # 안전한 환경에서만 사용
        return pii_types if isinstance(pii_types, list) else []
    except:
        return []

def main():
    # Mistral 모델과 토크나이저 로드
    print("모델을 로딩중입니다...")
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # JSON 파일 경로
    json_path = "output/202503200800003_amone-relay-prod_transcript.json"
    
    print(f"JSON 파일을 읽는 중: {json_path}")
    # JSON 파일 읽기
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("개인정보 분석 중...")
    # 각 세그먼트 처리
    total_segments = len(data["segments"])
    # for i, segment in enumerate(data["segments"], 1):
    #     print(f"\r진행률: {i}/{total_segments} ({i/total_segments*100:.1f}%)", end="")
    #     pii_types = detect_pii(data["transcript"], segment["text"], tokenizer, model)

    #     print(f"segment: {segment['text']}")
    #     print(f"pii_types: {pii_types}")
    #     segment["pii_types"] = pii_types


    pii_types = detect_pii(data["transcript"], "", tokenizer, model)
    print(pii_types)
    
    print("\n결과 저장 중...")
    # 수정된 JSON 파일 저장
    output_path = "output/202503200800003_amone-relay-prod_transcript_with_pii.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"완료! 결과가 저장된 파일: {output_path}")

if __name__ == "__main__":
    main() 