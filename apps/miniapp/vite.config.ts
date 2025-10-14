import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    host: true,
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
