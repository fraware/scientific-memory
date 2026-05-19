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

const formalCheckView = z.object({
  obligation_id: z.string().min(1),
  predicate: z.string().min(1).nullish(),
  lean_theorem: z.string().min(1),
  status: z.string().nullish(),
  source_artifacts: z.array(z.string()).nullish(),
  checked_at: z.string().nullish(),
  lean_version: z.string().nullish(),
  result: z.string().nullish(),
  trust_boundary_invariant: z.string().nullish(),
  formal_scope: z.string().nullish(),
  expected: z.string().nullish(),
  actual: z.string().nullish(),
  responsible_component: z.string().nullish(),
  repair_hint: z.string().nullish(),
  pf_explain: z.string().nullish(),
});

const formalTrustKernel = z.object({
  title: z.string().min(1),
  what_was_checked: z.string().min(1),
  overall_status: z.string().min(1),
  formal_scope: z.string().min(1),
  formal_non_claims: z.array(z.string()).min(4),
  proof_obligations: z.array(formalCheckView).min(1),
  lean_check_results: z.array(formalCheckView).min(1),
  theorems_checked: z.array(z.string()).optional(),
  artifacts_used: z.array(z.string()).optional(),
  trust_boundary_invariants: z.array(z.string()).optional(),
  lean_version: z.string().optional(),
  checked_at: z.string().optional(),
  pf_explain: z.string().nullish(),
});

const REQUIRED_FORMAL_NON_CLAIM_SNIPPETS = [
  "does not prove the scientific claim is true",
  "does not prove the dataset is unbiased",
  "does not prove the model is valid",
  "proves only the declared PCS trust-envelope invariant",
];

function workflowRequiresFormalTrust(data) {
  return (
    data.workflow_id === "labtrust.qc_release_v0.1" ||
    data.workflow_id.startsWith("agent_tool_use") ||
    data.workflow_id.startsWith("scientific_computation")
  );
}

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
    dataset_receipt: namedArtifact.optional(),
    environment_receipt: namedArtifact.optional(),
    computation_run_receipt: namedArtifact.optional(),
    result_artifact: namedArtifact.optional(),
    computation_witness: namedArtifact.optional(),
    formal_trust_kernel: formalTrustKernel.optional(),
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
    const isComputation =
      data.domain === "scientific_computation" ||
      data.workflow_id.startsWith("scientific_computation");
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
    } else if (isComputation) {
      const required = [
        ["dataset_receipt", "DatasetReceipt.v0"],
        ["environment_receipt", "EnvironmentReceipt.v0"],
        ["computation_run_receipt", "ComputationRunReceipt.v0"],
        ["result_artifact", "ResultArtifact.v0"],
        ["computation_witness", "ComputationWitness.v0"],
      ];
      for (const [pathKey] of required) {
        if (!data[pathKey]) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `${pathKey} required for scientific_computation workflow`,
            path: [pathKey],
          });
        }
      }
      const runtime = data.runtime_artifact_types ?? [];
      for (const artifactType of [
        "DatasetReceipt.v0",
        "EnvironmentReceipt.v0",
        "ComputationRunReceipt.v0",
        "ResultArtifact.v0",
      ]) {
        if (!runtime.includes(artifactType)) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `runtime_artifact_types must include ${artifactType}`,
            path: ["runtime_artifact_types"],
          });
        }
      }
      const certs = data.certificate_artifact_types ?? [];
      if (!certs.includes("ComputationWitness.v0")) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "certificate_artifact_types must include ComputationWitness.v0",
          path: ["certificate_artifact_types"],
        });
      }
      const notice = data.limitation_notice ?? "";
      if (!notice.includes("computational provenance")) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "limitation_notice must include computation reproducibility disclaimer",
          path: ["limitation_notice"],
        });
      }
    } else if (!(data.handoff_manifests?.length ?? 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "handoff_manifests required for release workflows with producer handoffs",
        path: ["handoff_manifests"],
      });
    }

    if (workflowRequiresFormalTrust(data)) {
      if (!data.formal_trust_kernel) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "formal_trust_kernel required for formal-trust workflows",
          path: ["formal_trust_kernel"],
        });
        return;
      }
      const kernel = data.formal_trust_kernel;
      if (kernel.overall_status !== "ProofChecked") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "formal_trust_kernel.overall_status must be ProofChecked for passed releases",
          path: ["formal_trust_kernel", "overall_status"],
        });
      }
      for (const snippet of REQUIRED_FORMAL_NON_CLAIM_SNIPPETS) {
        const found = (kernel.formal_non_claims ?? []).some((line) => line.includes(snippet));
        if (!found) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `formal_non_claims must include: ${snippet}`,
            path: ["formal_trust_kernel", "formal_non_claims"],
          });
        }
      }
      const theoremCount = kernel.lean_check_results?.length ?? 0;
      if (theoremCount < 1) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "lean_check_results must list at least one theorem",
          path: ["formal_trust_kernel", "lean_check_results"],
        });
      }
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
