import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { cn } from '@/utils/cn'
import { Providers } from './providers'
import '@/styles/globals.css'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'Dashboard IAM - Gerenciamento de Permissões',
  description: 'Sistema revolucionário de gerenciamento de permissões com arquitetura multi-agente',
  keywords: ['IAM', 'dashboard', 'permissões', 'gerenciamento', 'multi-agente'],
  authors: [{ name: 'IAM Dashboard Team' }],
  creator: 'IAM Dashboard Team',
  publisher: 'IAM Dashboard Team',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'pt_BR',
    url: '/',
    siteName: 'Dashboard IAM',
    title: 'Dashboard IAM - Gerenciamento de Permissões',
    description: 'Sistema revolucionário de gerenciamento de permissões com arquitetura multi-agente',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Dashboard IAM',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Dashboard IAM - Gerenciamento de Permissões',
    description: 'Sistema revolucionário de gerenciamento de permissões com arquitetura multi-agente',
    images: ['/og-image.png'],
  },
  robots: {
    index: false, // Dashboard should not be indexed
    follow: false,
    googleBot: {
      index: false,
      follow: false,
    },
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className={cn(inter.variable)} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}