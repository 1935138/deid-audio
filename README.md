# deid-audio
개인정보 보호를 위한 음성 데이터 비식별화 시스템

## todo
[x] faster-whisper를 사용하여 음성 파일을 전사하는 코드
[x] whisper_timestamped 를 사용하여 정확한 단어 기준 타임스탬프를 찍으면서 전사하는 코드
[x] Qwen/Qwen3-0.6B 테스트 코드
[ ] 노이즈제거
[ ] 시연을 위한 프로토타입

## 디렉토리 구성
```
.
├── data/              # 음성 데이터 파일 저장 디렉토리
├── result/            # 테스트 결과 저장 디렉토리
├── fast_whisper.py    # faster-whisper를 사용한 음성 전사 코드
├── whisper_timestamped_transcribe.py  # 단어 단위 타임스탬프 전사 코드
├── qwen3_test.py      # Qwen3-0.6B 모델 테스트 코드
└── requirements.txt   # 프로젝트 의존성 패키지 목록
```

# frontend
Svelte + Vite