/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy uploads through Next so URLs like http://localhost:3002/uploads/... work.
    // In Docker, backend is reachable as http://backend:8000.
    return [
      {
        source: "/uploads/:path*",
        destination: "http://backend:8000/uploads/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
