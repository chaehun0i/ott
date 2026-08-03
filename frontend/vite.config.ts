import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: {
    manifest: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes("react-router") ||
            id.includes("react-dom") ||
            /node_modules[/\\]react[/\\]/.test(id)
          )
            return "react";
          if (id.includes("@tanstack/react-query")) return "query";
          if (id.includes("i18next")) return "i18n";
          return undefined;
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
      exclude: ["src/main.tsx", "src/shared/api/generated/**"],
    },
  },
});
