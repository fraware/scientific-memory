export interface PaperMetadata {
  id: string;
  title: string;
  authors: string[];
  year: number;
  domain: string;
  tags?: string[];
  artifact_status: string;
}

export interface Claim {
  id: string;
  paper_id: string;
  section: string;
  informal_text: string;
  claim_type: string;
  status: string;
  linked_formal_targets?: string[];
}

export interface CoverageMetrics {
  claim_count: number;
  mapped_claim_count: number;
  machine_checked_count: number;
  kernel_linked_count: number;
}
