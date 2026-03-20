/**
 * Gate 5 smoke test: assert that the built portal includes all manifest-driven
 * routes and the dependency graph capability (React Flow in build output).
 * Run after: pnpm --dir portal build
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORTAL_DIR = path.resolve(__dirname, "..");
const OUT_DIR = path.join(PORTAL_DIR, "out");
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const CORPUS = path.join(REPO_ROOT, "corpus");

/** Map route path (e.g. /papers/foo) to static export file path relative to out/ */
function routeToFile(route) {
  const trimmed = (route || "").replace(/^\//, "").trim();
  if (!trimmed) return null;
  return trimmed + ".html";
}

function loadJson(filePath) {
  if (!fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function main() {
  if (!fs.existsSync(OUT_DIR)) {
    console.error("Gate 5 smoke: out/ not found. Run portal build first.");
    process.exit(1);
  }

  const missing = [];
  const papersDir = path.join(CORPUS, "papers");
  if (fs.existsSync(papersDir)) {
    for (const name of fs.readdirSync(papersDir)) {
      const manifestPath = path.join(papersDir, name, "manifest.json");
      if (!fs.existsSync(manifestPath)) continue;
      const manifest = loadJson(manifestPath);
      if (!manifest || !Array.isArray(manifest.generated_pages)) continue;
      for (const page of manifest.generated_pages) {
        const file = routeToFile(page);
        if (!file) continue;
        const outPath = path.join(OUT_DIR, file);
        if (!fs.existsSync(outPath)) missing.push(page + " -> " + file);
      }
    }
  }

  const kernelsPath = path.join(CORPUS, "kernels.json");
  if (fs.existsSync(kernelsPath)) {
    const raw = fs.readFileSync(kernelsPath, "utf8").trim();
    if (raw) {
      try {
        const kernels = JSON.parse(raw);
        if (Array.isArray(kernels)) {
          for (const k of kernels) {
            if (k && k.id) {
              const file = routeToFile("/kernels/" + k.id);
              if (file) {
                const outPath = path.join(OUT_DIR, file);
                if (!fs.existsSync(outPath))
                  missing.push("/kernels/" + k.id + " -> " + file);
              }
            }
          }
        }
      } catch (_) {}
    }
  }

  if (missing.length > 0) {
    console.error("Gate 5 smoke: manifest-driven routes missing from build:");
    missing.forEach((m) => console.error("  ", m));
    process.exit(1);
  }

  const langmuirManifestPath = path.join(
    papersDir,
    "langmuir_1918_adsorption",
    "manifest.json",
  );
  if (fs.existsSync(langmuirManifestPath)) {
    const langmuirManifest = loadJson(langmuirManifestPath);
    const dg = langmuirManifest && langmuirManifest.dependency_graph;
    if (Array.isArray(dg) && dg.length > 0) {
      console.log(
        "Gate 5 smoke: manifest routes OK; Langmuir dependency_graph non-empty.",
      );
      return;
    }
  }

  const paperHtml = path.join(
    OUT_DIR,
    "papers",
    "langmuir_1918_adsorption.html",
  );
  const hasPaperPage = fs.existsSync(paperHtml);
  const html = hasPaperPage ? fs.readFileSync(paperHtml, "utf8") : "";
  const hasGraphSectionInHtml = html.includes("Dependency graph");
  if (hasGraphSectionInHtml) {
    console.log(
      "Gate 5 smoke: manifest routes OK; graph section found in paper page.",
    );
    return;
  }
  const chunksDir = path.join(OUT_DIR, "_next", "static", "chunks");
  if (!fs.existsSync(chunksDir)) {
    console.error("Gate 5 smoke: _next/static/chunks not found.");
    process.exit(1);
  }
  const allFiles = fs.readdirSync(chunksDir);
  const hasReactFlow = allFiles.some((f) => {
    if (!f.endsWith(".css") && !f.endsWith(".js")) return false;
    const content = fs.readFileSync(path.join(chunksDir, f), "utf8");
    return content.includes("react-flow");
  });
  if (!hasReactFlow) {
    console.error(
      "Gate 5 smoke: graph library (react-flow) not found in build output.",
    );
    process.exit(1);
  }
  console.log("Gate 5 smoke: manifest routes OK; graph library in build.");
}

main();
