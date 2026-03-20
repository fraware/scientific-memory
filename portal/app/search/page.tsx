import { Suspense } from "react";
import { SearchClient } from "@/components/SearchClient";

export const metadata = {
  title: "Search | Scientific Memory",
  description: "Search papers and claims in the corpus.",
};

export default function SearchPage() {
  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">Search</h1>
      <p className="mt-2 text-gray-600">
        Find papers and claims by title, id, year, or claim text.
      </p>
      <Suspense fallback={<p className="mt-4 text-gray-600">Loading…</p>}>
        <SearchClient />
      </Suspense>
    </main>
  );
}
