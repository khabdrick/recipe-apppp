import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Recipe Dashboard',
  description: 'A Next.js frontend for the Recipe API',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
