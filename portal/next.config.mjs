/** @type {import('next').NextConfig} */
const nextConfig = {};

// Static export for `pnpm build` / CI only. `next dev` must not use output: "export"
// or dynamic routes error despite generateStaticParams (Next.js 14 on Windows).
if (process.env.NODE_ENV === "production") {
  nextConfig.output = "export";
}

export default nextConfig;
