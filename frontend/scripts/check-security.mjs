import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const files = readdirSync("dist/assets");
if (files.some((name) => name.endsWith(".map"))) throw new Error("Public source map detected");
const source = files
  .filter((name) => name.endsWith(".js"))
  .map((name) => readFileSync(join("dist/assets", name), "utf8"))
  .join("\n");
for (const pattern of [/BEGIN (?:RSA |EC )?PRIVATE KEY/, /authorization:\s*bearer/i, /eval\s*\(/]) {
  if (pattern.test(source)) throw new Error(`Forbidden production pattern: ${String(pattern)}`);
}
console.log("Production asset security scan passed");
