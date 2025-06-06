/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  swcMinify: true,
  
  experimental: {
    serverComponentsExternalPackages: [],
  },
  
  images: {
    domains: [
      'img.youtube.com',
      'i.ytimg.com',
      'yt3.ggpht.com',
      'localhost',
    ],
    
    formats: ['image/webp', 'image/avif'],
    
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
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
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  
  async redirects() {
    return [
    ];
  },
  
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
        },
      ];
    }
    return [];
  },
  

  
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });
    
    return config;
  },
  
  typescript: {
    ignoreBuildErrors: false,
  },
  
  eslint: {
    ignoreDuringBuilds: false,
    
    dirs: ['src', 'pages', 'components', 'lib', 'utils'],
  },
  
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  
  compress: true,
  
  poweredByHeader: false,
  
  trailingSlash: false,
  
  pageExtensions: ['ts', 'tsx', 'js', 'jsx'],
};

module.exports = nextConfig;
