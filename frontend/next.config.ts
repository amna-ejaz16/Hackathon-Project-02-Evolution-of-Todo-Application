import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Configure webpack to handle Node.js modules for Neon WebSocket driver
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Don't bundle these Node.js modules on the server
      // They're available at runtime in Node.js environment
      config.externals = config.externals || [];
      config.externals.push({
        bufferutil: "bufferutil",
        "utf-8-validate": "utf-8-validate",
      });
    }
    return config;
  },

  // Ensure server components can use Node.js APIs
  serverExternalPackages: ["ws", "@neondatabase/serverless"],
};

export default nextConfig;
