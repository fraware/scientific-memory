/**
 * Validate Phase 2 PCS read model (workflow-aware: LabTrust QC, tool-use safety, future profiles).
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
  admission_status: z.enum(["passed", "warning", "failed", "deferred", "not_applicable"]),
  registry_admission_result: z.string().min(1),
});

const handoffEntry = z.object({
  handoff_id: z.string().min(1),
  from_component: z.string().min(1),
  to_component: z.string().min(1),
});

const namedArtifact = z.object({
  id: z.string().min(1),
  artifact_type: z.string().nullish(),
  schema_version: z.string().nullish(),
  status: z.string().nullish(),
  signature_or_digest: z.string().nullish(),
});

const phase2Schema = z
  .object({
    claim_id: z.string().min(1),
    workflow_id: z.string().min(1),
    domain: z.string().min(1),
    runtime_artifact_types: z.array(z.string()).optional(),
    certificate_artifact_types: z.array(z.string()).optional(),
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
    handoff_manifests: z.array(handoffEntry).optional(),
    artifact_dependency_graph: z
      .array(z.object({ from: z.string(), to: z.string(), kind: z.string() }))
      .min(1),
    release_manifest_hash: z.string().startsWith("sha256:"),
    signed_bundle_hash: z.string().startsWith("sha256:"),
    artifact_registry_version: z.string().min(1),
    workflow_profile: z.object({
      workflow_id: z.string().min(1),
      domain: z.string().min(1),
    }),
    tool_use_trace: namedArtifact.optional(),
    tool_use_certificate: namedArtifact.optional(),
    trace_certificate: namedArtifact.optional(),
    lineage: z.object({
      claim_id: z.string().min(1),
      certificate_id: z.string().min(1),
      signed_bundle_hash: z.string().startsWith("sha256:"),
      claim_state: z.enum(["current", "stale", "superseded", "withdrawn", "revalidated"]),
      recommended_action: z.string().min(1),
    }),
    staleness: z.object({
      stale: z.boolean(),
      stale_reasons: z.array(z.string()),
      claim_state: z.enum(["current", "stale", "superseded", "withdrawn", "revalidated"]),
      repair_hint: z.string(),
      recommended_action: z.string().min(1),
    }),
    limitation_notice: z.string().min(1),
  })
  .superRefine((data, ctx) => {
    const isToolUse =
      data.domain === "agent_tool_use" ||
      data.workflow_id.startsWith("agent_tool_use");
    if (isToolUse) {
      if (!data.tool_use_trace) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "tool_use_trace required for agent_tool_use workflow",
          path: ["tool_use_trace"],
        });
      }
      if (!data.tool_use_certificate) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "tool_use_certificate required for agent_tool_use workflow",
          path: ["tool_use_certificate"],
        });
      }
      const runtime = data.runtime_artifact_types ?? [];
      if (!runtime.includes("ToolUseTrace.v0")) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "runtime_artifact_types must include ToolUseTrace.v0",
          path: ["runtime_artifact_types"],
        });
      }
    } else if (!(data.handoff_manifests?.length ?? 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "handoff_manifests required for release workflows with producer handoffs",
        path: ["handoff_manifests"],
      });
    }
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
console.log(
  `OK: Phase 2 read model ${modelPath} (claim_id=${parsed.data.claim_id}, workflow_id=${parsed.data.workflow_id})`,
);
