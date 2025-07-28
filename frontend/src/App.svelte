<script>
  import { onMount } from 'svelte';
  
  let audioFiles = [];
  let jsonFiles = [];
  let selectedAudio = null;
  let selectedJson = null;
  let jsonContent = null;

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
      jsonContent = await response.json();
      selectedJson = filename;
    } catch (error) {
      console.error('JSON 파일을 불러오는데 실패했습니다:', error);
    }
  }

  function handleAudioSelect(filename) {
    selectedAudio = filename;
  }
</script>

<main>
  <div class="container">
    <div class="audio-section">
      <h2>오디오 파일</h2>
      <div class="file-list">
        {#each audioFiles as file}
          <div
            class="file-item"
            class:selected={selectedAudio === file}
            on:click={() => handleAudioSelect(file)}
          >
            {file}
          </div>
        {/each}
      </div>
      {#if selectedAudio}
        <div class="audio-player">
          <audio controls src={`/api/audio/${selectedAudio}`}>
            <track kind="captions" />
          </audio>
        </div>
      {/if}
    </div>

    <div class="json-section">
      <h2>JSON 파일</h2>
      <div class="file-list">
        {#each jsonFiles as file}
          <div
            class="file-item"
            class:selected={selectedJson === file}
            on:click={() => loadJsonContent(file)}
          >
            {file}
          </div>
        {/each}
      </div>
      {#if jsonContent}
        <div class="json-viewer">
          <pre>{JSON.stringify(jsonContent, null, 2)}</pre>
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
  .json-section {
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
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
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

  .json-viewer {
    background: white;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
  }

  pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
</style>
