import { promises as fs } from "fs";
import path from "path";

import type { PcsClaimReadModel, PcsPortalExport } from "./pcsTypes";

const ROOT = process.cwd();
const PCS_EXPORT = path.join(ROOT, ".generated", "pcs-export.json");
const CORPUS_PCS = path.join(ROOT, "..", "corpus", "pcs", "claims");

async function readPcsExport(): Promise<PcsPortalExport | null> {
  const raw = await fs.readFile(PCS_EXPORT, "utf8").catch(() => null);
  if (!raw) return null;
  return JSON.parse(raw) as PcsPortalExport;
}

async function readClaimFromCorpus(claimId: string): Promise<PcsClaimReadModel | null> {
  const p = path.join(CORPUS_PCS, claimId, "read_model.json");
  const raw = await fs.readFile(p, "utf8").catch(() => null);
  if (!raw) return null;
  return JSON.parse(raw) as PcsClaimReadModel;
}

export async function getAllPcsClaimIds(): Promise<string[]> {
  const exported = await readPcsExport();
  if (exported?.claim_ids?.length) {
    return exported.claim_ids;
  }
  const entries = await fs.readdir(CORPUS_PCS, { withFileTypes: true }).catch(() => []);
  return entries.filter((e) => e.isDirectory()).map((e) => e.name);
}

export async function getPcsClaimById(
  claimId: string,
): Promise<PcsClaimReadModel | null> {
  const exported = await readPcsExport();
  const fromExport = exported?.claims?.[claimId];
  if (fromExport) return fromExport;
  return readClaimFromCorpus(claimId);
}
