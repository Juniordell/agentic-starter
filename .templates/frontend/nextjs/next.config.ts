import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    // Proxy /api/* to FastAPI. Set FASTAPI_URL in .env.local to override.
    const fastapiUrl = process.env.FASTAPI_URL ?? 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${fastapiUrl}/:path*`,
      },
    ]
  },
}

export default nextConfig
