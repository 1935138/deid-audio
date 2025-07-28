import os
from faster_whisper import WhisperModel

def main():
    """
    faster-whisper를 사용하여 음성 파일을 전사하는 메인 함수
    """
    # 모델 크기 설정 (tiny, base, small, medium, large-v2, large-v3)
    model_size = "medium"
    
    # 모델 로드 (GPU 사용 시도, 실패하면 CPU로 대체)
    print(f"Whisper 모델 ({model_size}) 로딩 중...")
    
    # GPU 먼저 시도
    try:
        print("GPU 모드로 시도 중...")
        model = WhisperModel(model_size, device="cuda", compute_type="int8")
        print("GPU 모드 로딩 완료!")
    except Exception as e:
        print(f"GPU 모드 실패: {e}")
        print("CPU 모드로 대체 중...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("CPU 모드 로딩 완료!")
    
    # 음성 파일 경로 설정
    audio_file_path = "data/202503201100007_amone-relay-prod.wav"  # 실제 음성 파일 경로로 변경
    
    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        print(f"오류: 음성 파일을 찾을 수 없습니다 - {audio_file_path}")
        print("data/ 폴더에 음성 파일을 넣어주세요.")
        return
    
    print(f"음성 파일 전사 시작: {audio_file_path}")
    
    # 음성 파일 전사
    # language="ko" 옵션으로 한국어 전사 최적화 가능
    segments, info = model.transcribe(
        audio_file_path, 
        language="ko",  # 한국어 설정 (None으로 설정시 자동 감지)
        beam_size=5,    # 빔 서치 크기
        word_timestamps=True  # 단어별 타임스탬프 포함
    )
    
    print(f"감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
    print(f"전체 길이: {info.duration:.2f}초")
    print("\n=== 전사 결과 ===")
    
    # 결과 출력 및 저장
    full_text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        full_text += segment.text + " "
        
        # 단어별 타임스탬프 출력 (옵션)
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                print(f"  - {word.word} [{word.start:.2f}s-{word.end:.2f}s]")
    
    # 결과를 텍스트 파일로 저장
    output_file = "transcription_result.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"음성 파일: {audio_file_path}\n")
        f.write(f"감지된 언어: {info.language}\n")
        f.write(f"전체 길이: {info.duration:.2f}초\n")
        f.write("\n=== 전사 결과 ===\n")
        f.write(full_text.strip())
    
    print(f"\n전사 결과가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    main() 