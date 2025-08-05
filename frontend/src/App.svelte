<script>
  import { onMount } from 'svelte';
  
  let audioFiles = [];
  let jsonFiles = [];
  let selectedAudio = null;
  let selectedJson = null;
  let jsonContent = null;
  let audioPlayer;
  let currentSegment = null;
  let transcriptViewer;

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
      const response = await fetch('/api/files');
      const data = await response.json();
      audioFiles = data.audioFiles;
      jsonFiles = data.jsonFiles;
    } catch (error) {
      console.error('파일 목록을 불러오는데 실패했습니다:', error);
    }
  });

  async function loadJsonContent(filename) {
    try {
      const response = await fetch(`/api/json/${filename}`);
      const data = await response.json();
      console.log('Loaded segments:', data.segments?.slice(0, 2));
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
    if (jsonContent && jsonContent.segments) {
      const segment = jsonContent.segments.find(seg => 
        time >= seg.start && time <= seg.end
      );
      
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
    if (audioPlayer && segment) {
      audioPlayer.currentTime = segment.start_time;
      audioPlayer.play();
      currentSegment = segment;
    }
  }

  function handleWordClick(segment, wordInfo) {
    if (audioPlayer) {
      audioPlayer.currentTime = wordInfo.start || segment.start;
      audioPlayer.play();
    }
  }

  function getWords(text, segment) {
    if (!segment.words) {
      return [{text: text, start: segment.start}];
    }
    // words 배열의 각 항목을 text 속성을 가진 형태로 변환
    return segment.words.map(w => ({
      text: w.word,
      start: w.start,
      end: w.end,
      pii_type: w.pii_type
    }));
  }
</script>

<main class="main-container">
  <div class="container">
    <!-- 좌측 영역: 전사 파일 목록 (1) -->
    <div class="file-list-section">
      <h2>전사 파일 목록</h2>
      <div class="file-list">
        {#each jsonFiles as file}
          <button
            class="file-item"
            class:selected={selectedJson === file}
            on:click={() => loadJsonContent(file)}
          >
            {file}
          </button>
        {/each}
      </div>
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
              on:click={() => playSegment(segment)}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && playSegment(segment)}
              data-segment-id={segment.id}
            >
              <div class="segment-header">
                <span class="segment-time">
                  {formatTime(segment.start)} - {formatTime(segment.end)}
                </span>
                <span class="segment-duration">
                  (길이: {formatTime(segment.end - segment.start)})
                </span>
              </div>
              <div class="segment-text">
                {#each getWords(segment.text, segment) as word}
                  <span 
                    class="word"
                    class:pii={word.pii_type}
                    on:click={() => handleWordClick(segment, word)}
                    role="button"
                    tabindex="0"
                    on:keydown={(e) => e.key === 'Enter' && handleWordClick(segment, word)}
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
