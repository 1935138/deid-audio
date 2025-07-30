import json
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from src.audio_transcript import AudioTranscript, AudioSegment

def load_transcript(file_path):
    transcript = AudioTranscript("")
    transcript.load_from_json(file_path)
    return transcript

def extract_personal_info(transcript: AudioTranscript):
    # 모델과 토크나이저 로드
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    
    print("토크나이저를 로딩중입니다...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print("모델을 로딩중입니다...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # 개인정보가 포함된 세그먼트를 찾기 위한 프롬프트
    segments_info = []
    
    for segment in transcript.segments:
        prompt = f"""<s>[INST] 아래 텍스트에서 다음과 같은 개인정보가 포함되어 있는지 확인하고, 있다면 어떤 종류의 개인정보인지 알려주세요:
- 이름
- 주민등록번호
- 전화번호
- 주소
- 차량 관련 정보
- 병원 정보
- 기타 민감한 개인정보

텍스트:
{segment.text}

JSON 형식으로 결과를 출력해주세요. 개인정보가 없다면 빈 객체를 반환해주세요.
예시 형식:
{{
    "contains_pii": true/false,
    "pii_types": ["이름", "전화번호" 등],
    "found_info": {{
        "이름": ["홍길동"],
        "전화번호": ["010-1234-5678"]
    }}
}}
[/INST]"""

        # 입력 인코딩
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # 생성 파라미터 설정
        generation_config = {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True,
            "pad_token_id": tokenizer.pad_token_id,
        }

        # 텍스트 생성
        with torch.no_grad():
            outputs = model.generate(**inputs, **generation_config)

        # 결과 디코딩 및 출력
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 프롬프트 부분 제거
        response = response.split("[/INST]")[-1].strip()
        
        try:
            result = json.loads(response)
            if result.get("contains_pii", False):
                segments_info.append({
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "text": segment.text,
                    "pii_info": result
                })
        except json.JSONDecodeError:
            print(f"Warning: JSON 파싱 실패 - {response}")
            continue

    # 최종 결과 생성
    final_result = {
        "audio_file": transcript.file_name,
        "total_segments": len(transcript.segments),
        "pii_segments": segments_info,
        "processing_time": transcript.processing_time,
        "processed_date": transcript.processed_date.isoformat(),
        "model_info": transcript.model_info
    }
    
    print("\n=== 개인정보가 포함된 세그먼트 ===")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))
    
    return final_result

if __name__ == "__main__":
    # 트랜스크립트 파일 경로
    transcript_file = "output/202503200800003_amone-relay-prod_transcript.json"
    
    # 트랜스크립트 로드
    transcript = load_transcript(transcript_file)
    
    # 개인정보 추출
    extracted_info = extract_personal_info(transcript) 