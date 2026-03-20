/** Portal data loaders: consume `portal/.generated/corpus-export.json` (see `sm_pipeline.publish.portal_read_model.build_portal_bundle`). */
import { promises as fs } from "fs";
import path from "path";

import {
  parseCorpusExportBundle,
  toPaperReadModel,
  type CorpusExportBundle,
  type PaperReadModel,
} from "./readModel";

const ROOT = process.cwd();
const CORPUS = path.join(ROOT, "..", "corpus");
const EXPORTED_BUNDLE = path.join(ROOT, ".generated", "corpus-export.json");

export async function getPapersList(): Promise<
  { id: string; title: string; year: number }[]
> {
  const exported = await readExportBundle();
  const exportedPapers = exported?.papers_index?.papers;
  if (Array.isArray(exportedPapers) && exportedPapers.length > 0) {
    return exportedPapers;
  }
  const indexPath = path.join(CORPUS, "index.json");
  const raw = await fs.readFile(indexPath, "utf8").catch(() => "{}");
  const index = JSON.parse(raw || "{}") as {
    papers?: { id: string; title: string; year: number }[];
  };
  return index.papers ?? [];
}

/** All claim IDs across papers (for static export). */
export async function getAllClaimIds(): Promise<string[]> {
  const papers = await getPapersList();
  const ids: string[] = [];
  for (const p of papers) {
    const bundle = await getPaperBundle(p.id);
    const claims = bundle.claims as Record<string, unknown>[];
    for (const c of claims) {
      if (c?.id != null) ids.push(String(c.id));
    }
  }
  return ids;
}

/** All theorem card IDs (from manifest generated_pages) and declaration names (for static export). */
export async function getAllTheoremCardIds(): Promise<string[]> {
  const papers = await getPapersList();
  const ids = new Set<string>();
  for (const p of papers) {
    const bundle = await getPaperBundle(p.id);
    const pages = (bundle.manifest.generated_pages as string[]) ?? [];
    for (const url of pages) {
      if (url.startsWith("/theorem-cards/")) {
        ids.add(decodeURIComponent(url.slice("/theorem-cards/".length)));
      }
    }
    const mappingPath = path.join(CORPUS, "papers", p.id, "mapping.json");
    const mappingRaw = await fs.readFile(mappingPath, "utf8").catch(() => "{}");
    const mapping = JSON.parse(mappingRaw || "{}") as Record<string, unknown>;
    const claimToDecl = (mapping.claim_to_decl as Record<string, string>) ?? {};
    const namespace = String(mapping.namespace ?? "");
    for (const decl of Object.values(claimToDecl)) {
      const full = namespace ? `${namespace}.${decl}` : decl;
      ids.add(full);
    }
  }
  return Array.from(ids);
}

/** All kernel IDs from corpus/kernels.json (for static export). */
export async function getAllKernelIds(): Promise<string[]> {
  const kernels = await getKernelsIndex();
  return kernels.map((k) => String(k.id)).filter(Boolean);
}

/** Search index: papers and claim summaries for client-side search (build-time or static JSON). */
export type SearchIndex = {
  papers: { id: string; title: string; year: number }[];
  claims: { id: string; paper_id: string; informal_text: string }[];
};

const SEARCH_SNIPPET_LENGTH = 200;

export async function getSearchIndex(): Promise<SearchIndex> {
  const papers = await getPapersList();
  const claims: SearchIndex["claims"] = [];
  for (const p of papers) {
    const bundle = await getPaperBundle(p.id);
    const claimList = bundle.claims as Record<string, unknown>[];
    for (const c of claimList) {
      const id = c?.id != null ? String(c.id) : "";
      const text = (
        c?.informal_text != null ? String(c.informal_text) : ""
      ).slice(0, SEARCH_SNIPPET_LENGTH);
      if (id) claims.push({ id, paper_id: p.id, informal_text: text });
    }
  }
  return { papers, claims };
}

