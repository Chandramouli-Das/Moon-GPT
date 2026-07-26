import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MoonGPT · Chandramouli Das",
  description: "An intelligent portfolio assistant for Chandramouli Das.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
