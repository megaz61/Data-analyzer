// import type { NextConfig } from 'next';

// const nextConfig: NextConfig = {
//   experimental: {
//     appDir: true,
//   },
//   images: {
//     domains: [],
//   },
// };

// export default nextConfig;

// next.config.ts
import type { NextConfig } from 'next';

const nextConfig = {
  images: {
    domains: [],
  },
} satisfies NextConfig;

export default nextConfig;