export type PaperCoverage = {
  paperId: string;
  title: string;
  claimCount: number;
  mappedCount: number;
  machineCheckedCount: number;
  kernelLinkedCount: number;
  reviewerBlockedCount: number;
  reviewerUnreviewedCount: number;
  reviewerReviewedCount: number;
  reviewerAcceptedCount: number;
};

export type CoverageDashboard = {
  papers: PaperCoverage[];
  totalClaims: number;
  totalMapped: number;
  totalMachineChecked: number;
  totalKernelLinked: number;
  totalReviewerBlocked: number;
  totalReviewerUnreviewed: number;
  totalReviewerReviewed: number;
  totalReviewerAccepted: number;
};

/** Declaration snapshot for diff (proof status per Lean decl). */
export type DiffDeclaration = { lean_decl: string; proof_status: string };

/** FNV-1a-ish digest for assumption text (stable drift signal). */
export function digestAssumptionText(s: string): string {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}

/** Baseline snapshot shape for diff (e.g. corpus/snapshots/last-release.json). */
export type DiffBaseline = {
  baseline_id?: string;
  title?: string;
  narrative?: string;
  highlights?: string[];
  snapshot_at?: string;
  papers: {
    id: string;
    title?: string;
    year?: number;
    claim_count: number;
    assumption_ids?: string[];
    /** When present, compared to current to detect same-id assumption text changes. */
    assumption_text_digests?: Record<string, string>;
    claim_statuses?: { id: string; status: string }[];
    declarations?: DiffDeclaration[];
  }[];
};

/** Load baseline for diff if present (corpus/snapshots/last-release.json). */
export async function getDiffBaseline(
  baselineId = "last-release",
): Promise<DiffBaseline | null> {
  const filename = baselineId.endsWith(".json")
    ? baselineId
    : `${baselineId}.json`;
  const p = path.join(CORPUS, "snapshots", filename);
  try {
    const raw = await fs.readFile(p, "utf8");
    const data = JSON.parse(raw) as unknown;
    if (
      data &&
      typeof data === "object" &&
      Array.isArray((data as { papers?: unknown }).papers)
    ) {
      return data as DiffBaseline;
    }
  } catch {
    /* no baseline */
  }
  return null;
}

/** List available diff baseline ids in corpus/snapshots/*.json. */
export async function listDiffBaselines(): Promise<string[]> {
  const dir = path.join(CORPUS, "snapshots");
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    const ids = entries
      .filter((e) => e.isFile() && e.name.endsWith(".json"))
      .map((e) => e.name.replace(/\.json$/i, ""));
    return ids.sort((a, b) => {
      if (a === "last-release") return -1;
      if (b === "last-release") return 1;
      return a.localeCompare(b);
    });
  } catch {
    return [];
  }
}

/** Current corpus state in same shape as baseline for diff. */
export async function getDiffCurrent(): Promise<DiffBaseline> {
  const list = await getPapersList();
  const dashboard = await getCoverageDashboard();
  const byId = new Map(dashboard.papers.map((p) => [p.paperId, p]));
  const papers: DiffBaseline["papers"] = [];
  for (const p of list) {
    const cov = byId.get(p.id);
    const bundle = await getPaperBundle(p.id);
    const assumptions = bundle.assumptions as Record<string, unknown>[];
    const assumption_text_digests: Record<string, string> = {};
    for (const a of assumptions) {
      const id = a?.id != null ? String(a.id) : "";
      const text = a?.text != null ? String(a.text) : "";
      if (id) assumption_text_digests[id] = digestAssumptionText(text);
    }
    const claims = bundle.claims as Record<string, unknown>[];
    const claim_statuses = claims
      .filter((c) => c?.id != null)
      .map((c) => ({ id: String(c.id), status: String(c.status ?? "") }));
    let declarations: DiffDeclaration[] = [];
    const cardsPath = path.join(CORPUS, "papers", p.id, "theorem_cards.json");
    try {
      const cardsRaw = await fs.readFile(cardsPath, "utf8");
      const cards = JSON.parse(cardsRaw) as Record<string, unknown>[];
      if (Array.isArray(cards)) {
        declarations = cards
          .filter((c) => c && typeof c === "object" && c.lean_decl)
          .map((c) => ({
            lean_decl: String((c as { lean_decl: unknown }).lean_decl),
            proof_status: String(
              (c as { proof_status?: unknown }).proof_status ?? "",
            ),
          }));
      }
    } catch {
      /* no theorem_cards; try manifest declaration_index */
      const manifest = bundle.manifest as Record<string, unknown>;
      const declIndex = manifest.declaration_index as string[] | undefined;
      if (Array.isArray(declIndex)) {
        declarations = declIndex
          .filter((d) => d)
          .map((d) => ({ lean_decl: String(d), proof_status: "" }));
      }
    }
    papers.push({
      id: p.id,
      title: p.title,
      year: p.year,
      claim_count: cov?.claimCount ?? 0,
      assumption_ids: assumptions.map((a) => String(a.id)).filter(Boolean),
      assumption_text_digests,
      claim_statuses,
      declarations,
    });
  }
  return { papers };
}

