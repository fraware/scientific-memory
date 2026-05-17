import { readFileSync } from "node:fs";
import path from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PcsClaimPage } from "@/components/pcs/PcsClaimPage";
import type { PcsClaimReadModel } from "@/lib/pcsTypes";

const readModelPath = path.resolve(
  __dirname,
  "../../tests/pcs/fixtures/canonical_pcs_read_model.json",
);
const model = JSON.parse(readFileSync(readModelPath, "utf-8")) as PcsClaimReadModel;

const LIMITATION_SNIPPET =
  "proof-carrying simulation result";

describe("PcsClaimPage", () => {
  it("renders all required PCS sections", () => {
    render(<PcsClaimPage model={model} />);

    expect(screen.getByTestId("pcs-claim-page")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-claim")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-assumptions")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-runtime-evidence")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-temporal-certificate")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-verification-result")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-artifact-hashes")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-source-repos")).toBeTruthy();
    expect(screen.getByTestId("pcs-section-reproduce-verify")).toBeTruthy();
    expect(screen.getByTestId("pcs-limitation-notice")).toBeTruthy();
  });

  it("displays verification result and artifact hashes", () => {
    render(<PcsClaimPage model={model} />);

    expect(screen.getByTestId("pcs-verification-status")).toBeTruthy();
    expect(screen.getByTestId("pcs-hash-table")).toBeTruthy();
    expect(screen.getAllByTestId("pcs-hash-digest").length).toBeGreaterThan(0);
  });

  it("displays the mandatory LabTrust limitation notice", () => {
    render(<PcsClaimPage model={model} />);
    const notice = screen.getByTestId("pcs-limitation-notice");
    expect(notice.textContent).toContain(LIMITATION_SNIPPET);
    expect(notice.textContent).toContain("not a clinical validation");
  });
});
