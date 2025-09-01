const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
	// Only proxy API calls. Avoid proxying frontend routes like /recordings or /transcripts
	app.use(
		'/api',
		createProxyMiddleware({
			target: 'http://localhost:5000',
			changeOrigin: true,
			logLevel: 'silent',
		})
	);
};


