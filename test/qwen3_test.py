import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time

def test_qwen3_basic():
    """
    Qwen3-0.6B 모델의 기본 텍스트 생성 기능을 테스트하는 함수
    """
    print("=== Qwen3-0.6B 기본 텍스트 생성 테스트 ===")
    
    model_name = "Qwen/Qwen3-0.6B"
    
    # 모델과 토크나이저 로드
    print(f"모델 로딩 중: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 테스트 프롬프트들
    test_prompts = [
        "안녕하세요. 자기소개를 해주세요.",
        "개인정보 보호의 중요성에 대해 설명해주세요.",
        "음성 데이터에서 개인을 식별할 수 있는 정보는 무엇인가요?",
        "AI 모델이 개인정보를 어떻게 보호할 수 있을까요?"
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- 테스트 {i}: {prompt[:30]}... ---")
        
        # 채팅 템플릿 적용 (thinking mode 활성화)
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True  # thinking 모드 활성화
        )
        
        # 토큰화
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        # 텍스트 생성
        start_time = time.time()
        try:
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=512,
                temperature=0.6,
                top_p=0.95,
                top_k=20,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            generation_time = time.time() - start_time
            
            # 출력 파싱
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            
            # thinking content와 답변 분리
            try:
                # </think> 토큰 찾기 (151668)
                index = len(output_ids) - output_ids[::-1].index(151668)
            except ValueError:
                index = 0
            
            thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip()
            answer_content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
            
            print(f"프롬프트: {prompt}")
            if thinking_content:
                print(f"추론 과정: {thinking_content[:200]}...")
            print(f"답변: {answer_content}")
            print(f"생성 시간: {generation_time:.2f}초")
            
            results.append({
                "prompt": prompt,
                "thinking": thinking_content,
                "answer": answer_content,
                "time": generation_time
            })
            
        except Exception as e:
            print(f"텍스트 생성 실패: {e}")
            
    return results

def test_qwen3_thinking_modes():
    """
    Qwen3-0.6B 모델의 thinking/non-thinking 모드를 비교 테스트하는 함수
    """
    print("\n=== Qwen3-0.6B Thinking/Non-Thinking 모드 비교 테스트 ===")
    
    model_name = "Qwen/Qwen3-0.6B"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 복잡한 추론이 필요한 프롬프트
    test_prompt = "음성 데이터에서 개인정보를 제거하는 가장 효과적인 방법 3가지를 단계별로 설명해주세요."
    
    modes = [
        {"name": "Thinking Mode", "enable_thinking": True, "temp": 0.6, "top_p": 0.95},
        {"name": "Non-Thinking Mode", "enable_thinking": False, "temp": 0.7, "top_p": 0.8}
    ]
    
    for mode in modes:
        print(f"\n--- {mode['name']} 테스트 ---")
        
        messages = [{"role": "user", "content": test_prompt}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=mode["enable_thinking"]
        )
        
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        start_time = time.time()
        try:
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=600,
                temperature=mode["temp"],
                top_p=mode["top_p"],
                top_k=20,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            generation_time = time.time() - start_time
            
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            
            if mode["enable_thinking"]:
                # thinking content 분리
                try:
                    index = len(output_ids) - output_ids[::-1].index(151668)
                except ValueError:
                    index = 0
                
                thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip()
                answer_content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
                
                print(f"추론 과정 길이: {len(thinking_content)} 문자")
                if thinking_content:
                    print(f"추론 과정 (일부): {thinking_content[:150]}...")
                print(f"최종 답변: {answer_content}")
            else:
                answer_content = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
                print(f"답변: {answer_content}")
            
            print(f"생성 시간: {generation_time:.2f}초")
            
        except Exception as e:
            print(f"텍스트 생성 실패: {e}")

def test_qwen3_privacy_scenarios():
    """
    개인정보 보호 관련 시나리오를 테스트하는 함수
    """
    print("\n=== Qwen3-0.6B 개인정보 보호 시나리오 테스트 ===")
    
    model_name = "Qwen/Qwen3-0.6B"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 개인정보 보호 관련 시나리오들
    privacy_scenarios = [
        "다음 음성 전사 텍스트에서 개인정보를 마스킹해주세요: '안녕하세요, 제 이름은 김철수이고 전화번호는 010-1234-5678입니다.'",
        "음성 데이터에서 화자의 신원을 보호하면서도 내용의 의미를 유지하는 방법을 설명해주세요.",
        "GDPR과 개인정보보호법에 따른 음성 데이터 처리 가이드라인을 요약해주세요.",
        "음성 데이터 비식별화 과정에서 고려해야 할 기술적, 법적 요소들을 나열해주세요."
    ]
    
    for i, scenario in enumerate(privacy_scenarios, 1):
        print(f"\n--- 시나리오 {i} ---")
        print(f"질문: {scenario}")
        
        messages = [
            {"role": "system", "content": "당신은 개인정보 보호 전문가입니다. 정확하고 실용적인 조언을 제공해주세요."},
            {"role": "user", "content": scenario}
        ]
        
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True
        )
        
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        try:
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=400,
                temperature=0.6,
                top_p=0.95,
                top_k=20,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            
            # thinking content 분리
            try:
                index = len(output_ids) - output_ids[::-1].index(151668)
            except ValueError:
                index = 0
            
            answer_content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
            print(f"답변: {answer_content}")
            
        except Exception as e:
            print(f"텍스트 생성 실패: {e}")

def save_test_results(results, filename="qwen3_test_results.txt"):
    """
    테스트 결과를 파일로 저장하는 함수
    """
    print(f"\n테스트 결과를 {filename}에 저장 중...")
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== Qwen3-0.6B 테스트 결과 ===\n\n")
            f.write(f"테스트 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"총 테스트 수: {len(results)}\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"--- 테스트 {i} ---\n")
                f.write(f"프롬프트: {result['prompt']}\n")
                if result.get('thinking'):
                    f.write(f"추론 과정: {result['thinking']}\n")
                f.write(f"답변: {result['answer']}\n")
                f.write(f"생성 시간: {result['time']:.2f}초\n\n")
        
        print(f"테스트 결과가 {filename}에 저장되었습니다.")
        
    except Exception as e:
        print(f"파일 저장 실패: {e}")

def main():
    """
    Qwen3-0.6B 테스트의 메인 함수
    """
    print("Qwen3-0.6B 모델 테스트를 시작합니다...")
    
    # GPU/CPU 정보 확인
    if torch.cuda.is_available():
        print(f"CUDA 사용 가능 - GPU: {torch.cuda.get_device_name()}")
        print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    else:
        print("CPU 모드로 실행됩니다.")
    
    try:
        # 1. 기본 텍스트 생성 테스트
        results = test_qwen3_basic()
        
        # 2. Thinking/Non-thinking 모드 비교 테스트
        test_qwen3_thinking_modes()
        
        # 3. 개인정보 보호 시나리오 테스트
        test_qwen3_privacy_scenarios()
        
        # 4. 결과 저장
        if results:
            save_test_results(results)
        
        print("\n=== 모든 테스트가 완료되었습니다! ===")
        
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 