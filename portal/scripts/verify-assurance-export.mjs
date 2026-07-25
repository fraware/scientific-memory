#!/usr/bin/env node
/**
 * Verify portal/.generated/assurance-export.json shape (canonical manifests only).
 * Fail closed when the export is missing: portal pages must build from export data.
 */
import { readFileSync, existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const exportPath = path.join(root, ".generated", "assurance-export.json");

const EVIDENCE_CLASSES = new Set([
  "formally_checked",
  "certificate_checked",
  "runtime_observed",
  "empirically_measured",
  "human_reviewed",
  "unchecked_advisory",
]);

function fail(msg) {
  console.error(msg);
  process.exit(1);
}

if (!existsSync(exportPath)) {
  fail(
    "assurance-export.json missing; run: just export-assurance-portal-data (portal builds from export only)",
  );
}

const data = JSON.parse(readFileSync(exportPath, "utf8"));
if (data.schema_version !== "AssurancePortalExport.v1") {
  fail(`Unexpected schema_version: ${data.schema_version}`);
}
if (!Array.isArray(data.action_ids) || typeof data.actions !== "object") {
  fail("assurance-export must have action_ids[] and actions{}");
}
for (const id of data.action_ids) {
  const action = data.actions[id];
  if (!action) fail(`Missing action payload for ${id}`);
  if (!Array.isArray(action.nodes) || !Array.isArray(action.gaps)) {
    fail(`Action ${id} missing nodes/gaps arrays`);
  }
  if (!Array.isArray(action.chronology)) {
    fail(`Action ${id} missing chronology[]`);
  }
  for (const node of action.nodes) {
    if (node.privacy === "internal" && data.include_internal !== true) {
      if (node.summary && node.summary !== "[redacted]" && node.payload) {
        fail(
          `Public export must not expose internal payload for ${node.node_id}`,
        );
      }
    }
    for (const cls of node.evidence_classes || []) {
      if (!EVIDENCE_CLASSES.has(cls)) {
        fail(`Unknown evidence class ${cls} on ${node.node_id}`);
      }
    }
  }
}
console.log(`assurance-export ok (${data.action_ids.length} actions)`);
