/// <reference types="vitest/config" />
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// CLINIC_SRC_DIR lets scripts/verify_solutions.py point the tests at a temporary copy.
const clinicDir = process.env.CLINIC_SRC_DIR ?? path.resolve(__dirname, "src/clinic");
// Same idea for the AI-interview apps (frontend/src/<app>, API on its own port): PAYOUTS_SRC_DIR etc.
const interviewApps = [
  { name: "payouts", port: 8713 },
  { name: "remits", port: 8714 },
  { name: "earnings", port: 8715 },
  { name: "sandbox", port: 8716 },
  { name: "warmup", port: 8717 },
];
const appDir = (name: string) => process.env[`${name.toUpperCase()}_SRC_DIR`] ?? path.resolve(__dirname, `src/${name}`);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@clinic": clinicDir, ...Object.fromEntries(interviewApps.map((a) => [`@${a.name}`, appDir(a.name)])) },
  },
  build: {
    rollupOptions: {
      // Each AI-interview app (payouts.html, ...) is its own page, so a compile error in the code
      // you're editing can't take the trainer down with it.
      input: {
        main: path.resolve(__dirname, "index.html"),
        ...Object.fromEntries(interviewApps.map((a) => [a.name, path.resolve(__dirname, `${a.name}.html`)])),
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    open: process.env.TRAINER_OPEN_BROWSER === "1",
    proxy: {
      // Trainer API (exercise catalog, test runner, progress)
      "/api": "http://127.0.0.1:8710",
      // Clinic API (the buggy app you're debugging): /clinic-api/patients -> :8711/patients
      "/clinic-api": {
        target: "http://127.0.0.1:8711",
        rewrite: (p) => p.replace(/^\/clinic-api/, ""),
      },
      // AI-interview APIs: /payouts-api/providers -> :8713/providers, /remits-api -> :8714, ...
      ...Object.fromEntries(
        interviewApps.map((a) => [
          `/${a.name}-api`,
          { target: `http://127.0.0.1:${a.port}`, rewrite: (p: string) => p.replace(`/${a.name}-api`, "") },
        ]),
      ),
    },
  },
  test: {
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
});
