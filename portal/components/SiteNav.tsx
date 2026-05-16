import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/search", label: "Search" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/diff", label: "Diff" },
  { href: "/pcs", label: "PCS claims" },
] as const;

export function SiteNav() {
  return (
    <nav className="border-b bg-gray-50 px-4 py-3">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 text-sm">
        <Link href="/" className="font-semibold text-gray-900 hover:text-gray-700">
          Scientific Memory
        </Link>
        {links.slice(1).map(({ href, label }) => (
          <Link key={href} href={href} className="text-blue-600 hover:underline">
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
