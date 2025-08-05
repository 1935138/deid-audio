import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { promises as fs } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(cors());

// 정적 파일 서빙 설정
app.use(express.static(path.join(__dirname, 'dist')));

// 시간 값을 숫자로 변환하는 함수
function normalizeTimeValues(segments) {
  return segments.map(segment => ({
    ...segment,
    start: parseFloat(segment.start) || 0,
    end: parseFloat(segment.end) || 0,
    words: segment.words?.map(word => ({
      ...word,
      start: parseFloat(word.start) || 0,
      end: parseFloat(word.end) || 0
    }))
  }));
}

// API 라우트들
app.get('/api/files', async (req, res) => {
  try {
    const dataDir = path.join(__dirname, '..', 'data', 'raw');
    const outputDir = path.join(__dirname, '..', 'output');

    const [audioFiles, jsonFiles] = await Promise.all([
      fs.readdir(dataDir),
      fs.readdir(outputDir)
    ]);

    res.json({
      audioFiles: audioFiles.filter(file => file.match(/\.(wav|mp3)$/)),
      jsonFiles: jsonFiles.filter(file => file.endsWith('.json'))
    });
  } catch (error) {
    console.error('Error reading directory:', error);
    res.status(500).json({ error: '파일 목록을 가져오는데 실패했습니다.' });
  }
});

app.get('/api/audio/:filename', async (req, res) => {
  const filename = req.params.filename;
  const filepath = path.join(__dirname, '..', 'data', 'raw', filename);

  try {
    await fs.access(filepath);
    res.sendFile(filepath);
  } catch (error) {
    res.status(404).json({ error: '파일을 찾을 수 없습니다.' });
  }
});

app.get('/api/json/:filename', async (req, res) => {
  const filename = req.params.filename;
  const filepath = path.join(__dirname, '..', 'output', filename);

  try {
    const content = await fs.readFile(filepath, 'utf-8');
    const jsonData = JSON.parse(content);
    
    if (jsonData.segments) {
      jsonData.segments = normalizeTimeValues(jsonData.segments);
    }
    
    res.json(jsonData);
  } catch (error) {
    console.error('Error reading JSON file:', error);
    res.status(404).json({ error: 'JSON 파일을 찾을 수 없습니다.' });
  }
});

// 기본 라우트 - SPA를 위한 설정
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
}); 