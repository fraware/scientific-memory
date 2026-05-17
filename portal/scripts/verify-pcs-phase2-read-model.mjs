/**
 * Validate Phase 2 PCS read model sections (release manifest, chain validation, registry).
 * Run: node portal/scripts/verify-pcs-phase2-read-model.mjs [path]
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const registryEntry = z.object({
  name: z.string().min(1),
  artifact_type: z.string().min(1),
  producer: z.string().min(1),
  schema: z.string().min(1),
  status: z.string().min(1),
  source_repo: z.string().url(),
  source_commit: z.string().min(40),
  hash: z.string().startsWith("sha256:"),
  semantic_checks_performed: z.array(z.string()),
});

const phase2Schema = z.object({
  claim_id: z.string().min(1),
  release_manifest: z.object({
    release_id: z.string().min(1),
    release_status: z.string().min(1),
    manifest_hash: z.string().startsWith("sha256:"),
  }),
  release_chain_validation: z.object({
    validation_id: z.string().min(1),
    status: z.literal("ProofChecked"),
    checks: z.array(z.object({ check_id: z.string(), status: z.string() })).min(1),
  }),
  artifact_registry: z.array(registryEntry).min(1),
  artifact_dependency_graph: z
    .array(z.object({ from: z.string(), to: z.string(), kind: z.string() }))
    .min(1),
  release_manifest_hash: z.string().startsWith("sha256:"),
  signed_bundle_hash: z.string().startsWith("sha256:"),
});

const modelPath = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.resolve(__dirname, "../../tests/pcs/fixtures/labtrust-release/.phase2-read-model.json");

const raw = JSON.parse(readFileSync(modelPath, "utf8"));
const parsed = phase2Schema.safeParse(raw);
if (!parsed.success) {
  console.error("PCS Phase 2 read model contract failed:", parsed.error.flatten());
  process.exit(1);
}
console.log(`OK: Phase 2 read model ${modelPath} (claim_id=${parsed.data.claim_id})`);
