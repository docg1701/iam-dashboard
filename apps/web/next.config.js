/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features for Next.js 15
  experimental: {
    // Enable React Compiler (if available)
    reactCompiler: true,
  },

  // TypeScript configuration
  typescript: {
    // Type checking is done in CI/CD pipeline
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    // Linting is done in CI/CD pipeline
    ignoreDuringBuilds: false,
  },

  // Image optimization
  images: {
    domains: [],
    formats: ['image/webp', 'image/avif'],
  },

  // Environment variables that should be available on the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },

  // Webpack configuration
  webpack: (config, { isServer }) => {
    // Optimize bundle size
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    }

    return config
  },

  // Output configuration
  output: 'standalone',

  // Enable compression
  compress: true,

  // Power by header
  poweredByHeader: false,
}

module.exports = nextConfig