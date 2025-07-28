import os
import whisper_timestamped as whisper
import json
from datetime import timedelta

def format_timestamp(seconds):
    """초를 hh:mm:ss.ms 형식으로 변환"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def main():
    """
    whisper_timestamped를 사용하여 정확한 단어별 타임스탬프와 함께 음성 파일을 전사하는 메인 함수
    """
    # 모델 크기 설정 (tiny, base, small, medium, large, large-v2, large-v3)
    model_size = "medium"
    
    print(f"Whisper Timestamped 모델 ({model_size}) 로딩 중...")
    
    # 모델 로드
    try:
        model = whisper.load_model(model_size)
        print("모델 로딩 완료!")
    except Exception as e:
        print(f"모델 로딩 실패: {e}")
        return
    
    # 음성 파일 경로 설정 (data 폴더의 첫 번째 파일 사용)
    data_dir = "data"
    audio_files = [f for f in os.listdir(data_dir) if f.endswith('.wav')]
    
    if not audio_files:
        print("오류: data/ 폴더에 .wav 파일을 찾을 수 없습니다.")
        return
    
    audio_file_path = os.path.join(data_dir, audio_files[0])
    print(f"음성 파일 전사 시작: {audio_file_path}")
    
    # 음성 파일 전사 (whisper_timestamped 사용)
    try:
        result = whisper.transcribe(
            model, 
            audio_file_path,
            language="ko",  # 한국어 설정
            verbose=True,   # 진행 상황 표시
            plot_word_alignment=False,  # 단어 정렬 플롯 비활성화
        )
        print("전사 완료!")
        
    except Exception as e:
        print(f"전사 실패: {e}")
        return
    
    print(f"감지된 언어: {result.get('language', 'N/A')}")
    print(f"전체 길이: {result.get('duration', 0):.2f}초")
    print("\n=== 전사 결과 (정확한 단어별 타임스탬프) ===")
    
    # 결과 출력 및 저장
    full_text = ""
    detailed_results = []
    
    for segment in result['segments']:
        segment_start = segment['start']
        segment_end = segment['end']
        segment_text = segment['text'].strip()
        
        print(f"\n[{format_timestamp(segment_start)} -> {format_timestamp(segment_end)}] {segment_text}")
        full_text += segment_text + " "
        
        segment_data = {
            "start": segment_start,
            "end": segment_end,
            "text": segment_text,
            "words": []
        }
        
        # 단어별 타임스탬프 출력
        if 'words' in segment:
            for word_info in segment['words']:
                word = word_info['text']
                word_start = word_info['start']
                word_end = word_info['end']
                confidence = word_info.get('confidence', 0)
                
                print(f"  └─ '{word}' [{format_timestamp(word_start)} - {format_timestamp(word_end)}] (신뢰도: {confidence:.3f})")
                
                segment_data['words'].append({
                    "word": word,
                    "start": word_start,
                    "end": word_end,
                    "confidence": confidence
                })
        
        detailed_results.append(segment_data)
    
    # 결과를 텍스트 파일로 저장
    base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
    
    # 텍스트 결과 저장
    txt_output_file = f"result/{base_filename}_timestamped.txt"
    os.makedirs("result", exist_ok=True)
    
    with open(txt_output_file, "w", encoding="utf-8") as f:
        f.write(f"음성 파일: {audio_file_path}\n")
        f.write(f"감지된 언어: {result.get('language', 'N/A')}\n")
        f.write(f"전체 길이: {result.get('duration', 0):.2f}초\n")
        f.write(f"모델: {model_size}\n")
        f.write(f"전사 도구: whisper_timestamped\n\n")
        f.write("=== 전사 결과 ===\n")
        f.write(full_text.strip())
        f.write("\n\n=== 상세 타임스탬프 ===\n")
        
        for segment_data in detailed_results:
            f.write(f"\n[{format_timestamp(segment_data['start'])} -> {format_timestamp(segment_data['end'])}] {segment_data['text']}\n")
            for word_data in segment_data['words']:
                f.write(f"  └─ '{word_data['word']}' [{format_timestamp(word_data['start'])} - {format_timestamp(word_data['end'])}] (신뢰도: {word_data['confidence']:.3f})\n")
    
    # JSON 결과 저장 (프로그래밍적 접근을 위해)
    json_output_file = f"result/{base_filename}_timestamped.json"
    
    output_data = {
        "audio_file": audio_file_path,
        "language": result.get('language', 'N/A'),
        "duration": result.get('duration', 0),
        "model": model_size,
        "tool": "whisper_timestamped",
        "full_text": full_text.strip(),
        "segments": detailed_results
    }
    
    with open(json_output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n전사 결과가 다음 파일들에 저장되었습니다:")
    print(f"- 텍스트 파일: {txt_output_file}")
    print(f"- JSON 파일: {json_output_file}")
    print(f"\n총 {len(detailed_results)}개 세그먼트, {sum(len(seg['words']) for seg in detailed_results)}개 단어가 전사되었습니다.")

if __name__ == "__main__":
    main() 