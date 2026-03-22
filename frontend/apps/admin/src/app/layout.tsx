import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CMDB Admin",
  description: "CMDB Administration Panel",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
