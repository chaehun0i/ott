import { gzipSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const manifest = JSON.parse(readFileSync("dist/.vite/manifest.json", "utf8"));
const entry = Object.values(manifest).find((item) => item.isEntry);
if (!entry) throw new Error("Vite manifest has no entry");
const files = [
  entry.file,
  ...(entry.imports ?? []).map((key) => manifest[key]?.file).filter(Boolean),
];
const bytes = files.reduce(
  (total, file) => total + gzipSync(readFileSync(join("dist", file))).byteLength,
  0,
);
if (bytes > 200 * 1024) throw new Error(`Initial route gzip budget exceeded: ${bytes} bytes`);
if (files.length > 6)
  throw new Error(`Initial request-count budget exceeded: ${files.length} assets`);
console.log(`Initial route gzip: ${bytes} bytes`);
console.log(`Initial route asset requests: ${files.length}`);
