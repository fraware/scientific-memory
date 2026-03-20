interface CoveragePanelProps {
  claimCount: number;
  mappedCount: number;
  machineCheckedCount: number;
  kernelLinkedCount: number;
}

export function CoveragePanel({
  claimCount,
  mappedCount,
  machineCheckedCount,
  kernelLinkedCount,
}: CoveragePanelProps) {
  return (
    <div className="rounded border p-4">
      <h3 className="font-medium">Coverage</h3>
      <ul className="mt-2 text-sm">
        <li>Claims: {claimCount}</li>
        <li>Mapped: {mappedCount}</li>
        <li>Machine-checked: {machineCheckedCount}</li>
        <li>Kernel-linked: {kernelLinkedCount}</li>
      </ul>
    </div>
  );
}
