"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

type SearchIndex = {
  papers: { id: string; title: string; year: number }[];
  claims: { id: string; paper_id: string; informal_text: string }[];
};

function normalize(s: string): string {
  return s.toLowerCase().trim();
}

function matchesPaper(
  p: { id: string; title: string; year: number },
  q: string,
): boolean {
  const nq = normalize(q);
  if (!nq) return false;
  return (
    normalize(p.id).includes(nq) ||
    normalize(p.title).includes(nq) ||
    String(p.year).includes(nq)
  );
}

function matchesClaim(
  c: { id: string; paper_id: string; informal_text: string },
  q: string,
): boolean {
  const nq = normalize(q);
  if (!nq) return false;
  return (
    normalize(c.id).includes(nq) ||
    normalize(c.paper_id).includes(nq) ||
    normalize(c.informal_text).includes(nq)
  );
}

export function SearchClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(initialQ);
  const [index, setIndex] = useState<SearchIndex | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetched = useRef(false);
  const urlSyncRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (fetched.current) return;
    fetched.current = true;
    fetch("/search-index.json")
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load search index: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (data && Array.isArray(data.papers) && Array.isArray(data.claims)) {
          setIndex(data as SearchIndex);
        } else {
          setError("Invalid search index format");
        }
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load index"),
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setQuery(initialQ);
  }, [initialQ]);

  // Keep URL in sync with query (debounced) so search is shareable/bookmarkable
  useEffect(() => {
    if (urlSyncRef.current) clearTimeout(urlSyncRef.current);
    urlSyncRef.current = setTimeout(() => {
      const current = searchParams.get("q") ?? "";
      if (query === current) return;
      const params = new URLSearchParams(searchParams.toString());
      if (query.trim()) params.set("q", query.trim());
      else params.delete("q");
      const next = params.toString();
      const path = next ? `/search?${next}` : "/search";
      router.replace(path, { scroll: false });
    }, 300);
    return () => {
      if (urlSyncRef.current) clearTimeout(urlSyncRef.current);
    };
  }, [query, router, searchParams]);

  const papers = useMemo(() => {
    if (!index || !query.trim()) return [];
    return index.papers.filter((p) => matchesPaper(p, query));
  }, [index, query]);

  const claims = useMemo(() => {
    if (!index || !query.trim()) return [];
    return index.claims.filter((c) => matchesClaim(c, query));
  }, [index, query]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  }, []);

  if (loading) {
    return <p className="mt-4 text-gray-600">Loading search index…</p>;
  }

  if (error) {
    return (
      <p className="mt-4 text-red-600" role="alert">
        {error}
      </p>
    );
  }

  if (!index) {
    return <p className="mt-4 text-gray-600">No search index available.</p>;
  }

  return (
    <div className="mt-6">
      <label htmlFor="search-input" className="sr-only">
        Search papers and claims
      </label>
      <input
        id="search-input"
        type="search"
        value={query}
        onChange={handleChange}
        placeholder="Search by paper title, id, year, or claim id/text…"
        className="w-full rounded border border-gray-300 px-3 py-2 text-base focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        aria-describedby="search-results-summary"
      />
      <div id="search-results-summary" className="sr-only" aria-live="polite">
        {query.trim()
          ? `${papers.length} paper(s), ${claims.length} claim(s)`
          : "Enter a query to search papers and claims."}
      </div>

      {!query.trim() && (
        <p className="mt-4 text-gray-500">
          Enter a query to find papers and claims.
        </p>
      )}

      {query.trim() && (
        <div className="mt-6 space-y-8">
          <section>
            <h2 className="text-lg font-medium">Papers ({papers.length})</h2>
            {papers.length === 0 ? (
              <p className="mt-2 text-gray-500">No papers match.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {papers.map((p) => (
                  <li key={p.id}>
                    <Link
                      href={`/papers/${encodeURIComponent(p.id)}`}
                      className="text-blue-600 hover:underline"
                    >
                      {p.title}
                    </Link>
                    <span className="ml-2 text-sm text-gray-500">
                      {p.id} ({p.year})
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section>
            <h2 className="text-lg font-medium">Claims ({claims.length})</h2>
            {claims.length === 0 ? (
              <p className="mt-2 text-gray-500">No claims match.</p>
            ) : (
              <ul className="mt-2 space-y-3">
                {claims.map((c) => (
                  <li key={c.id} className="rounded border border-gray-200 p-3">
                    <Link
                      href={`/claims/${encodeURIComponent(c.id)}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {c.id}
                    </Link>
                    <span className="ml-2 text-sm text-gray-500">
                      in {c.paper_id}
                    </span>
                    <p className="mt-1 text-sm text-gray-700 line-clamp-2">
                      {c.informal_text}
                      {c.informal_text.length >= 200 ? "…" : ""}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
