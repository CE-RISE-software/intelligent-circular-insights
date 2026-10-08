import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.ICI_API_TARGET ?? "http://127.0.0.1:8000";

// The API is same-origin in production and proxied in development, so the client
// never needs a base URL and never has to think about CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": { target: apiTarget, changeOrigin: true } },
  },
  build: { outDir: "dist", sourcemap: true },
});
