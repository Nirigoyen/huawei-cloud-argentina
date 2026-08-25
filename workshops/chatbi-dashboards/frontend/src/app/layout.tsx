import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChatBI Workshop",
  description: "Dashboard competition workshop",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body className="bg-slate-950 text-slate-200 antialiased">
        {children}
      </body>
    </html>
  );
}
