import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Exclude test files from production builds
    if (!dev) {
      config.module.rules.push({
        test: /\.(test|spec)\.(js|jsx|ts|tsx)$/,
        loader: "ignore-loader",
      });

      config.module.rules.push({
        test: /src\/__tests__\//,
        loader: "ignore-loader",
      });
    }

    return config;
  },
};

export default nextConfig;
