/**
 * Typed read-model boundary for portal data.
 *
 * Raw JSON from `corpus-export.json` / corpus files is narrowed here so UI code
 * depends on stable field names, not `Record<string, unknown>` everywhere.
 */

/** Matches `portal_read_model.PORTAL_BUNDLE_VERSION` in the pipeline. */
export const EXPECTED_PORTAL_BUNDLE_VERSION = "0.1";

export type PaperIndexEntry = {
  id: string;
  title: string;
  year: number;
};

export type PapersIndex = {
  papers?: PaperIndexEntry[];
};

/** One paper slice inside the exported bundle (authoritative shape from Python). */
export type ExportedPaperBundle = {
  metadata?: Record<string, unknown>;
  claims?: unknown[];
  assumptions?: unknown[];
  symbols?: unknown[];
  mapping?: Record<string, unknown>;
  manifest?: Record<string, unknown>;
  theorem_cards?: unknown[];
};

export type CorpusExportBundle = {
  version?: string;
  papers_index?: PapersIndex;
  papers?: Record<string, ExportedPaperBundle>;
  kernels?: unknown[];
};

export type ClaimRecord = Record<string, unknown>;
export type AssumptionRecord = Record<string, unknown>;
export type SymbolRecord = Record<string, unknown>;
export type TheoremCardRecord = Record<string, unknown>;

/** Normalized paper bundle consumed by portal pages (adapter output). */
export type PaperReadModel = {
  metadata: Record<string, unknown>;
  claims: ClaimRecord[];
  assumptions: AssumptionRecord[];
  symbols: SymbolRecord[];
  mapping: Record<string, unknown>;
  manifest: Record<string, unknown>;
  theorem_cards: TheoremCardRecord[];
};

function isRecord(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function asObjectRecords(v: unknown): Record<string, unknown>[] {
  if (!Array.isArray(v)) return [];
  return v.filter(isRecord);
}

/** Narrow unknown JSON into `PaperReadModel` (defensive for OSS / partial exports). */
export function toPaperReadModel(
  raw: ExportedPaperBundle | null | undefined,
): PaperReadModel {
  if (!raw || !isRecord(raw)) {
    return {
      metadata: {},
      claims: [],
      assumptions: [],
      symbols: [],
      mapping: {},
      manifest: {},
      theorem_cards: [],
    };
  }
  return {
    metadata: isRecord(raw.metadata) ? raw.metadata : {},
    claims: asObjectRecords(raw.claims) as ClaimRecord[],
    assumptions: asObjectRecords(raw.assumptions) as AssumptionRecord[],
    symbols: asObjectRecords(raw.symbols) as SymbolRecord[],
    mapping: isRecord(raw.mapping) ? raw.mapping : {},
    manifest: isRecord(raw.manifest) ? raw.manifest : {},
    theorem_cards: asObjectRecords(raw.theorem_cards) as TheoremCardRecord[],
  };
}

export function parseCorpusExportBundle(
  raw: unknown,
): CorpusExportBundle | null {
  if (!raw || !isRecord(raw)) return null;
  return raw as CorpusExportBundle;
}
