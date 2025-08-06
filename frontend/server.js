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
app.use(express.json()); // JSON 파싱 미들웨어 추가

// 정적 파일 서빙 설정
app.use(express.static(path.join(__dirname, 'dist')));

// 서버 시작 로그
app.listen(PORT, () => {
  console.log(`서버가 http://localhost:${PORT} 에서 실행 중입니다.`);
});

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
// CORS 설정 추가
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

app.get('/api/files', async (req, res) => {
  try {
    console.log('GET /api/files 요청 받음');
    const dataDir = path.join(__dirname, '..', 'data', 'raw');
    const processedDir = path.join(__dirname, '..', 'output', 'processed');

    console.log('디렉토리 경로:', {
      dataDir,
      processedDir
    });

    const [audioFiles, jsonFiles] = await Promise.all([
      fs.readdir(dataDir),
      fs.readdir(processedDir)
    ]);

    console.log('파일 목록:', {
      audioFiles,
      jsonFiles
    });

    const response = {
      audioFiles: audioFiles.filter(file => file.match(/\.(wav|mp3)$/)),
      jsonFiles: jsonFiles.filter(file => file.endsWith('.json'))
    };

    console.log('응답 데이터:', response);
    res.json(response);
  } catch (error) {
    console.error('Error reading directory:', error);
    res.status(500).json({ error: '파일 목록을 가져오는데 실패했습니다.' });
  }
});

// processed 디렉토리 전용 API
app.get('/api/processed-files', async (req, res) => {
  try {
    console.log('GET /api/processed-files 요청 받음');
    const processedDir = path.join(__dirname, '..', 'output', 'processed');
    console.log('processed 디렉토리 경로:', processedDir);
    
    const files = await fs.readdir(processedDir);
    console.log('전체 파일 목록:', files);
    
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    console.log('JSON 파일 목록:', jsonFiles);
    
    // 파일 정보와 함께 반환 (파일 크기, 수정 날짜 등)
    const fileDetails = await Promise.all(
      jsonFiles.map(async (file) => {
        const filePath = path.join(processedDir, file);
        const stats = await fs.stat(filePath);
        return {
          name: file,
          size: stats.size,
          modified: stats.mtime,
          created: stats.birthtime
        };
      })
    );

    const response = {
      files: fileDetails,
      count: jsonFiles.length
    };
    
    console.log('응답 데이터:', response);
    res.json(response);
  } catch (error) {
    console.error('Error reading processed directory:', error);
    console.error(error);
    res.status(500).json({ error: 'processed 파일 목록을 가져오는데 실패했습니다.' });
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
  const filepath = path.join(__dirname, '..', 'output', 'processed', filename);

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

// JSON 파일 업데이트를 위한 PUT 엔드포인트
app.put('/api/json/:filename', async (req, res) => {
  const filename = req.params.filename;
  const filepath = path.join(__dirname, '..', 'output', 'processed', filename);
  const updatedData = req.body;

  try {
    // 파일이 존재하는지 확인
    await fs.access(filepath);
    
    // 업데이트된 데이터를 파일에 저장
    await fs.writeFile(filepath, JSON.stringify(updatedData, null, 2), 'utf-8');
    
    console.log(`JSON 파일 업데이트 완료: ${filename}`);
    
    // PII 변경 통계 로깅
    if (updatedData.segments) {
      const totalWords = updatedData.segments.reduce((count, segment) => {
        return count + (segment.words ? segment.words.length : 0);
      }, 0);
      
      const piiWords = updatedData.segments.reduce((count, segment) => {
        return count + (segment.words ? segment.words.filter(word => word.is_pii).length : 0);
      }, 0);
      
      console.log(`PII 통계 - 전체 단어: ${totalWords}, PII 단어: ${piiWords}`);
    }
    
    res.json({ 
      success: true, 
      message: '파일이 성공적으로 업데이트되었습니다.',
      filename: filename
    });
  } catch (error) {
    console.error('Error updating JSON file:', error);
    if (error.code === 'ENOENT') {
      res.status(404).json({ error: 'JSON 파일을 찾을 수 없습니다.' });
    } else {
      res.status(500).json({ error: 'JSON 파일 업데이트에 실패했습니다.' });
    }
  }
});

// 기본 라우트 - SPA를 위한 설정
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
}); 