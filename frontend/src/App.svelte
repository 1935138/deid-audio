<script>
  import { onMount } from 'svelte';
  
  let audioFiles = [];
  let jsonFiles = [];
  let processedFiles = [];
  let selectedAudio = null;
  let selectedJson = null;
  let jsonContent = null;
  let audioPlayer;
  let currentSegment = null;
  let transcriptViewer;
  let showProcessedFiles = true;

  // JSON 파일명에서 기본 ID를 추출하는 함수
  function extractBaseId(filename) {
    // 예: "202103230700001_ai-stt-relay001_20250804_080954.json" -> "202103230700001_ai-stt-relay001"
    const match = filename.match(/^(\d+_ai-stt-relay\d+)/);
    return match ? match[1] : null;
  }

  // 기본 ID에 매칭되는 오디오 파일을 찾는 함수
  function findMatchingAudioFile(baseId) {
    return audioFiles.find(file => file.startsWith(baseId));
  }

  onMount(async () => {
    try {
      console.log('API 호출 시작...');
      const [filesResponse, processedResponse] = await Promise.all([
        fetch('/api/files'),
        fetch('/api/processed-files')
      ]);
      
      console.log('files API 응답:', filesResponse);
      console.log('processed API 응답:', processedResponse);
      
      const filesData = await filesResponse.json();
      const processedData = await processedResponse.json();
      
      console.log('files 데이터:', filesData);
      console.log('processed 데이터:', processedData);
      
      audioFiles = filesData.audioFiles;
      jsonFiles = filesData.jsonFiles;
      processedFiles = processedData.files || [];

      console.log('상태 업데이트 완료:', {
        audioFiles,
        jsonFiles,
        processedFiles
      });
    } catch (error) {
      console.error('파일 목록을 불러오는데 실패했습니다:', error);
    }
  });

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'});
  }

  async function loadJsonContent(filename) {
    try {
      console.log('🔄 JSON 파일 로드 시작:', filename);
      const response = await fetch(`/api/json/${filename}`);
      console.log('📡 API 응답 상태:', response.status);
      
      const data = await response.json();
      console.log('📊 전체 데이터:', data);
      console.log('📝 세그먼트 개수:', data.segments?.length);
      console.log('📋 처음 2개 세그먼트:', data.segments?.slice(0, 2));
      
      // PII 데이터 검사
      if (data.segments) {
        console.log('🔍 PII 데이터 검사 시작...');
        const allPiiWords = [];
        data.segments.forEach(segment => {
          if (segment.words) {
            segment.words.forEach(word => {
              if (word.is_pii === true) {
                allPiiWords.push(word);
              }
            });
          }
        });
        console.log('🔢 전체 PII 단어 개수:', allPiiWords.length);
        console.log('📝 PII 단어 예시:', allPiiWords.slice(0, 5));
      } else {
        console.warn('⚠️ segments 데이터가 없습니다!');
      }
      
      jsonContent = data;
      selectedJson = filename;

      // JSON 파일에서 기본 ID를 추출하고 매칭되는 오디오 파일을 찾아 자동 선택
      const baseId = extractBaseId(filename);
      if (baseId) {
        const matchingAudioFile = findMatchingAudioFile(baseId);
        if (matchingAudioFile) {
          selectedAudio = matchingAudioFile;
        } else {
          console.warn('매칭되는 오디오 파일을 찾을 수 없습니다:', baseId);
        }
      }
    } catch (error) {
      console.error('JSON 파일을 불러오는데 실패했습니다:', error);
    }
  }

  function handleAudioSelect(filename) {
    selectedAudio = filename;
  }

  function formatTime(seconds) {
    if (typeof seconds !== 'number' || isNaN(seconds)) {
      console.warn('Invalid time value:', seconds);
      return '00:00.000';
    }

    try {
      // 음수 시간을 0으로 처리
      seconds = Math.max(0, seconds);
      
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      const msecs = Math.round((seconds % 1) * 1000);
      
      // msecs가 1000이 되는 경우 처리
      if (msecs === 1000) {
        return `${String(mins).padStart(2, '0')}:${String(secs + 1).padStart(2, '0')}.000`;
      }
      
      return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(msecs).padStart(3, '0')}`;
    } catch (error) {
      console.error('Time formatting error:', error);
      return '00:00.000';
    }
  }

  function updateCurrentSegment(time) {
    if (jsonContent && jsonContent.segments && isFinite(time) && time >= 0) {
      const segment = jsonContent.segments.find(seg => {
        const start = parseFloat(seg.start) || 0;
        const end = parseFloat(seg.end) || 0;
        return time >= start && time <= end;
      });
      
      if (segment && segment !== currentSegment) {
        currentSegment = segment;
        // 현재 세그먼트로 스크롤
        const segmentElement = document.querySelector(`[data-segment-id="${segment.id}"]`);
        if (segmentElement && transcriptViewer) {
          segmentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  }

  function handleTimeUpdate(event) {
    const currentTime = event.target.currentTime;
    updateCurrentSegment(currentTime);
  }

  function playSegment(segment) {
    if (!audioPlayer || !segment) {
      console.warn('오디오 플레이어가 없거나 세그먼트가 없습니다.');
      return;
    }
    
    // 오디오가 로드되지 않았으면 return
    if (audioPlayer.readyState < 1) {
      console.warn('오디오가 아직 로드되지 않았습니다.');
      return;
    }
    
    try {
      const startTime = parseFloat(segment.start || segment.start_time) || 0;
      if (isFinite(startTime) && startTime >= 0 && startTime <= audioPlayer.duration) {
        audioPlayer.currentTime = startTime;
        audioPlayer.play().catch(error => {
          console.error('오디오 재생 실패:', error);
        });
        currentSegment = segment;
      } else {
        console.warn('유효하지 않은 시간 값:', startTime, '오디오 길이:', audioPlayer.duration);
      }
    } catch (error) {
      console.error('playSegment 오류:', error);
    }
  }

  function handleWordClick(segment, wordInfo) {
    if (!audioPlayer) {
      console.warn('오디오 플레이어가 없습니다.');
      return;
    }
    
    // 오디오가 로드되지 않았으면 return
    if (audioPlayer.readyState < 1) {
      console.warn('오디오가 아직 로드되지 않았습니다.');
      return;
    }
    
    try {
      const startTime = parseFloat(wordInfo.start || segment.start) || 0;
      if (isFinite(startTime) && startTime >= 0 && startTime <= audioPlayer.duration) {
        audioPlayer.currentTime = startTime;
        audioPlayer.play().catch(error => {
          console.error('오디오 재생 실패:', error);
        });
      } else {
        console.warn('유효하지 않은 단어 시간 값:', startTime, '오디오 길이:', audioPlayer.duration);
      }
    } catch (error) {
      console.error('handleWordClick 오류:', error);
    }
  }

  function getWords(text, segment) {
    if (!segment.words) {
      return [{text: text, start: segment.start}];
    }
    // words 배열의 각 항목을 text 속성을 가진 형태로 변환
    const words = segment.words.map(w => ({
      text: w.word,
      start: w.start,
      end: w.end,
      is_pii: w.is_pii
    }));
    
    // PII 단어가 있는지 디버깅
    const piiWords = words.filter(w => w.is_pii);
    if (piiWords.length > 0) {
      console.log('PII 단어 발견:', piiWords);
    }
    
    return words;
  }
</script>

<main class="main-container">
  <div class="container">
    <!-- 좌측 영역: 전사 파일 목록 (1) -->
    <div class="file-list-section">
      <div class="tabs">
        <button 
          class="tab"
          class:active={showProcessedFiles}
          on:click={() => showProcessedFiles = true}
        >
          Processed 파일 ({processedFiles.length})
        </button>
        <button 
          class="tab"
          class:active={!showProcessedFiles}
          on:click={() => showProcessedFiles = false}
        >
          전체 파일 ({jsonFiles.length})
        </button>
      </div>

      {#if showProcessedFiles}
        <div class="file-list">
          <h3>Processed JSON 파일</h3>
          {#each processedFiles as file}
            <div class="processed-file-item" class:selected={selectedJson === file.name}>
              <button
                class="file-name-btn"
                on:click={() => {
                  console.log('🖱️ 파일 클릭됨:', file.name);
                  loadJsonContent(file.name);
                }}
              >
                {file.name}
              </button>
              <div class="file-info">
                <span class="file-size">{formatFileSize(file.size)}</span>
                <span class="file-date">{formatDate(file.modified)}</span>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="file-list">
          <h3>전체 전사 파일</h3>
          {#each jsonFiles as file}
            <button
              class="file-item"
              class:selected={selectedJson === file}
              on:click={() => {
                console.log('🖱️ 전체 파일 클릭됨:', file);
                loadJsonContent(file);
              }}
            >
              {file}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <!-- 우측 영역: 오디오 플레이어 및 전사 내용 -->
    <div class="content-section">
      <!-- 상단: 오디오 플레이어 -->
      {#if selectedAudio}
        <div class="audio-player-section">
          <audio
            controls
            bind:this={audioPlayer}
            src={`/api/audio/${selectedAudio}`}
            on:timeupdate={handleTimeUpdate}
          >
            <track kind="captions" />
          </audio>
        </div>
      {/if}

      <!-- 하단: 전사 내용 -->
      {#if jsonContent && jsonContent.segments}
        <div class="transcript-viewer" bind:this={transcriptViewer}>
          {#each jsonContent.segments as segment}
            <div
              class="segment"
              class:current={currentSegment === segment}
              on:click={(e) => {
                e.preventDefault();
                e.stopPropagation();
                playSegment(segment);
              }}
              role="button"
              tabindex="0"
              on:keydown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  playSegment(segment);
                }
              }}
              data-segment-id={segment.id}
            >
              <div class="segment-header">
                <span class="segment-time">
                  {formatTime(parseFloat(segment.start) || 0)} - {formatTime(parseFloat(segment.end) || 0)}
                </span>
                <span class="segment-duration">
                  (길이: {formatTime((parseFloat(segment.end) || 0) - (parseFloat(segment.start) || 0))})
                </span>
              </div>
              <div class="segment-text">
                {#each getWords(segment.text, segment) as word}
                  <span 
                    class="word"
                    class:pii={word.is_pii}
                    style={word.is_pii ? 'background-color: #9fff9c !important; border: 2px solid red;' : ''}
                    on:click={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleWordClick(segment, word);
                    }}
                    role="button"
                    tabindex="0"
                    on:keydown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleWordClick(segment, word);
                      }
                    }}
                    title={`PII: ${word.is_pii}`}
                  >
                    {word.text}
                  </span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</main>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(html, body) {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
  }

  :global(#app) {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
  }

  .main-container {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh;
    margin: 0;
    padding: 0;
    overflow: hidden;
    display: flex;
    background: #e0e0e0;
  }

  .container {
    display: flex;
    gap: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  /* 좌측 영역: 1 비율 */
  .file-list-section {
    flex: 1;
    height: 100%;
    background: #f5f5f5;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border-right: 1px solid #ddd;
  }

  /* 우측 영역: 3 비율 */
  .content-section {
    flex: 3;
    flex-direction: column;
    height: 100%;
    display: flex;
    gap: 1rem;
    background: #f5f5f5;
    padding: 1rem;
    overflow: hidden;
  }

  .audio-player-section {
    background: white;
    padding: 1rem;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    height: 120px;
    display: flex;
    align-items: center;
  }

  audio {
    width: 100%;
    height: 50px;
  }

  h2 {
    margin: 0 0 1rem 0;
    color: #333;
    font-size: 1.2rem;
    font-weight: 600;
  }

  h3 {
    margin: 0 0 1rem 0;
    color: #333;
    font-size: 1rem;
    font-weight: 500;
  }

  .tabs {
    display: flex;
    margin-bottom: 1rem;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .tab {
    flex: 1;
    padding: 0.75rem 1rem;
    background: white;
    border: none;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
    color: #666;
  }

  .tab:hover {
    background: #f8f9fa;
  }

  .tab.active {
    background: #007bff;
    color: white;
  }

  .processed-file-item {
    background: white;
    border-radius: 6px;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
  }

  .processed-file-item:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }

  .processed-file-item.selected {
    box-shadow: 0 2px 6px rgba(0, 123, 255, 0.3);
    border: 2px solid #007bff;
  }

  .file-name-btn {
    width: 100%;
    padding: 0.75rem;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    color: #333;
    word-break: break-all;
  }

  .processed-file-item.selected .file-name-btn {
    color: #007bff;
  }

  .file-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 0.75rem 0.75rem 0.75rem;
    font-size: 0.75rem;
    color: #666;
    border-top: 1px solid #f0f0f0;
  }

  .file-size {
    font-weight: 500;
    color: #007bff;
  }

  .file-date {
    color: #999;
  }

  .file-list {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow-y: auto;
    padding-right: 0.5rem;
  }

  .file-list::-webkit-scrollbar {
    width: 6px;
  }

  .file-list::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }

  .file-list::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 3px;
  }

  .file-list::-webkit-scrollbar-thumb:hover {
    background: #666;
  }

  .file-item {
    padding: 0.75rem;
    background: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    font-size: 0.9rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .file-item:hover {
    background: #f0f0f0;
    transform: translateY(-1px);
  }

  .file-item.selected {
    background: #007bff;
    color: white;
    box-shadow: 0 1px 3px rgba(0, 123, 255, 0.3);
  }

  .transcript-viewer {
    flex: 1;
    background: white;
    padding: 1rem;
    border-radius: 4px;
    overflow-y: auto;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    height: calc(100% - 140px);
  }

  .segment {
    padding: 1rem;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .segment:hover {
    background-color: #f8f9fa;
  }

  .segment.current {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
  }

  .segment-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
    font-family: monospace;
  }

  .segment-time {
    color: #2196f3;
    font-weight: bold;
  }

  .segment-duration {
    color: #666;
    font-size: 0.9em;
  }

  .segment-text {
    line-height: 1.5;
    font-size: 1.1em;
  }

  .word {
    display: inline-block;
    padding: 0 2px;
    cursor: pointer;
    border-radius: 2px;
  }

  .word:hover {
    background-color: #e3f2fd;
  }

  .word.pii {
    color: inherit;
    background-color: #9fff9c;
    box-shadow: 0 0 3px rgba(0, 255, 0, 0.3);
    padding: 0 4px;
    border-radius: 2px;
  }
</style>
