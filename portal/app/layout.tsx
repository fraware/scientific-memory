import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Scientific Memory",
  description: "Buildable, machine-checkable scientific knowledge.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white font-sans text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
