import Link from "next/link";
import { getPapersList } from "@/lib/data";

export default async function HomePage() {
  const papers = await getPapersList();

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">Scientific Memory</h1>
      <p className="mt-2 text-gray-600">
        Buildable, machine-checkable scientific knowledge.
      </p>

      <nav className="mt-6 flex gap-4 text-sm">
        <Link href="/search" className="text-blue-600 hover:underline">
          Search
        </Link>
        <Link href="/dashboard" className="text-blue-600 hover:underline">
          Dashboard
        </Link>
        <Link href="/diff" className="text-blue-600 hover:underline">
          Diff
        </Link>
      </nav>

      <section className="mt-8">
        <h2 className="text-xl font-medium">Papers</h2>
        <ul className="mt-3 space-y-2">
          {papers.map((p) => (
            <li key={p.id}>
              <Link
                href={`/papers/${p.id}`}
                className="text-blue-600 hover:underline"
              >
                {p.title} ({p.year})
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