/** Aggregate coverage metrics from all paper manifests (for dashboard). */
export async function getCoverageDashboard(): Promise<CoverageDashboard> {
  const papers = await getPapersList();
  const papersData: PaperCoverage[] = [];
  let totalClaims = 0;
  let totalMapped = 0;
  let totalMachineChecked = 0;
  let totalKernelLinked = 0;
  let totalReviewerBlocked = 0;
  let totalReviewerUnreviewed = 0;
  let totalReviewerReviewed = 0;
  let totalReviewerAccepted = 0;
  for (const p of papers) {
    const bundle = await getPaperBundle(p.id);
    const cov =
      (bundle.manifest.coverage_metrics as Record<string, number>) ?? {};
    const claimCount = Number(cov.claim_count) || 0;
    const mappedCount = Number(cov.mapped_claim_count) || 0;
    const machineCheckedCount = Number(cov.machine_checked_count) || 0;
    const kernelLinkedCount = Number(cov.kernel_linked_count) || 0;
    const cards = bundle.theorem_cards;
    let reviewerBlockedCount = 0;
    let reviewerUnreviewedCount = 0;
    let reviewerReviewedCount = 0;
    let reviewerAcceptedCount = 0;
    for (const card of cards) {
      const status = String(card.reviewer_status ?? "unreviewed");
      if (status === "blocked") reviewerBlockedCount += 1;
      else if (status === "reviewed") reviewerReviewedCount += 1;
      else if (status === "accepted") reviewerAcceptedCount += 1;
      else reviewerUnreviewedCount += 1;
    }
    papersData.push({
      paperId: p.id,
      title: p.title ?? p.id,
      claimCount,
      mappedCount,
      machineCheckedCount,
      kernelLinkedCount,
      reviewerBlockedCount,
      reviewerUnreviewedCount,
      reviewerReviewedCount,
      reviewerAcceptedCount,
    });
    totalClaims += claimCount;
    totalMapped += mappedCount;
    totalMachineChecked += machineCheckedCount;
    totalKernelLinked += kernelLinkedCount;
    totalReviewerBlocked += reviewerBlockedCount;
    totalReviewerUnreviewed += reviewerUnreviewedCount;
    totalReviewerReviewed += reviewerReviewedCount;
    totalReviewerAccepted += reviewerAcceptedCount;
  }
  return {
    papers: papersData,
    totalClaims,
    totalMapped,
    totalMachineChecked,
    totalKernelLinked,
    totalReviewerBlocked,
    totalReviewerUnreviewed,
    totalReviewerReviewed,
    totalReviewerAccepted,
  };
}

