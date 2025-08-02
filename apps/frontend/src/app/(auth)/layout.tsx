import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Autenticação | IAM Dashboard",
  description: "Sistema de Gestão de Identidade e Acesso - Autenticação",
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="auth-layout">
      {children}
    </div>
  )
}