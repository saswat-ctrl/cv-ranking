'use client';

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { Toaster } from "react-hot-toast";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { usePathname } from "next/navigation";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();

  // Pages that should NOT have sidebar/topbar
  // We treat dashboard, jobs, settings, profile as "public" here so they don't render the Next.js layout before redirecting
  const publicPages = ['/', '/login', '/signup', '/set-password', '/dashboard', '/jobs', '/settings', '/profile'];
  const isPublicPage = publicPages.includes(pathname);

  return (
    <html lang="en">
      <head>
        <title>HR CV Shortlisting</title>
        <meta name="description" content="AI-Powered CV Ranking for Recruiters" />
      </head>
      <body className={inter.className}>
        <ErrorBoundary>
          <Providers>
            {isPublicPage ? (
              // Public pages - no sidebar/topbar
              <>
                {children}
                <Toaster position="top-right" />
              </>
            ) : (
              // Authenticated pages - with sidebar/topbar
              <div className="flex h-screen overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto bg-background-light dark:bg-background-dark">
                  <Topbar />
                  {children}
                </main>
              </div>
            )}
            <Toaster position="top-right" />
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}

