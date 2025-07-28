from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def test_mistral():
    # 모델과 토크나이저 로드
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    
    print("토크나이저를 로딩중입니다...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print("모델을 로딩중입니다...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,  # 메모리 사용량 줄이기 위해 float16 사용
        device_map="auto"  # 자동으로 가용 장치에 모델 할당
    )

    # 테스트할 프롬프트
    prompt = """<s>[INST] 인공지능에 대해 간단히 설명해주세요. [/INST]"""

    # 입력 인코딩
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # 생성 파라미터 설정
    generation_config = {
        "max_new_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.95,
        "do_sample": True,
        "pad_token_id": tokenizer.pad_token_id,
    }

    print("응답을 생성중입니다...")
    # 텍스트 생성
    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_config)

    # 결과 디코딩 및 출력
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\n=== 생성된 응답 ===")
    print(response)

if __name__ == "__main__":
    test_mistral() 