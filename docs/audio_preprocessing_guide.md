# 🎵 오디오 전처리 가이드

## 개요

`noise_reduce.py` 모듈은 음성 인식 전처리를 위한 고급 오디오 처리 기능을 제공합니다.

### 주요 기능
- **노이즈 제거**: librosa + noisereduce 기반
- **볼륨 정규화**: pydub 기반 dBFS 레벨 조정
- **포맷 통일**: 다양한 입력 포맷을 WAV로 변환
- **일괄 처리**: 디렉토리 단위 처리 지원

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 기본 사용법

```python
from src.noise_reduce import process_single_file

# 단일 파일 처리
process_single_file(
    input_path="input.wav",
    output_path="output_processed.wav",
    noise_clip_duration=2.0,    # 노이즈 샘플 길이 (초)
    target_dBFS=-20.0          # 목표 볼륨 레벨
)
```

### 3. 명령행 사용

```bash
# 기본 디렉토리 처리
python src/noise_reduce.py

# 커스텀 설정
python src/noise_reduce.py \
    --input data/raw \
    --output data/processed \
    --noise-duration 3.0 \
    --target-volume -18.0

# 단일 파일 처리
python src/noise_reduce.py \
    --single-file input.wav \
    --single-output output.wav
```

## 📋 처리 파이프라인

### 고급 처리 모드 (기본값)

1. **pydub 전처리**
   - 다양한 포맷 로드 지원
   - 모노 변환 (필요시)
   - 샘플레이트 정규화 (16kHz)
   - 1차 볼륨 정규화

2. **노이즈 제거**
   - librosa를 통한 오디오 로드
   - 시작 부분에서 노이즈 샘플 추출
   - noisereduce 알고리즘 적용

3. **최종 정규화**
   - numpy 배열을 AudioSegment로 변환
   - 최종 볼륨 레벨 조정
   - WAV 포맷으로 저장

### 기본 처리 모드

- librosa + noisereduce만 사용
- 기존 코드와의 호환성 유지

## 🎛️ 함수 레퍼런스

### `normalize_volume(audio_segment, target_dBFS=-20.0)`
오디오의 볼륨을 지정된 dBFS 레벨로 정규화

**Parameters:**
- `audio_segment` (AudioSegment): 정규화할 오디오
- `target_dBFS` (float): 목표 볼륨 레벨

### `preprocess_audio_pydub(input_path, output_path, target_dBFS=-20.0)`
pydub만을 사용한 간단한 전처리

**Features:**
- 포맷 변환
- 모노 변환
- 샘플레이트 정규화 (16kHz)
- 볼륨 정규화

### `reduce_noise_advanced(input_path, output_path, ...)`
고급 전처리 파이프라인

**Parameters:**
- `input_path` (str): 입력 파일 경로
- `output_path` (str): 출력 파일 경로
- `noise_clip_duration` (float): 노이즈 샘플 길이 (초)
- `target_dBFS` (float): 목표 볼륨 레벨
- `use_pydub_preprocessing` (bool): pydub 전처리 사용 여부

### `process_directory(input_dir, output_dir, ...)`
디렉토리 일괄 처리

**Features:**
- 재귀적 파일 검색
- 다중 포맷 지원 (.wav, .mp3, .flac, .m4a, .ogg)
- 디렉토리 구조 유지
- 진행 상황 로깅

### `process_single_file(input_path, output_path, ...)`
단일 파일 처리 편의 함수

## 📊 볼륨 레벨 가이드

| 환경 | 권장 dBFS | 설명 |
|------|-----------|------|
| 조용한 실내 | -15.0 | 높은 감도 필요 |
| 일반 사무실 | -20.0 | 표준 설정 (기본값) |
| 시끄러운 환경 | -25.0 | 노이즈 억제 우선 |
| 방송/녹음 | -23.0 | 전문 오디오 표준 |

## 🔧 고급 설정

### 노이즈 샘플 길이 조정

```python
# 짧은 노이즈 샘플 (빠른 처리)
noise_clip_duration = 1.0

# 긴 노이즈 샘플 (정확한 제거)
noise_clip_duration = 3.0
```

### 환경별 최적 설정

```python
# 조용한 환경
quiet_config = {
    "noise_clip_duration": 1.0,
    "target_dBFS": -15.0,
    "use_pydub_preprocessing": True
}

# 시끄러운 환경
noisy_config = {
    "noise_clip_duration": 3.0,
    "target_dBFS": -25.0,
    "use_pydub_preprocessing": True
}
```

## 📈 성능 최적화

### 메모리 사용량 줄이기
- 큰 파일의 경우 청크 단위 처리 고려
- 임시 파일 자동 정리 활용

### 처리 속도 향상
- SSD 사용 권장
- 멀티프로세싱 가능 (향후 추가 예정)

## 🐛 문제 해결

### 일반적인 오류

**ImportError: No module named 'pydub'**
```bash
pip install pydub
```

**FFmpeg 관련 오류**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# FFmpeg 바이너리를 PATH에 추가
```

**메모리 부족 오류**
- 큰 파일의 경우 청크 단위로 분할 처리
- 시스템 메모리 증설 고려

### 로그 확인

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 상세한 처리 과정 확인 가능
```

## 🎯 실사용 예시

### Whisper 전처리용

```python
# Whisper에 최적화된 전처리
def prepare_for_whisper(input_file, output_file):
    return reduce_noise_advanced(
        input_path=input_file,
        output_path=output_file,
        noise_clip_duration=2.0,
        target_dBFS=-20.0,      # Whisper 권장 레벨
        use_pydub_preprocessing=True
    )
```

### 실시간 처리 파이프라인

```python
# 실시간 녹음 -> 전처리 -> 인식
def realtime_pipeline(audio_chunk):
    # 1. 노이즈 제거
    processed = reduce_noise_advanced(audio_chunk, ...)
    
    # 2. Whisper 처리
    result = whisper.transcribe(processed)
    
    return result
```

## 📚 참고 자료

- [librosa 문서](https://librosa.org/)
- [pydub 문서](https://pydub.com/)
- [noisereduce GitHub](https://github.com/timsainb/noisereduce)
- [Whisper 전처리 가이드](https://openai.com/research/whisper)
