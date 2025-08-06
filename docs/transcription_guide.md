# 🎙️ 음성 전사 가이드

## 개요

`transcription.py` 모듈은 faster-whisper를 사용하여 고품질 음성 전사 기능을 제공합니다.

### 주요 기능
- **다중 모델 지원**: tiny ~ large-v3 모델 선택
- **다국어 지원**: 한국어, 영어, 자동 감지
- **GPU/CPU 자동 전환**: 최적 성능 보장
- **일괄 처리**: 디렉토리 단위 처리
- **단어별 타임스탬프**: 정밀한 시간 정보

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 기본 사용법

```python
from src.transcription import process_single_file

# 단일 파일 전사
process_single_file(
    input_path="audio.wav",
    output_dir="output/transcript",
    model_size="medium",
    language="ko"
)
```

### 3. 명령행 사용

```bash
# 단일 파일 처리
python src/transcription.py --single-file audio.wav

# 디렉토리 일괄 처리
python src/transcription.py --input data/audio --output results/

# 고급 설정
python src/transcription.py \
    --input data/audio \
    --output results/ \
    --model large-v3 \
    --language en \
    --device cuda \
    --verbose
```

## 📋 모델 선택 가이드

| 모델 | 크기 | 속도 | 정확도 | 권장 용도 |
|------|------|------|--------|-----------|
| `tiny` | 39MB | 🚀🚀🚀 | ⭐⭐ | 빠른 테스트, 실시간 |
| `base` | 74MB | 🚀🚀 | ⭐⭐⭐ | 일반 용도 |
| `small` | 244MB | 🚀 | ⭐⭐⭐⭐ | 균형잡힌 선택 |
| `medium` | 769MB | 🐌 | ⭐⭐⭐⭐⭐ | 권장 기본값 |
| `large-v2` | 1550MB | 🐌🐌 | ⭐⭐⭐⭐⭐ | 높은 정확도 |
| `large-v3` | 1550MB | 🐌🐌 | ⭐⭐⭐⭐⭐ | 최신/최고 성능 |

## 🌍 언어 설정

### 지원 언어
- `ko`: 한국어 (기본값)
- `en`: 영어
- `ja`: 일본어
- `zh`: 중국어
- `None`: 자동 감지

### 언어별 최적 설정

```python
# 한국어 (기본)
transcribe_audio(path, language="ko", model_size="medium")

# 영어 (높은 정확도)
transcribe_audio(path, language="en", model_size="large-v3")

# 다국어/미지 언어
transcribe_audio(path, language=None, model_size="large-v3")
```

## 🛠️ 함수 레퍼런스

### `transcribe_audio()`
기본 전사 함수

```python
def transcribe_audio(
    audio_file_path: str,
    model_size: str = "medium",
    output_dir: str = "output/transcript",
    language: Optional[str] = "ko",
    device: Optional[str] = None,
    verbose: bool = True
) -> str
```

### `process_directory()`
디렉토리 일괄 처리

```python
def process_directory(
    input_dir: str,
    output_dir: str = "output/transcript",
    model_size: str = "medium",
    language: Optional[str] = "ko",
    device: Optional[str] = None,
    audio_extensions: Optional[List[str]] = None
) -> None
```

### `load_whisper_model()`
모델 로딩 (재사용 최적화)

```python
def load_whisper_model(
    model_size: str,
    device: Optional[str] = None
) -> WhisperModel
```

## 🎯 사용 시나리오

### 1. 빠른 테스트
```bash
python src/transcription.py \
    --single-file test.wav \
    --model tiny \
    --output temp/
```

### 2. 고품질 전사
```bash
python src/transcription.py \
    --single-file important.wav \
    --model large-v3 \
    --language ko \
    --device cuda
```

### 3. 대량 일괄 처리
```bash
python src/transcription.py \
    --input data/interviews/ \
    --output results/transcripts/ \
    --model medium \
    --language ko
```

### 4. 다국어 처리
```bash
python src/transcription.py \
    --input data/multilingual/ \
    --output results/auto/ \
    --model large-v3 \
    --language none
```

## 📊 성능 최적화

### GPU 사용
```python
# GPU 강제 사용
transcribe_audio(path, device="cuda")

# CPU 강제 사용 (호환성)
transcribe_audio(path, device="cpu")

# 자동 선택 (권장)
transcribe_audio(path, device=None)
```

