module.exports = {
  devServer: {
    proxy: {
      '/api/ningbopoc': {
        target: 'http://navi.miscity.cn:48080',
        changeOrigin: true,
        ws: true,
        onProxyReq(proxyReq) {
          proxyReq.setHeader('Connection', 'keep-alive');
        }
      },
      '/api': {
        target: 'http://navi.miscity.cn:48888',
        changeOrigin: true,
        ws: true,
        onProxyReq(proxyReq) {
          proxyReq.setHeader('Connection', 'keep-alive');
        }
      }
    }
  }
}
