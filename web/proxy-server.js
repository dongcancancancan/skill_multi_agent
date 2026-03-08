const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();

// 静态文件服务
app.use(express.static(path.join(__dirname, 'dist')));

// SSE流优化中间件
const sseProxy = createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true,
  ws: true, // 启用WebSocket支持
  proxyTimeout: 0, // 无超时限制
  onProxyReq: (proxyReq, req, res) => {
    // 保持长连接
    proxyReq.setHeader('Connection', 'keep-alive');
    proxyReq.setHeader('Accept-Encoding', 'identity');
    console.log(`[SSE] 代理请求: ${req.method} ${req.url}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    // 确保SSE响应头正确传递
    proxyRes.headers['Cache-Control'] = 'no-cache';
    proxyRes.headers['X-Accel-Buffering'] = 'no';
  }
});

// 专门为SSE路由设置代理
app.use('/api/agents/main_graph', sseProxy);

// 其他API路由
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true
}));

// 启动服务器
const PORT = 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`代理服务器运行在 http://localhost:${PORT}`);
});
