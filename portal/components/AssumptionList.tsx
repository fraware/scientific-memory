interface Assumption {
  id: string;
  text: string;
  kind?: string;
}

interface AssumptionListProps {
  assumptions: Assumption[];
}

export function AssumptionList({ assumptions }: AssumptionListProps) {
  return (
    <ul className="space-y-2">
      {assumptions.map((a) => (
        <li key={a.id} className="rounded border p-2 text-sm">
          <span className="font-medium">{a.id}</span>: {a.text}
          {a.kind != null && (
            <span className="ml-2 text-gray-500">({a.kind})</span>
          )}
        </li>
      ))}
    </ul>
  );
}
