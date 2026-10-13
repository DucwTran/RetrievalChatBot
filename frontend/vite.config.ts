import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const API_TARGET = "http://localhost:8000";

// In dev the browser talks to Vite, which forwards API calls to the backend (no CORS needed).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/chat": API_TARGET,
      "/sessions": API_TARGET,
      "/health": API_TARGET,
    },
  },
});
