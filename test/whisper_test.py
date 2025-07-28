import os
import whisper
import time

def test_whisper_basic():
    """
    Whisper 모델의 기본 음성 인식 기능을 테스트하는 함수
    """
    print("=== Whisper 기본 음성 인식 테스트 ===")
    
    # 모델 크기 설정 (tiny, base, small, medium, large-v2)
    model_size = "medium"
    
    # 모델 로드
    print(f"Whisper 모델 ({model_size}) 로딩 중...")
    try:
        model = whisper.load_model(model_size)
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 테스트할 오디오 파일 경로 설정
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"오류: {data_dir} 디렉토리를 찾을 수 없습니다.")
        return
        
    audio_files = [f for f in os.listdir(data_dir) if f.endswith('.wav')]
    if not audio_files:
        print(f"오류: {data_dir} 디렉토리에 .wav 파일이 없습니다.")
        return
    
    results = []
    
    print("\n음성 인식 테스트 시작...")
    
    for audio_file in audio_files:
        audio_path = os.path.join(data_dir, audio_file)
        try:
            start_time = time.time()
            
            # 음성 파일 전사
            result = model.transcribe(
                audio_path,
                language="ko",  # 한국어 설정
                task="transcribe"  # transcribe 또는 translate
            )
            
            elapsed_time = time.time() - start_time
            
            results.append({
                "file": audio_file,
                "text": result["text"],
                "time": elapsed_time,
                "language": result.get("language", "unknown")
            })
            
            print(f"\n파일: {audio_file}")
            print(f"인식된 텍스트: {result['text']}")
            print(f"감지된 언어: {result.get('language', 'unknown')}")
            print(f"처리 시간: {elapsed_time:.2f}초")
            
        except Exception as e:
            print(f"처리 실패 ({audio_file}): {e}")
            results.append({
                "file": audio_file,
                "text": "실패",
                "error": str(e)
            })
    
    print("\n=== 테스트 결과 요약 ===")
    success_count = sum(1 for r in results if "error" not in r)
    print(f"성공: {success_count}/{len(audio_files)}")
    if success_count > 0:
        print(f"평균 처리 시간: {sum(r['time'] for r in results if 'time' in r) / success_count:.2f}초")

def test_whisper_segments():
    """
    Whisper 모델의 세그먼트 단위 음성 인식을 테스트하는 함수
    """
    print("\n=== Whisper 세그먼트 단위 음성 인식 테스트 ===")
    
    model_size = "medium"
    
    try:
        model = whisper.load_model(model_size)
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"오류: {data_dir} 디렉토리를 찾을 수 없습니다.")
        return
        
    audio_files = [f for f in os.listdir(data_dir) if f.endswith('.wav')]
    if not audio_files:
        print(f"오류: {data_dir} 디렉토리에 .wav 파일이 없습니다.")
        return
    
    # 첫 번째 오디오 파일에 대해서만 세그먼트 테스트 수행
    audio_path = os.path.join(data_dir, audio_files[0])
    
    print(f"\n파일 '{audio_files[0]}'에 대한 세그먼트 분석 시작...")
    
    try:
        start_time = time.time()
        
        # 음성 파일 전사 (세그먼트 정보 포함)
        result = model.transcribe(
            audio_path,
            language="ko",
            task="transcribe",
            verbose=True  # 진행 상황 표시
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n=== 세그먼트 단위 결과 ===")
        for segment in result["segments"]:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            print(f"\n[{start:.2f}s -> {end:.2f}s]")
            print(f"텍스트: {text}")
        
        print(f"\n총 세그먼트 수: {len(result['segments'])}")
        print(f"전체 처리 시간: {elapsed_time:.2f}초")
        
    except Exception as e:
        print(f"세그먼트 분석 실패: {e}")

if __name__ == "__main__":
    test_whisper_basic()
    test_whisper_segments() 