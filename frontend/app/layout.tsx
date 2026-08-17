import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "MAiX-YT Studio — AI YouTube Video Automation",
  description:
    "AI-powered YouTube video automation platform. Generate scripts, voiceovers, visuals, and fully assembled videos with a single click.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      appearance={{
        variables: {
          colorPrimary: "#8b5cf6",
          colorBackground: "#0a0a2e",
          borderRadius: "12px",
        },
      }}
    >
      <html lang="en" className="dark">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
