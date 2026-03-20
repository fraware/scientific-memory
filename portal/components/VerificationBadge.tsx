interface VerificationBadgeProps {
  boundary: string;
}

export function VerificationBadge({ boundary }: VerificationBadgeProps) {
  return (
    <span className="inline-flex rounded bg-gray-200 px-2 py-0.5 text-xs font-medium">
      {boundary.replace(/_/g, " ")}
    </span>
  );
}
