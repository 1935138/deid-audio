const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// 미들웨어 설정
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 정적 파일 제공 (frontend 폴더)
app.use(express.static(path.join(__dirname, 'frontend')));
app.use('/static', express.static(path.join(__dirname, 'static')));

// 기본 라우트
app.get('/', (req, res) => {
    res.json({
        message: 'Deid Audio Express Server가 실행 중입니다!',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

// API 라우트 예시
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
    });
});

// 404 핸들러
app.use('*', (req, res) => {
    res.status(404).json({
        error: '페이지를 찾을 수 없습니다',
        path: req.originalUrl
    });
});

// 에러 핸들러
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        error: '서버 내부 오류가 발생했습니다',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// 서버 시작
app.listen(PORT, () => {
    console.log(`🚀 Express 서버가 포트 ${PORT}에서 실행 중입니다`);
    console.log(`📁 정적 파일 경로: ${path.join(__dirname, 'frontend')}`);
    console.log(`🌐 서버 주소: http://localhost:${PORT}`);
});

module.exports = app;
