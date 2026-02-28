/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Auth endpoints
      {
        source: '/register',
        destination: 'http://localhost:8000/register',
      },
      {
        source: '/token',
        destination: 'http://localhost:8000/token',
      },
      {
        source: '/me',
        destination: 'http://localhost:8000/me',
      },
      // Chat and Voice endpoints
      {
        source: '/chat',
        destination: 'http://localhost:8000/chat',
      },
      {
        source: '/voice',
        destination: 'http://localhost:8000/voice',
      },
      // Other API endpoints
      {
        source: '/medicines',
        destination: 'http://localhost:8000/medicines',
      },
      {
        source: '/medicine',
        destination: 'http://localhost:8000/medicine',
      },
      {
        source: '/create_order',
        destination: 'http://localhost:8000/create_order',
      },
      {
        source: '/patients/:path*',
        destination: 'http://localhost:8000/patients/:path*',
      },
      {
        source: '/orders',
        destination: 'http://localhost:8000/orders',
      },
      {
        source: '/conversations/:path*',
        destination: 'http://localhost:8000/conversations/:path*',
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/audio/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
