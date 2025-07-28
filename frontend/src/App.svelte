<script>
  import { onMount } from 'svelte';
  
  let audioFiles = [];
  let jsonFiles = [];
  let selectedAudio = null;
  let selectedJson = null;
  let jsonContent = null;
  let audioPlayer;
  let currentSegment = null;

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
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      const msecs = Math.round((seconds % 1) * 1000);
      
      return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(msecs).padStart(3, '0')}`;
    } catch (error) {
      console.error('Time formatting error:', error);
      return '00:00.000';
    }
  }

  function playSegment(segment) {
    if (audioPlayer && segment) {
      console.log('Playing segment:', {
        start: segment.start_time,
        end: segment.end_time,
        type: typeof segment.start_time
      });
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
    return segment.words;
  }
</script>

<main>
  <div class="container">
    <div class="audio-section">
      <h2>오디오 파일</h2>
      <div class="file-list">
        {#each audioFiles as file}
          <button
            class="file-item"
            class:selected={selectedAudio === file}
            on:click={() => handleAudioSelect(file)}
          >
            {file}
          </button>
        {/each}
      </div>
      {#if selectedAudio}
        <div class="audio-player">
          <audio
            controls
            bind:this={audioPlayer}
            src={`/api/audio/${selectedAudio}`}
          >
            <track kind="captions" />
          </audio>
        </div>
      {/if}
    </div>

    <div class="transcript-section">
      <h2>전사 파일</h2>
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
      {#if jsonContent && jsonContent.segments}
        <div class="transcript-viewer">
          {#each jsonContent.segments as segment}
            <div
              class="segment"
              class:current={currentSegment === segment}
              on:click={() => playSegment(segment)}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && playSegment(segment)}
            >
              <div class="segment-header">
                <span class="segment-time">
                  {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                </span>
                <span class="segment-duration">
                  (길이: {formatTime(segment.end_time - segment.start_time)})
                </span>
              </div>
              <div class="segment-text">
                {segment.text}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</main>

<style>
  .container {
    display: flex;
    gap: 2rem;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .audio-section,
  .transcript-section {
    flex: 1;
    background: #f5f5f5;
    border-radius: 8px;
    padding: 1rem;
  }

  h2 {
    margin-top: 0;
    color: #333;
  }

  .file-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .file-item {
    padding: 0.5rem;
    background: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
    text-align: left;
    font-size: 1rem;
  }

  .file-item:hover {
    background: #e0e0e0;
  }

  .file-item.selected {
    background: #007bff;
    color: white;
  }

  .audio-player {
    margin-top: 1rem;
  }

  audio {
    width: 100%;
  }

  .transcript-viewer {
    background: white;
    padding: 1rem;
    border-radius: 4px;
    overflow-y: auto;
    max-height: 600px;
  }

  .segment {
    padding: 1rem;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .segment:hover {
    background-color: #f0f0f0;
  }

  .segment.current {
    background-color: #e3f2fd;
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
    border-radius: 2px;
    cursor: pointer;
  }

  .word:hover {
    background-color: #007bff;
    color: white;
  }
</style>
