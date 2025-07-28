import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time

def test_ax_basic_translation():
    """
    skt/A.X-4.0-Light 모델의 기본 번역 기능을 테스트하는 함수
    """
    print("=== skt/A.X-4.0-Light 기본 번역 테스트 ===")
    
    model_name = "skt/A.X-4.0-Light"
    
    # 모델과 토크나이저 로드
    print(f"모델 로딩 중: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        model.eval()
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 테스트용 영어 문장들
    test_sentences = [
        "The first human went into space and orbited the Earth on April 12, 1961.",
        "Artificial Intelligence is transforming the way we live and work.",
        "Privacy is a fundamental human right that must be protected in the digital age.",
        "The rapid development of technology brings both opportunities and challenges."
    ]
    
    results = []
    
    # 시스템 프롬프트 설정
    system_prompt = "당신은 사용자가 제공하는 영어 문장들을 한국어로 번역하는 AI 전문가입니다."
    
    print("\n번역 테스트 시작...")
    
    for sentence in test_sentences:
        try:
            start_time = time.time()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence},
            ]
            
            input_ids = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(model.device)
            
            with torch.no_grad():
                output = model.generate(
                    input_ids,
                    max_new_tokens=128,
                    do_sample=False,
                )
            
            len_input_prompt = len(input_ids[0])
            translation = tokenizer.decode(output[0][len_input_prompt:], skip_special_tokens=True)
            
            elapsed_time = time.time() - start_time
            
            results.append({
                "original": sentence,
                "translation": translation,
                "time": elapsed_time
            })
            
            print(f"\n원문: {sentence}")
            print(f"번역: {translation}")
            print(f"처리 시간: {elapsed_time:.2f}초")
            
        except Exception as e:
            print(f"번역 실패: {e}")
            results.append({
                "original": sentence,
                "translation": "실패",
                "error": str(e)
            })
    
    print("\n=== 테스트 결과 요약 ===")
    success_count = sum(1 for r in results if "error" not in r)
    print(f"성공: {success_count}/{len(test_sentences)}")
    print(f"평균 처리 시간: {sum(r['time'] for r in results if 'time' in r) / success_count:.2f}초")

def test_ax_long_text():
    """
    skt/A.X-4.0-Light 모델의 긴 텍스트 번역 능력을 테스트하는 함수
    """
    print("\n=== skt/A.X-4.0-Light 긴 텍스트 번역 테스트 ===")
    
    model_name = "skt/A.X-4.0-Light"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        model.eval()
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 긴 텍스트 테스트
    long_text = """
    Privacy protection in the digital age has become increasingly important. 
    As artificial intelligence and data collection become more sophisticated, 
    we must ensure that personal information remains secure. This includes 
    implementing robust security measures, establishing clear data handling 
    policies, and respecting user consent in all digital interactions.
    """
    
    print("\n긴 텍스트 번역 시작...")
    
    try:
        start_time = time.time()
        
        messages = [
            {"role": "system", "content": "당신은 사용자가 제공하는 영어 문장들을 한국어로 번역하는 AI 전문가입니다."},
            {"role": "user", "content": long_text},
        ]
        
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_new_tokens=256,  # 긴 텍스트를 위해 토큰 수 증가
                do_sample=False,
            )
        
        len_input_prompt = len(input_ids[0])
        translation = tokenizer.decode(output[0][len_input_prompt:], skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        
        print(f"\n원문: {long_text.strip()}")
        print(f"\n번역: {translation}")
        print(f"\n처리 시간: {elapsed_time:.2f}초")
        
    except Exception as e:
        print(f"번역 실패: {e}")

if __name__ == "__main__":
    test_ax_basic_translation()
    test_ax_long_text()