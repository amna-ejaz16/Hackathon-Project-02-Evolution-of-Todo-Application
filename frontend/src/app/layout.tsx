/**
 * Root layout for the application.
 * Defines the global HTML structure, font, and metadata.
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Configure Inter font with Latin subset
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "Todo Application",
    template: "%s | Todo App",
  },
  description: "Multi-user Todo application with secure authentication",
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="min-h-screen bg-dark-950 antialiased font-sans text-gray-100">
        {children}
      </body>
    </html>
  );
}
