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
app.use(express.static('dist'));

// 파일 목록을 가져오는 API
app.get('/api/files', async (req, res) => {
  try {
    const dataDir = path.join(__dirname, '..', 'data');
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

// 오디오 파일을 스트리밍하는 API
app.get('/api/audio/:filename', async (req, res) => {
  const filename = req.params.filename;
  const filepath = path.join(__dirname, '..', 'data', filename);

  try {
    await fs.access(filepath);
    res.sendFile(filepath);
  } catch (error) {
    res.status(404).json({ error: '파일을 찾을 수 없습니다.' });
  }
});

// JSON 파일을 가져오는 API
app.get('/api/json/:filename', async (req, res) => {
  const filename = req.params.filename;
  const filepath = path.join(__dirname, '..', 'output', filename);

  try {
    const content = await fs.readFile(filepath, 'utf-8');
    res.json(JSON.parse(content));
  } catch (error) {
    res.status(404).json({ error: 'JSON 파일을 찾을 수 없습니다.' });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
}); 