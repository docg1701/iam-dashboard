"use client"

import { useMemo } from "react"
import { Check, X } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PasswordStrengthResult } from "@/types/auth"

interface PasswordStrengthIndicatorProps {
  password: string
  className?: string
  showDetails?: boolean
}

// Password strength calculation function
function calculatePasswordStrength(password: string): PasswordStrengthResult {
  const feedback: string[] = []
  let score = 0

  // Check length
  if (password.length >= 8) {
    score += 1
  } else {
    feedback.push("Pelo menos 8 caracteres")
  }

  // Check for uppercase
  if (/[A-Z]/.test(password)) {
    score += 1
  } else {
    feedback.push("Pelo menos 1 letra maiúscula")
  }

  // Check for lowercase
  if (/[a-z]/.test(password)) {
    score += 1
  } else {
    feedback.push("Pelo menos 1 letra minúscula")
  }

  // Check for numbers
  if (/\d/.test(password)) {
    score += 1
  } else {
    feedback.push("Pelo menos 1 número")
  }

  // Check for special characters
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1
  } else {
    feedback.push("Pelo menos 1 caractere especial (!@#$%^&*)")
  }

  // Bonus points for longer passwords
  if (password.length >= 12) {
    score += 1
  }

  // Cap the score at 5
  score = Math.min(score, 5)

  const isValid = score >= 4 && password.length >= 8

  return {
    score,
    feedback,
    isValid,
  }
}

const strengthLabels = [
  { label: "Muito Fraca", color: "bg-red-500" },
  { label: "Fraca", color: "bg-orange-500" },
  { label: "Regular", color: "bg-yellow-500" },
  { label: "Boa", color: "bg-blue-500" },
  { label: "Forte", color: "bg-green-500" },
  { label: "Muito Forte", color: "bg-green-600" },
]

export function PasswordStrengthIndicator({ 
  password, 
  className,
  showDetails = true 
}: PasswordStrengthIndicatorProps) {
  const strength = useMemo(() => calculatePasswordStrength(password), [password])

  if (!password) {
    return null
  }

  const strengthInfo = strengthLabels[strength.score] || strengthLabels[0]

  return (
    <div className={cn("space-y-2", className)}>
      {/* Strength Bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Força da senha:</span>
          <span className={cn(
            "font-medium",
            strength.score >= 4 ? "text-green-600" : 
            strength.score >= 2 ? "text-yellow-600" : "text-red-600"
          )}>
            {strengthInfo.label}
          </span>
        </div>
        
        <div className="flex gap-1">
          {Array.from({ length: 5 }, (_, i) => (
            <div
              key={i}
              className={cn(
                "h-2 flex-1 rounded-sm transition-colors",
                i < strength.score
                  ? strengthInfo.color
                  : "bg-muted"
              )}
            />
          ))}
        </div>
      </div>

      {/* Requirements Details */}
      {showDetails && (
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">Requisitos:</div>
          <ul className="space-y-1">
            <li className={cn(
              "flex items-center gap-2 text-xs",
              password.length >= 8 ? "text-green-600" : "text-muted-foreground"
            )}>
              {password.length >= 8 ? (
                <Check className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Pelo menos 8 caracteres
            </li>
            
            <li className={cn(
              "flex items-center gap-2 text-xs",
              /[A-Z]/.test(password) ? "text-green-600" : "text-muted-foreground"
            )}>
              {/[A-Z]/.test(password) ? (
                <Check className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Pelo menos 1 letra maiúscula
            </li>
            
            <li className={cn(
              "flex items-center gap-2 text-xs",
              /[a-z]/.test(password) ? "text-green-600" : "text-muted-foreground"
            )}>
              {/[a-z]/.test(password) ? (
                <Check className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Pelo menos 1 letra minúscula
            </li>
            
            <li className={cn(
              "flex items-center gap-2 text-xs",
              /\d/.test(password) ? "text-green-600" : "text-muted-foreground"
            )}>
              {/\d/.test(password) ? (
                <Check className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Pelo menos 1 número
            </li>
            
            <li className={cn(
              "flex items-center gap-2 text-xs",
              /[!@#$%^&*(),.?":{}|<>]/.test(password) ? "text-green-600" : "text-muted-foreground"
            )}>
              {/[!@#$%^&*(),.?":{}|<>]/.test(password) ? (
                <Check className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Pelo menos 1 caractere especial
            </li>
          </ul>
        </div>
      )}
    </div>
  )
}

// Enhanced login form with password strength
export function LoginFormWithStrength() {
  // This would be integrated into the main LoginForm component
  // Left as a separate component for modularity
  return null
}