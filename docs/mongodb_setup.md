# MongoDB 설정 및 사용 가이드

## 개요

이 프로젝트는 오디오 데이터, 전사 데이터, 개인정보 탐지 결과를 통합 관리하기 위해 MongoDB를 사용합니다.

## 시스템 아키텍처

```
오디오 파일 (WAV/MP3)
    ↓
전사 처리 (Whisper)
    ↓
개인정보 탐지 (LLM)
    ↓
MongoDB 저장
    ↓
통합 데이터 관리
```

## 설치 및 설정

### 1. MongoDB 설치

#### Ubuntu/Debian
```bash
# MongoDB 공식 리포지토리 추가
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# 설치
sudo apt-get update
sudo apt-get install -y mongodb-org

# 서비스 시작
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Docker 사용
```bash
# MongoDB 컨테이너 실행
docker run -d \
  --name mongodb-deid \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0

# 또는 docker-compose 사용
docker-compose up -d
```

### 2. Python 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 설정

`config.env` 파일을 확인하고 필요시 수정:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=deid_audio_db
SERVER_HOST=localhost
SERVER_PORT=8000
LOG_LEVEL=INFO
```

## 데이터 모델

### AudioData (메인 컬렉션)

```json
{
  "_id": ObjectId,
  "filename": "sample_audio.wav",
  "file_path": "/data/sample_audio.wav",
  "file_size": 2048000,
  "duration": 125.3,
  "format": "wav",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "status": "processed",
  
  "transcription": {
    "sentences": [
      {
        "text": "안녕하세요, 제 이름은 홍길동입니다.",
        "start_time": 0.0,
        "end_time": 3.2,
        "words": [
          {
            "text": "안녕하세요",
            "start_time": 0.0,
            "end_time": 1.0,
            "confidence": 0.95
          }
        ]
      }
    ],
    "personal_info": [
      {
        "type": "NAME",
        "value": "홍길동",
        "masked_value": "[이름]",
        "start_time": 1.9,
        "end_time": 3.2,
        "word_index": 3,
        "sentence_index": 0,
        "confidence_score": 0.92
      }
    ],
    "language": "ko",
    "transcription_engine": "whisper-large-v3",
    "processed_at": "2024-01-01T00:00:00Z"
  },
  
  "metadata": {
    "speaker_id": "patient_001",
    "recording_date": "2024-01-01T00:00:00Z",
    "sample_rate": 44100,
    "channels": 1,
    "bit_depth": 16,
    "tags": ["medical", "consultation"]
  }
}
```

## 주요 기능

### 1. 데이터 삽입

```python
from src.database import AudioData, insert_audio_data

# 오디오 데이터 생성
audio_data = AudioData(
    filename="sample.wav",
    file_path="/data/sample.wav",
    duration=120.5,
    format="wav"
)

# 데이터베이스에 삽입
audio_id = await insert_audio_data(audio_data)
```

### 2. 데이터 조회

```python
from src.database import get_audio_data, get_audio_data_by_filename

# ID로 조회
audio = await get_audio_data(audio_id)

# 파일명으로 조회
audio = await get_audio_data_by_filename("sample.wav")
```

### 3. 전사 데이터 업데이트

```python
from src.database import TranscriptionData, update_transcription_data

transcription = TranscriptionData(
    sentences=sentences,
    language="ko",
    transcription_engine="whisper"
)

await update_transcription_data(audio_id, transcription)
```

### 4. 개인정보 추가

```python
from src.database import PersonalInfoData, add_personal_info

personal_info = [
    PersonalInfoData(
        type="NAME",
        value="홍길동",
        masked_value="[이름]",
        start_time=1.9,
        end_time=3.2,
        confidence_score=0.92
    )
]

await add_personal_info(audio_id, personal_info)
```

### 5. 검색 및 통계

