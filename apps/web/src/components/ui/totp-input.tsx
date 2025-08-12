/**
 * TOTP Input Component - 6-digit OTP input with improved UX
 * Features: auto-focus, auto-submit, backspace handling, paste support
 */

'use client'

import * as React from 'react'
import { cn } from '@/utils/cn'

export interface TotpInputProps {
  value?: string
  onChange?: (value: string) => void
  onComplete?: (value: string) => void
  disabled?: boolean
  error?: boolean
  className?: string
  placeholder?: string
  autoFocus?: boolean
  'aria-label'?: string
}

const TotpInput = React.forwardRef<HTMLDivElement, TotpInputProps>(
  ({ 
    value = '', 
    onChange, 
    onComplete,
    disabled = false,
    error = false,
    className,
    placeholder = '000000',
    autoFocus = false,
    'aria-label': ariaLabel = 'Código de autenticação de 6 dígitos',
    ...props 
  }, ref) => {
    const [digits, setDigits] = React.useState<string[]>(Array(6).fill(''))
    const inputRefs = React.useRef<(HTMLInputElement | null)[]>([])

    // Initialize digit array from value prop
    React.useEffect(() => {
      const paddedValue = value.padEnd(6, '').slice(0, 6)
      const newDigits = paddedValue.split('')
      setDigits(newDigits)
    }, [value])

    // Auto-focus first input on mount
    React.useEffect(() => {
      if (autoFocus && inputRefs.current[0] && !disabled) {
        inputRefs.current[0].focus()
      }
    }, [autoFocus, disabled])

    const focusInput = (index: number) => {
      if (inputRefs.current[index] && !disabled) {
        inputRefs.current[index]?.focus()
      }
    }

    const handleChange = (index: number, newValue: string) => {
      // Only allow digits
      const cleanValue = newValue.replace(/\D/g, '')
      
      if (cleanValue.length > 1) {
        // Handle paste - distribute digits across inputs
        const pastedDigits = cleanValue.slice(0, 6).split('')
        const newDigits = [...digits]
        
        pastedDigits.forEach((digit, i) => {
          if (index + i < 6) {
            newDigits[index + i] = digit
          }
        })
        
        setDigits(newDigits)
        const newValue = newDigits.join('')
        onChange?.(newValue)
        
        // Focus on next empty input or last input
        const nextEmptyIndex = newDigits.findIndex(d => d === '')
        const targetIndex = nextEmptyIndex >= 0 ? nextEmptyIndex : Math.min(5, index + pastedDigits.length)
        focusInput(targetIndex)
        
        // Check if complete
        if (newDigits.every(d => d !== '')) {
          onComplete?.(newValue)
        }
      } else {
        // Single digit input
        const newDigits = [...digits]
        newDigits[index] = cleanValue
        setDigits(newDigits)
        
        const newValue = newDigits.join('')
        onChange?.(newValue)
        
        // Auto-advance to next input
        if (cleanValue && index < 5) {
          focusInput(index + 1)
        }
        
        // Check if complete
        if (newDigits.every(d => d !== '')) {
          onComplete?.(newValue)
        }
      }
    }

    const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Backspace') {
        e.preventDefault()
        const newDigits = [...digits]
        
        if (digits[index]) {
          // Clear current digit
          newDigits[index] = ''
        } else if (index > 0) {
          // Move to previous input and clear it
          newDigits[index - 1] = ''
          focusInput(index - 1)
        }
        
        setDigits(newDigits)
        onChange?.(newDigits.join(''))
      } else if (e.key === 'ArrowLeft' && index > 0) {
        e.preventDefault()
        focusInput(index - 1)
      } else if (e.key === 'ArrowRight' && index < 5) {
        e.preventDefault()
        focusInput(index + 1)
      } else if (e.key === 'Enter' && digits.every(d => d !== '')) {
        e.preventDefault()
        onComplete?.(digits.join(''))
      }
    }

    const handleFocus = (index: number) => {
      // Select all text when focused for easier replacement
      inputRefs.current[index]?.select()
    }

    return (
      <div 
        ref={ref} 
        className={cn('flex gap-2 justify-center', className)} 
        {...props}
      >
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(el) => (inputRefs.current[index] = el)}
            type="text"
            inputMode="numeric"
            pattern="[0-9]"
            maxLength={6} // Allow pasting up to 6 digits
            value={digit}
            placeholder={placeholder[index] || '0'}
            disabled={disabled}
            className={cn(
              'w-12 h-12 text-center text-lg font-mono border rounded-md bg-background',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              error && 'border-destructive focus:ring-destructive',
              !error && 'border-input',
              digit && 'font-semibold'
            )}
            aria-label={`${ariaLabel}, dígito ${index + 1}`}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onFocus={() => handleFocus(index)}
          />
        ))}
      </div>
    )
  }
)

TotpInput.displayName = 'TotpInput'

export { TotpInput }