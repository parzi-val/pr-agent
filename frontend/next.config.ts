import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Explicitly setting the root for Turbopack to stop it from 
     looking in the parent directories for node_modules */
  experimental: {
    // @ts-expect-error - turbo is a valid field in some Next versions but missing in types sometimes
    turbo: {
      root: '.',
    },
  } as any,
};

export default nextConfig;