/** Paper JSON for one id, normalized through the read-model adapter (export or corpus). */
export async function getPaperBundle(paperId: string): Promise<PaperReadModel> {
  const exported = await readExportBundle();
  const exportedPaper = exported?.papers?.[paperId];
  if (exportedPaper) {
    return toPaperReadModel(exportedPaper);
  }
  const base = path.join(CORPUS, "papers", paperId);
  const [
    metadata,
    claims,
    assumptions,
    symbols,
    manifest,
    mappingRaw,
    cardsRaw,
  ] = await Promise.all([
    fs.readFile(path.join(base, "metadata.json"), "utf8"),
    fs.readFile(path.join(base, "claims.json"), "utf8"),
    fs.readFile(path.join(base, "assumptions.json"), "utf8").catch(() => "[]"),
    fs.readFile(path.join(base, "symbols.json"), "utf8").catch(() => "[]"),
    fs.readFile(path.join(base, "manifest.json"), "utf8").catch(() => "{}"),
    fs.readFile(path.join(base, "mapping.json"), "utf8").catch(() => "{}"),
    fs
      .readFile(path.join(base, "theorem_cards.json"), "utf8")
      .catch(() => "[]"),
  ]);

  return toPaperReadModel({
    metadata: JSON.parse(metadata) as Record<string, unknown>,
    claims: JSON.parse(claims) as unknown[],
    assumptions: JSON.parse(assumptions || "[]") as unknown[],
    symbols: JSON.parse(symbols || "[]") as unknown[],
    mapping: JSON.parse(mappingRaw || "{}") as Record<string, unknown>,
    manifest: JSON.parse(manifest || "{}") as Record<string, unknown>,
    theorem_cards: JSON.parse(cardsRaw || "[]") as unknown[],
  });
}

/** Resolve a claim by id by scanning corpus papers (canonical data only). */
export async function getClaimById(claimId: string): Promise<{
  claim: Record<string, unknown>;
  paperId: string;
  metadata: Record<string, unknown>;
  assumptions: Record<string, unknown>[];
  symbols: Record<string, unknown>[];
  mapping: Record<string, unknown>;
} | null> {
  const index = await getPapersList();
  for (const p of index) {
    const bundle = await getPaperBundle(p.id);
    const claims = bundle.claims as Record<string, unknown>[];
    const claim = claims.find((c) => String(c.id) === claimId);
    if (claim) {
      const mappingPath = path.join(CORPUS, "papers", p.id, "mapping.json");
      const mappingRaw = await fs
        .readFile(mappingPath, "utf8")
        .catch(() => "{}");
      const mapping = JSON.parse(mappingRaw || "{}") as Record<string, unknown>;
      return {
        claim,
        paperId: p.id,
        metadata: bundle.metadata,
        assumptions: bundle.assumptions,
        symbols: bundle.symbols,
        mapping,
      };
    }
  }
  return null;
}

