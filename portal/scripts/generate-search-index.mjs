/**
 * Build-time script: reads corpus and writes public/search-index.json
 * for client-side search. Run from portal dir: node scripts/generate-search-index.mjs
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORTAL_ROOT = path.resolve(__dirname, "..");
const CORPUS = path.join(PORTAL_ROOT, "..", "corpus");
const SNIPPET_LENGTH = 200;

function readJson(filePath, fallback = null) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    return JSON.parse(raw || "{}");
  } catch {
    return fallback;
  }
}

const indexPath = path.join(CORPUS, "index.json");
const index = readJson(indexPath, { papers: [] });
const papers = index.papers ?? [];

const claims = [];
for (const p of papers) {
  const claimsPath = path.join(CORPUS, "papers", p.id, "claims.json");
  const claimList = readJson(claimsPath, []);
  if (!Array.isArray(claimList)) continue;
  for (const c of claimList) {
    const id = c?.id != null ? String(c.id) : "";
    const text = (
      c?.informal_text != null ? String(c.informal_text) : ""
    ).slice(0, SNIPPET_LENGTH);
    if (id) claims.push({ id, paper_id: p.id, informal_text: text });
  }
}

const searchIndex = { papers, claims };
const outDir = path.join(PORTAL_ROOT, "public");
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(
  path.join(outDir, "search-index.json"),
  JSON.stringify(searchIndex),
  "utf8",
);
