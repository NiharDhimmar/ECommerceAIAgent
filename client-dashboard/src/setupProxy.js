const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
	// Only proxy API calls. Avoid proxying frontend routes like /recordings or /transcripts
	app.use(
		'/api',
		createProxyMiddleware({
			target: 'http://127.0.0.1:5000',
			changeOrigin: true,
			logLevel: 'debug',
			ws: false,
			proxyTimeout: 120000,
			timeout: 120000,
			onError(err, req, res) {
				console.error('Proxy error:', err?.code || err?.message || err);
				if (!res.headersSent) {
					res.writeHead(502, { 'Content-Type': 'application/json' });
				}
				res.end(JSON.stringify({ error: 'Proxy error', details: String(err?.code || err?.message || err) }));
			},
		})
	);
};