### 배치 처리 최적화
```python
# 모델 재사용으로 성능 향상
model = load_whisper_model("medium", "cuda")

for audio_file in audio_files:
    # transcribe_audio_with_model() 사용
    # 모델 재로딩 없이 빠른 처리
    pass
```

### 메모리 관리
- **모델 크기**: 시스템 메모리에 맞게 선택
- **배치 크기**: 대량 처리 시 메모리 모니터링
- **임시 파일**: 자동 정리됨

## 📄 출력 형식

### JSON 구조
```json
{
  "source_file": "audio.wav",
  "model_info": "faster-whisper-medium (lang: ko, confidence: 0.95)",
  "processing_time": 12.34,
  "full_transcript": "전체 전사 텍스트...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.5,
      "text": "안녕하세요",
      "words": [
        {
          "word": "안녕하세요",
          "start": 0.0,
          "end": 1.2,
          "is_pii": false
        }
      ]
    }
  ]
}
```

### 파일명 규칙
```
원본파일명_whisper-모델명_타임스탬프.json

예시:
interview_20231201_whisper-medium_20231201_143022.json
```

## 🔧 고급 설정

### VAD (Voice Activity Detection) 조정
```python
# 기본 VAD 설정 (코드 내부)
vad_parameters = vad.VadOptions(
    threshold=0.3,              # 음성 감지 임계값
    neg_threshold=0.15,         # 무음 임계값
    min_speech_duration_ms=1200, # 최소 음성 길이
    max_speech_duration_s=30,   # 최대 음성 길이
    min_silence_duration_ms=2000, # 최소 무음 길이
    speech_pad_ms=1000          # 음성 패딩
)
```

### 빔 서치 설정
```python
# 정확도 vs 속도 조절
beam_size=5      # 기본값 (균형)
beam_size=1      # 빠름 (그리디 디코딩)
beam_size=10     # 느림 (높은 정확도)
```

## 🐛 문제 해결

### 일반적인 오류

**CUDA 메모리 부족**
```bash
# 더 작은 모델 사용
--model medium  # 대신 small 사용

# CPU 모드로 전환
--device cpu
```

**파일 형식 오류**
```bash
# 지원 형식 확인
--extensions .wav .mp3 .flac

# FFmpeg 설치 필요할 수 있음
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

**언어 감지 오류**
```bash
# 명시적 언어 설정
--language ko  # 한국어 강제
--language en  # 영어 강제
```

### 로그 확인
```bash
# 상세 로그 활성화
--verbose

# 또는 Python에서
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 벤치마크

### 성능 참고 (RTX 3080 기준)

| 모델 | 10분 오디오 처리 시간 | GPU 메모리 사용량 |
|------|---------------------|------------------|
| tiny | ~30초 | ~1GB |
| base | ~45초 | ~1.5GB |
| small | ~1분 | ~2GB |
| medium | ~2분 | ~4GB |
| large-v3 | ~4분 | ~8GB |

### 정확도 참고

- **한국어**: medium 이상 권장
- **영어**: small 이상 충분
- **기술 용어**: large-v3 권장
- **노이즈 많은 환경**: large-v3 + 전처리

## 🔗 통합 사용

### 전처리와 연계
```bash
# 1단계: 오디오 전처리
python src/preprocessing.py --input raw/ --output preprocessed/

# 2단계: 전사
python src/transcription.py --input preprocessed/ --output transcripts/
```

### 파이프라인 예시
```python
from src.preprocessing import process_single_file as preprocess
from src.transcription import process_single_file as transcribe

# 완전한 파이프라인
def full_pipeline(input_audio, output_dir):
    # 1. 전처리
    preprocessed = preprocess(
        input_audio, 
        f"{output_dir}/preprocessed.wav"
    )
    
    # 2. 전사
    transcript = transcribe(
        preprocessed,
        f"{output_dir}/transcript"
    )
    
    return transcript
```

## 📚 참고 자료

- [Faster-Whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [OpenAI Whisper 논문](https://arxiv.org/abs/2212.04356)
- [Whisper 모델 카드](https://github.com/openai/whisper/blob/main/model-card.md)
