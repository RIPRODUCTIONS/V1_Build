import './globals.css';

import type { Metadata } from 'next';

import ErrorBoundary from '@/components/ErrorBoundary';

import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Builder Dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        {process.env.NEXT_PUBLIC_MOCK === 'true' && typeof window !== 'undefined' && <></>}
        <ErrorBoundary>
          <Providers>{children}</Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
