import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    // Allows production builds to successfully complete even with lint warnings
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allows production builds to successfully complete
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