```python
from src.database import search_by_personal_info_type, get_statistics

# 개인정보 유형별 검색
name_files = await search_by_personal_info_type("NAME")
phone_files = await search_by_personal_info_type("PHONE_NUMBER")

# 통계 조회
stats = await get_statistics()
print(f"총 파일 수: {stats['total_audio_files']}")
```

## 인덱스 전략

다음 인덱스들이 자동으로 생성됩니다:

```javascript
// 기본 인덱스
db.audio_data.createIndex({"filename": 1}, {unique: true})
db.audio_data.createIndex({"file_path": 1}, {unique: true})
db.audio_data.createIndex({"created_at": 1})
db.audio_data.createIndex({"status": 1})

// 전사 데이터 인덱스
db.audio_data.createIndex({"transcription.personal_info.type": 1})
db.audio_data.createIndex({"transcription.language": 1})

// 메타데이터 인덱스
db.audio_data.createIndex({"metadata.speaker_id": 1})
db.audio_data.createIndex({"metadata.tags": 1})
```

## 자주 사용하는 쿼리

### 1. 개인정보 유형별 검색

```javascript
db.audio_data.find({
  "transcription.personal_info.type": "PHONE_NUMBER"
})
```

### 2. 특정 시간대 전사 데이터 검색

```javascript
db.audio_data.find({
  "transcription.sentences": {
    "$elemMatch": {
      "start_time": {"$gte": 10},
      "end_time": {"$lte": 20}
    }
  }
})
```

### 3. 처리 상태별 검색

```javascript
db.audio_data.find({"status": "processed"})
```

### 4. 개인정보 통계

```javascript
db.audio_data.aggregate([
  {"$unwind": "$transcription.personal_info"},
  {"$group": {
    "_id": "$transcription.personal_info.type",
    "count": {"$sum": 1},
    "files": {"$addToSet": "$filename"}
  }}
])
```

## 백업 및 복원

### 백업

```bash
# 전체 데이터베이스 백업
mongodump --db deid_audio_db --out /backup/

# 특정 컬렉션 백업
mongodump --db deid_audio_db --collection audio_data --out /backup/
```

### 복원

```bash
# 전체 데이터베이스 복원
mongorestore --db deid_audio_db /backup/deid_audio_db/

# 특정 컬렉션 복원
mongorestore --db deid_audio_db --collection audio_data /backup/deid_audio_db/audio_data.bson
```

## 성능 최적화

### 1. 인덱스 최적화

- 자주 검색하는 필드에 대해 복합 인덱스 고려
- 텍스트 검색이 필요한 경우 텍스트 인덱스 생성

### 2. 쿼리 최적화

- `explain()` 명령어로 쿼리 성능 분석
- 필요한 필드만 projection으로 선택

### 3. 연결 풀링

- 애플리케이션에서 연결 풀 설정
- 적절한 연결 수 제한

## 보안 고려사항

### 1. 접근 제어

```javascript
// 사용자 생성
use deid_audio_db
db.createUser({
  user: "deid_user",
  pwd: "secure_password",
  roles: [
    {role: "readWrite", db: "deid_audio_db"}
  ]
})
```

### 2. 암호화

- 개인정보 필드 암호화 고려
- TLS/SSL 연결 사용

### 3. 감사 로그

- MongoDB 감사 로그 활성화
- 접근 및 수정 기록 추적

## 모니터링

### 1. 성능 메트릭

- CPU/메모리 사용량 모니터링
- 디스크 I/O 모니터링
- 쿼리 응답 시간 추적

### 2. 로그 관리

- MongoDB 로그 레벨 설정
- 로그 로테이션 설정

## 문제 해결

### 일반적인 문제들

1. **연결 실패**
   - MongoDB 서비스 상태 확인
   - 방화벽 설정 확인
   - 연결 URL 검증

2. **성능 저하**
   - 인덱스 사용 여부 확인
   - 쿼리 최적화
   - 리소스 사용량 점검

3. **디스크 공간 부족**
   - 오래된 데이터 아카이빙
   - 로그 파일 정리
   - 컬렉션 압축 