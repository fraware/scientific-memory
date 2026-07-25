import Link from "next/link";
import { getAllAssuranceActionIds } from "@/lib/assuranceData";

export default async function AssuranceIndexPage() {
  const ids = await getAllAssuranceActionIds();
  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">Assurance actions</h1>
      <p className="mt-2 text-sm text-gray-600">
        Action chains from the canonical assurance export. Not a live
        authorization system.
      </p>
      {ids.length ? (
        <ul className="mt-6 list-disc space-y-2 pl-5">
          {ids.map((id) => (
            <li key={id}>
              <Link
                className="text-blue-600 hover:underline"
                href={`/assurance/actions/${id}`}
              >
                {id}
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-6 text-gray-500">
          No actions in portal/.generated/assurance-export.json.
        </p>
      )}
    </main>
  );
}
