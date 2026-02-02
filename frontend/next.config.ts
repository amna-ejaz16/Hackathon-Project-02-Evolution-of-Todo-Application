import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Configure webpack to handle Node.js modules and path aliases
  webpack: (config, { isServer }) => {
    // Ensure @ alias resolves to src directory for production builds
    // Use process.cwd() which is reliable in both local and Vercel environments
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.resolve(process.cwd(), "src"),
    };

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
