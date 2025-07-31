# deid-audio
개인정보 보호를 위한 음성 데이터 비식별화 시스템

## 개요
대화에서 개인정보를 자동으로 식별하고 비식별화 처리하는 AI 기반 시스템입니다.
LLM을 활용하여 대화에서 이름, 주민등록번호, 전화번호, 거주지 등의 개인정보를 탐지하고 마스킹 처리합니다.

## 주요 기능

### 1. 오디오 전사 및 타임스탬프 처리
- **faster-whisper**: 고속 음성 전사
- **whisper_timestamped**: 정확한 단어 단위 타임스탬프 생성
- JSON 형태의 구조화된 전사 결과 출력

### 2. AI 기반 개인정보 자동 탐지
- **LLM 모델**: DeepSeek-R1-Distill-Llama-8B 사용
- **탐지 대상**: 이름, 주민등록번호, 전화번호, 거주지, 주소
- **컨텍스트 분석**: 전후 문맥을 고려한 정확한 개인정보 식별
- **구조화된 출력**: Pydantic 모델 기반 JSON 스키마 검증

### 3. 개인정보 비식별화 처리
- **세그먼트 단위 마스킹**: 개인정보 길이만큼 `*`로 치환
- **단어 단위 마스킹**: 개인정보가 포함된 개별 단어 처리
- **원본 타임스탬프 보존**: 비식별화 후에도 시간 정보 유지

### 4. 웹 인터페이스
- **프론트엔드**: Svelte + Vite 기반
- **사용자 친화적 UI**: 직관적인 오디오 업로드 및 결과 확인

## 시스템 구성요소

### 데이터 모델
- **PIISentence**: 개인정보 문장 정보 (문장ID, PII유형, PII텍스트)
- **PIISentences**: 개인정보 문장들의 컬렉션
- **AudioTranscriptInfo**: 오디오 전사 데이터 관리

### 핵심 모듈
- **extract.py**: 개인정보 탐지 및 비식별화 처리
- **audio_transcript_info.py**: 오디오 전사 데이터 구조 관리
- **transcript.py**: 음성 전사 처리

## 디렉토리 구성
```
.
├── src/                    # 소스 코드
│   ├── extract.py          # 개인정보 탐지 및 비식별화 메인 모듈
│   ├── audio_transcript_info.py  # 전사 데이터 구조 관리
│   └── transcript.py       # 음성 전사 처리
├── data/                   # 원본 음성 데이터 파일
├── output/                 # 비식별화 처리 결과 파일
├── result/                 # 테스트 결과 저장
├── test/                   # 테스트 코드
├── frontend/               # 웹 인터페이스 (Svelte + Vite)
└── requirements.txt        # Python 의존성 패키지
```

## 기술 스택
- **AI/ML**: DeepSeek-R1-Distill-Llama-8B, Faster-Whisper, vLLM
- **백엔드**: Python, Pydantic, requests
- **프론트엔드**: Svelte, Vite, JavaScript
- **데이터**: JSON, 오디오 파일 (WAV, MP3 등)

## 설치 및 실행

### 1. Python 환경 설정
```bash
pip install -r requirements.txt
```

### 2. vLLM 서버 실행 (개인정보 탐지용)
```bash
# localhost:8000에서 DeepSeek 모델 서버 실행 필요
```

### 3. 프론트엔드 실행
```bash
cd frontend
npm install
npm run server
```

## 사용법
1. 오디오 파일을 시스템에 업로드
2. AI가 자동으로 개인정보 탐지
3. 비식별화된 전사 결과 확인 및 다운로드

## 보안 고려사항
- 의료 데이터 개인정보 보호 규정 준수
- 로컬 처리를 통한 데이터 보안 강화
- 정확한 개인정보 탐지를 위한 컨텍스트 분석

## todo
[x] faster-whisper를 사용하여 음성 파일을 전사하는 코드
[x] whisper_timestamped 를 사용하여 정확한 단어 기준 타임스탬프를 찍으면서 전사하는 코드  
[x] Qwen/Qwen3-0.6B 테스트 코드
[x] LLM 기반 개인정보 자동 탐지 시스템
[x] 개인정보 비식별화 처리 모듈
[ ] 노이즈제거
[ ] 시연을 위한 프로토타입
[ ] 웹 인터페이스 완성
[ ] 배치 처리 기능