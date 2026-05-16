interface ReplayCommandProps {
  reproduceCommands: string[];
  verifyCommands: string[];
}

export function ReplayCommand({
  reproduceCommands,
  verifyCommands,
}: ReplayCommandProps) {
  return (
    <section data-testid="pcs-section-reproduce-verify">
      <h2 className="text-lg font-medium">Reproduce / Verify</h2>
      {reproduceCommands.length > 0 && (
        <div className="mt-3">
          <h3 className="text-sm font-medium text-gray-700">Reproduce</h3>
          <ul className="mt-2 space-y-2">
            {reproduceCommands.map((cmd) => (
              <li key={cmd}>
                <pre className="overflow-x-auto rounded border bg-gray-900 p-3 text-xs text-gray-100">
                  {cmd}
                </pre>
              </li>
            ))}
          </ul>
        </div>
      )}
      {verifyCommands.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700">Verify externally</h3>
          <ul className="mt-2 space-y-2">
            {verifyCommands.map((cmd) => (
              <li key={cmd}>
                <pre className="overflow-x-auto rounded border bg-gray-900 p-3 text-xs text-gray-100">
                  {cmd}
                </pre>
              </li>
            ))}
          </ul>
        </div>
      )}
      {reproduceCommands.length === 0 && verifyCommands.length === 0 && (
        <p className="mt-2 text-sm text-gray-600">No reproduce or verify commands recorded.</p>
      )}
    </section>
  );
}
