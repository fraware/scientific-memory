interface LimitationNoticeProps {
  notice: string;
  additional?: string[];
}

export function LimitationNotice({ notice, additional }: LimitationNoticeProps) {
  const extras = (additional ?? []).filter((line) => line.trim() && line !== notice);
  return (
    <aside
      className="rounded border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950"
      role="note"
      data-testid="pcs-limitation-notice"
    >
      <h3 className="font-semibold">Limitations</h3>
      <p className="mt-2">{notice}</p>
      {extras.length > 0 && (
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {extras.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
    </aside>
  );
}
