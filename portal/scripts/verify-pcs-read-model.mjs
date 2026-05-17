/**
 * Validate canonical PCS read model JSON (portal zod contract; no vitest required).
 * Run: node portal/scripts/verify-pcs-read-model.mjs [path]
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const defaultPath = path.resolve(
  __dirname,
  "../../tests/pcs/fixtures/canonical_pcs_read_model.json",
);
const modelPath = process.argv[2] ? path.resolve(process.argv[2]) : defaultPath;

const LIMITATION_NOTICE =
  "This artifact is a proof-carrying simulation result. It demonstrates " +
  "protocol-level and runtime-evidence verification inside LabTrust-Gym. It is " +
  "not a clinical validation, production medical certification, or guarantee " +
  "about a real hospital laboratory.";

const namedArtifact = z.object({
  signature_or_digest: z.string().min(1),
});

const readModelSchema = z.object({
  schema_version: z.string().min(1),
  claim_id: z.string().min(1),
  limitation_notice: z.literal(LIMITATION_NOTICE),
  limitations: z.array(z.string()).min(1),
  claim: namedArtifact,
  assumption_set: z.object({
    assumptions: z.array(z.object({ text: z.string().min(1) })).min(1),
  }),
  runtime_receipt: namedArtifact,
  trace_certificate: namedArtifact,
  verification_result: z.object({
    verification_id: z.string().optional(),
    verifier: z.string().optional(),
    checks: z.array(z.object({ outcome: z.string() })).min(1),
  }),
  artifact_hashes: z.array(z.object({ name: z.string(), digest: z.string() })).min(5),
  canonical_digests: z.object({
    claim_artifact: z.string().startsWith("sha256:"),
    runtime_receipt: z.string().startsWith("sha256:"),
    trace_certificate: z.string().startsWith("sha256:"),
    evidence_bundle: z.string().startsWith("sha256:"),
    signed_bundle: z.string().startsWith("sha256:"),
  }),
  source_repositories: z
    .array(
      z.object({
        source_repo: z.string().url(),
        source_commit: z.string().min(1),
      }),
    )
    .min(1),
  reproduce_commands: z.array(z.string()),
  verify_commands: z.array(z.string()),
});

const raw = JSON.parse(readFileSync(modelPath, "utf8"));
const parsed = readModelSchema.safeParse(raw);
if (!parsed.success) {
  console.error("PCS read model contract failed:", parsed.error.flatten());
  process.exit(1);
}
console.log(`OK: ${modelPath} (claim_id=${parsed.data.claim_id})`);
