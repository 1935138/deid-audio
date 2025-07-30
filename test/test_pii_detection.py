import unittest
from src.audio_transcript import AudioTranscript, AudioSegment
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import os

class TestPIIDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Mistral 모델과 토크나이저 로드
        cls.model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        cls.tokenizer = AutoTokenizer.from_pretrained(cls.model_name)
        cls.model = AutoModelForCausalLM.from_pretrained(
            cls.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    def detect_pii(self, text):
        prompt = f"""<s>[INST] 아래 텍스트에서 다음과 같은 개인정보가 포함되어 있는지 확인하고, 있다면 어떤 종류의 개인정보인지 알려주세요:
- 이름
- 주민등록번호
- 전화번호
- 주소
- 차량 관련 정보
- 병원 정보
- 기타 민감한 개인정보

텍스트:
{text}

JSON 형식으로 결과를 출력해주세요. 개인정보가 없다면 빈 객체를 반환해주세요.
예시 형식:
{{
    "text": "홍길동씨의 전화번호는 010-1234-5678입니다.",
    "contains_pii": true,
    "pii_types": ["이름", "전화번호"],
    "found_info": {{
        "이름": ["홍길동"],
        "전화번호": ["010-1234-5678"]
    }}
}}

또는 개인정보가 없는 경우:
{{
    "text": "오늘 날씨가 참 좋네요.",
    "contains_pii": false,
    "pii_types": [],
    "found_info": {{}}
}}
[/INST]"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        generation_config = {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True,
            "pad_token_id": self.tokenizer.pad_token_id,
        }

        with torch.no_grad():
            outputs = self.model.generate(**inputs, **generation_config)

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.split("[/INST]")[-1].strip()
        
        try:
            # 응답을 리스트로 파싱
            pii_types = eval(response)  # 안전한 환경에서만 사용
            return pii_types if isinstance(pii_types, list) else []
        except:
            return []

    def test_fill_pii_types(self):
        # 테스트용 JSON 파일 경로
        json_path = "output/202503200800003_amone-relay-prod_transcript.json"
        
        # JSON 파일 읽기
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 각 세그먼트의 pii_types 채우기
        for segment in data["segments"]:
            pii_types = self.detect_pii(segment["text"])
            segment["pii_types"] = pii_types
        
        # 수정된 JSON 파일 저장
        output_path = "output/202503200800003_amone-relay-prod_transcript_with_pii.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 결과 검증
        self.assertTrue(os.path.exists(output_path))
        
        # 저장된 파일 다시 읽어서 검증
        with open(output_path, "r", encoding="utf-8") as f:
            result_data = json.load(f)
        
        # 모든 세그먼트에 pii_types가 리스트로 존재하는지 확인
        for segment in result_data["segments"]:
            self.assertIsInstance(segment["pii_types"], list)
            
            # 차량 관련 정보가 포함된 세그먼트 확인
            if "차 대차" in segment["text"]:
                self.assertIn("차량 관련 정보", segment["pii_types"])

if __name__ == '__main__':
    unittest.main() 