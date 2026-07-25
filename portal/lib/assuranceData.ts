import { promises as fs } from "fs";
import path from "path";

import type {
  AssuranceActionModel,
  AssurancePortalExport,
} from "./assuranceTypes";

const ROOT = process.cwd();
const ASSURANCE_EXPORT = path.join(ROOT, ".generated", "assurance-export.json");

async function readAssuranceExport(): Promise<AssurancePortalExport | null> {
  const raw = await fs.readFile(ASSURANCE_EXPORT, "utf8").catch(() => null);
  if (!raw) return null;
  return JSON.parse(raw) as AssurancePortalExport;
}

export async function getAllAssuranceActionIds(): Promise<string[]> {
  const exported = await readAssuranceExport();
  return exported?.action_ids ?? [];
}

export async function getAssuranceActionById(
  actionId: string,
): Promise<AssuranceActionModel | null> {
  const exported = await readAssuranceExport();
  const actions = exported?.["actions"];
  return actions?.[actionId] ?? null;
}
