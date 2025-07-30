import json
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

def load_transcript(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['transcript']

def create_llm_pipeline():
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

    # Hugging Face 파이프라인 생성
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=1024,
        temperature=0.7,
        top_p=0.95,
        pad_token_id=tokenizer.pad_token_id
    )

    # LangChain LLM 생성
    llm = HuggingFacePipeline(pipeline=pipe)
    
    return llm

def extract_personal_info(text):
    # LLM 파이프라인 생성
    llm = create_llm_pipeline()

    # 프롬프트 템플릿 정의
    template = """아래 텍스트에서 다음과 같은 개인정보를 추출해주세요:
- 이름
- 주민등록번호
- 전화번호
- 주소
- 차량 관련 정보
- 병원 정보
- 기타 민감한 개인정보

텍스트:
{text}

JSON 형식으로 결과를 출력해주세요."""

    # 프롬프트 템플릿 생성
    prompt = PromptTemplate(
        input_variables=["text"],
        template=template
    )

    # LLMChain 생성
    chain = LLMChain(llm=llm, prompt=prompt)

    print("개인정보를 추출중입니다...")
    # 체인 실행
    result = chain.run(text=text)
    
    print("\n=== 추출된 개인정보 ===")
    print(result)
    
    return result

if __name__ == "__main__":
    # 트랜스크립트 파일 경로
    transcript_file = "output/202503200800003_amone-relay-prod_transcript.json"
    
    # 트랜스크립트 로드
    text = load_transcript(transcript_file)
    
    # 개인정보 추출
    extracted_info = extract_personal_info(text) 