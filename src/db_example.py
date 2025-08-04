"""
MongoDB 사용 예제
"""
import asyncio
import os
from datetime import datetime
from src.database import (
    AudioData, TranscriptionData, PersonalInfoData, 
    WordData, SentenceData, AudioMetadata,
    insert_audio_data, get_audio_data, update_transcription_data,
    add_personal_info, search_by_personal_info_type, get_statistics,
    create_indexes
)

async def example_usage():
    """MongoDB 사용 예제"""
    
    # 1. 인덱스 생성
    print("1. 인덱스 생성 중...")
    create_indexes()
    
    # 2. 샘플 오디오 데이터 생성
    print("2. 샘플 오디오 데이터 생성 중...")
    sample_audio = AudioData(
        filename="sample_medical_conversation.wav",
        file_path="/data/sample_medical_conversation.wav",
        file_size=2048000,
        duration=125.3,
        format="wav",
        metadata=AudioMetadata(
            speaker_id="patient_001",
            recording_date=datetime.now(),
            sample_rate=44100,
            channels=1,
            bit_depth=16,
            tags=["medical", "consultation"]
        )
    )
    
    # 3. 데이터베이스에 삽입
    print("3. 데이터베이스에 삽입 중...")
    audio_id = await insert_audio_data(sample_audio)
    print(f"   삽입된 오디오 ID: {audio_id}")
    
    # 4. 전사 데이터 생성 및 업데이트
    print("4. 전사 데이터 생성 및 업데이트 중...")
    
    # 단어별 데이터
    words1 = [
        WordData(text="안녕하세요", start_time=0.0, end_time=1.0, confidence=0.95),
        WordData(text="저는", start_time=1.1, end_time=1.3, confidence=0.92),
        WordData(text="홍길동이라고", start_time=1.4, end_time=2.1, confidence=0.88),
        WordData(text="합니다", start_time=2.2, end_time=2.8, confidence=0.94)
    ]
    
    words2 = [
        WordData(text="제", start_time=3.0, end_time=3.2, confidence=0.96),
        WordData(text="전화번호는", start_time=3.3, end_time=4.0, confidence=0.93),
        WordData(text="010-1234-5678", start_time=4.1, end_time=5.5, confidence=0.87),
        WordData(text="입니다", start_time=5.6, end_time=6.0, confidence=0.95)
    ]
    
    # 문장별 데이터
    sentences = [
        SentenceData(
            text="안녕하세요, 저는 홍길동이라고 합니다.",
            start_time=0.0,
            end_time=2.8,
            words=words1
        ),
        SentenceData(
            text="제 전화번호는 010-1234-5678입니다.",
            start_time=3.0,
            end_time=6.0,
            words=words2
        )
    ]
    
    # 전사 데이터
    transcription = TranscriptionData(
        sentences=sentences,
        language="ko",
        transcription_engine="whisper-large-v3"
    )
    
    # 전사 데이터 업데이트
    await update_transcription_data(audio_id, transcription)
    print("   전사 데이터 업데이트 완료")
    
    # 5. 개인정보 데이터 추가
    print("5. 개인정보 데이터 추가 중...")
    
    personal_info_list = [
        PersonalInfoData(
            type="NAME",
            value="홍길동",
            masked_value="[이름]",
            start_time=1.4,
            end_time=2.1,
            word_index=2,
            sentence_index=0,
            confidence_score=0.92
        ),
        PersonalInfoData(
            type="PHONE_NUMBER",
            value="010-1234-5678",
            masked_value="[전화번호]",
            start_time=4.1,
            end_time=5.5,
            word_index=2,
            sentence_index=1,
            confidence_score=0.95
        )
    ]
    
    await add_personal_info(audio_id, personal_info_list)
    print("   개인정보 데이터 추가 완료")
    
    # 6. 데이터 조회
    print("6. 데이터 조회 중...")
    retrieved_audio = await get_audio_data(audio_id)
    if retrieved_audio:
        print(f"   파일명: {retrieved_audio.filename}")
        print(f"   재생시간: {retrieved_audio.duration}초")
        print(f"   전사 문장 수: {len(retrieved_audio.transcription.sentences) if retrieved_audio.transcription else 0}")
        print(f"   개인정보 개수: {len(retrieved_audio.transcription.personal_info) if retrieved_audio.transcription else 0}")
    
    # 7. 개인정보 유형별 검색
    print("7. 개인정보 유형별 검색 중...")
    name_audio_list = await search_by_personal_info_type("NAME")
    print(f"   이름이 포함된 오디오 파일 수: {len(name_audio_list)}")
    
    phone_audio_list = await search_by_personal_info_type("PHONE_NUMBER")
    print(f"   전화번호가 포함된 오디오 파일 수: {len(phone_audio_list)}")
    
    # 8. 통계 조회
    print("8. 데이터베이스 통계 조회 중...")
    stats = await get_statistics()
    print(f"   전체 오디오 파일 수: {stats['total_audio_files']}")
    print(f"   처리 상태별 분포: {stats['status_breakdown']}")
    print(f"   개인정보 유형별 분포: {stats['personal_info_types']}")

def example_queries():
    """MongoDB 쿼리 예제"""
    print("\n=== MongoDB 쿼리 예제 ===")
    
    print("""
    1. 특정 개인정보 유형이 포함된 오디오 검색:
    db.audio_data.find({
        "transcription.personal_info.type": "PHONE_NUMBER"
    })
    
    2. 특정 시간대의 전사 데이터 검색:
    db.audio_data.find({
        "transcription.sentences": {
            "$elemMatch": {
                "start_time": {"$gte": 10},
                "end_time": {"$lte": 20}
            }
        }
    })
    
    3. 특정 화자의 오디오 검색:
    db.audio_data.find({
        "metadata.speaker_id": "patient_001"
    })
    
    4. 특정 기간에 생성된 오디오 검색:
    db.audio_data.find({
        "created_at": {
            "$gte": ISODate("2024-01-01"),
            "$lt": ISODate("2024-12-31")
        }
    })
    
    5. 개인정보가 포함된 문장 검색:
    db.audio_data.aggregate([
        {"$unwind": "$transcription.sentences"},
        {"$unwind": "$transcription.personal_info"},
        {"$match": {
            "transcription.personal_info.sentence_index": "$transcription.sentences.index"
        }},
        {"$project": {
            "filename": 1,
            "sentence": "$transcription.sentences.text",
            "personal_info": "$transcription.personal_info"
        }}
    ])
    
    6. 개인정보 유형별 통계:
    db.audio_data.aggregate([
        {"$unwind": "$transcription.personal_info"},
        {"$group": {
            "_id": "$transcription.personal_info.type",
            "count": {"$sum": 1},
            "files": {"$addToSet": "$filename"}
        }}
    ])
    """)

if __name__ == "__main__":
    print("MongoDB 사용 예제 실행 중...")
    
    # 비동기 함수 실행
    asyncio.run(example_usage())
    
    # 쿼리 예제 출력
    example_queries()
    
    print("\n예제 실행 완료!") 