/** Resolve a theorem card by id (declaration name or claim-based card id) from manifest + mapping + theorem_cards. */
export async function getTheoremCardById(cardId: string): Promise<{
  paperId: string;
  claimId: string;
  claim: Record<string, unknown>;
  declaration: string;
  namespace: string;
  metadata: Record<string, unknown>;
  manifest: Record<string, unknown>;
  verificationBoundary: string;
  executableLinks: string[];
  linkedKernelIds: string[];
  filePath: string;
  reviewerStatus: string;
  notes: string;
} | null> {
  const index = await getPapersList();
  for (const p of index) {
    const bundle = await getPaperBundle(p.id);
    const mappingPath = path.join(CORPUS, "papers", p.id, "mapping.json");
    const mappingRaw = await fs.readFile(mappingPath, "utf8").catch(() => "{}");
    const mapping = JSON.parse(mappingRaw || "{}") as Record<string, unknown>;
    const claimToDecl = (mapping.claim_to_decl as Record<string, string>) ?? {};
    const namespace = String(mapping.namespace ?? "");

    for (const [cid, decl] of Object.entries(claimToDecl)) {
      const fullDecl = namespace ? `${namespace}.${decl}` : decl;
      if (cid === cardId || decl === cardId || fullDecl === cardId) {
        const claims = bundle.claims as Record<string, unknown>[];
        const claim = claims.find((c) => String(c.id) === cid) ?? {};
        const cardsPath = path.join(
          CORPUS,
          "papers",
          p.id,
          "theorem_cards.json",
        );
        let verificationBoundary = "";
        let executableLinks: string[] = [];
        let cardIdFromCard = "";
        let filePath = "";
        let reviewerStatus = "";
        let notes = "";
        try {
          const cardsRaw = await fs.readFile(cardsPath, "utf8");
          const cards = JSON.parse(cardsRaw) as Record<string, unknown>[];
          if (Array.isArray(cards)) {
            const card = cards.find(
              (c) =>
                String(c?.id) === cardId ||
                (String(c?.claim_id) === cid &&
                  (String(c?.lean_decl) === fullDecl ||
                    (namespace && String(c?.lean_decl) === decl))),
            ) as Record<string, unknown> | undefined;
            if (card) {
              cardIdFromCard = String(card.id ?? "");
              verificationBoundary = String(card.verification_boundary ?? "");
              executableLinks = Array.isArray(card.executable_links)
                ? (card.executable_links as string[]).filter(Boolean)
                : [];
              filePath = String(card.file_path ?? "");
              reviewerStatus = String(card.reviewer_status ?? "");
              notes = String(card.notes ?? "");
            }
          }
        } catch {
          /* no theorem_cards.json */
        }
        const kernelIds = new Set<string>(executableLinks);
        const kernels = await getKernelsIndex();
        for (const k of kernels) {
          const linked = (k.linked_theorem_cards as string[]) ?? [];
          if (
            linked.includes(cardId) ||
            linked.includes(fullDecl) ||
            (cardIdFromCard && linked.includes(cardIdFromCard))
          )
            kernelIds.add(String(k.id));
        }
        return {
          paperId: p.id,
          claimId: cid,
          claim: claim as Record<string, unknown>,
          declaration: fullDecl,
          namespace,
          metadata: bundle.metadata,
          manifest: bundle.manifest,
          verificationBoundary,
          executableLinks,
          linkedKernelIds: Array.from(kernelIds),
          filePath,
          reviewerStatus,
          notes,
        };
      }
    }
  }
  return null;
}

/** Load kernels index (canonical corpus/kernels.json). */
async function getKernelsIndex(): Promise<Record<string, unknown>[]> {
  const exported = await readExportBundle();
  if (Array.isArray(exported?.kernels)) {
    return exported.kernels.filter(
      (k): k is Record<string, unknown> =>
        k !== null && typeof k === "object" && !Array.isArray(k),
    );
  }
  const p = path.join(CORPUS, "kernels.json");
  const raw = await fs.readFile(p, "utf8").catch(() => "[]");
  const arr = JSON.parse(raw || "[]") as unknown[];
  return Array.isArray(arr) ? (arr as Record<string, unknown>[]) : [];
}

async function readExportBundle(): Promise<CorpusExportBundle | null> {
  try {
    const raw = await fs.readFile(EXPORTED_BUNDLE, "utf8");
    return parseCorpusExportBundle(JSON.parse(raw));
  } catch {
    // Fallback to direct corpus reads.
  }
  return null;
}

/** Resolve a kernel by id from corpus/kernels.json; fallback: papers that reference it in manifest. */
export async function getKernelById(kernelId: string): Promise<{
  kernel: Record<string, unknown>;
  paperIds: string[];
} | null> {
  const kernels = await getKernelsIndex();
  const kernel = kernels.find((k) => String(k.id) === kernelId) ?? null;
  const paperIds: string[] = [];
  const index = await getPapersList();
  for (const p of index) {
    const bundle = await getPaperBundle(p.id);
    const ki = (bundle.manifest.kernel_index as string[]) ?? [];
    if (ki.includes(kernelId)) paperIds.push(p.id);
  }
  if (kernel) {
    return { kernel, paperIds };
  }
  if (paperIds.length > 0) {
    return {
      kernel: { id: kernelId, domain: "unknown", linked_theorem_cards: [] },
      paperIds,
    };
  }
  return null;
}
