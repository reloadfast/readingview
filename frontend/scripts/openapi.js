#!/usr/bin/env node
/**
 * Regenerate frontend types from the backend's OpenAPI schema.
 *
 * Usage:
 *   pnpm openapi                  # fetch from running backend (default)
 *   pnpm openapi --spec-path ./x  # use local OpenAPI spec file directly
 */

import { execSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "../public");
const specPath = join(outDir, "openapi.json");
const outFile = join(__dirname, "../src/lib/api.generated.ts");

const args = process.argv.slice(2);
const specFlagIndex = args.indexOf("--spec-path");

if (specFlagIndex !== -1 && specFlagIndex + 1 < args.length) {
  // Use local spec file directly
  const localSpec = args[specFlagIndex + 1];
  console.log(`Using local spec: ${localSpec}`);
  execSync(`npx openapi-typescript "${localSpec}" -o "${outFile}"`, { stdio: "inherit" });
  console.log("Done.");
} else {
  // Fetch from running backend
  console.log("Fetching OpenAPI schema from backend...");
  const res = await fetch("http://localhost:8000/api/openapi.json");
  if (!res.ok) {
    console.error(`Failed to fetch OpenAPI schema: ${res.status}`);
    console.error("Is the backend running? Or use --spec-path to provide a local file.");
    process.exit(1);
  }
  const spec = await res.json();

  mkdirSync(outDir, { recursive: true });
  writeFileSync(specPath, JSON.stringify(spec, null, 2), "utf-8");
  console.log(`Wrote spec → ${specPath}`);

  execSync(`npx openapi-typescript "${specPath}" -o "${outFile}"`, { stdio: "inherit" });
  console.log("Done.");
}
