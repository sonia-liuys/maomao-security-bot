/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Configure allowed origins for development - include all possible IP patterns
  experimental: {
    allowedDevOrigins: [
      'localhost', 
      '127.0.0.1', 
      '192.168.1.147',
      '192.168.1.*',
      'security-bot.local'
    ],
  },
  // Disable strict mode for external URLs
  images: {
    domains: ['localhost', '127.0.0.1', '192.168.1.147', 'security-bot.local'],
  },
  // Add CORS headers for API routes if needed
  async headers() {
    return [
      {
        // Apply these headers to all routes
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
