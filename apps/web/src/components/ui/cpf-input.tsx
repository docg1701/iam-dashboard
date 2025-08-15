'use client'

import { validateCPF, formatCPF } from '@shared/utils'
import { forwardRef, useEffect, useState } from 'react'

import { Input } from '@/components/ui/input'

interface CPFInputProps
  extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    'onChange' | 'value'
  > {
  value?: string
  onChange?: (value: string) => void
  onValidationChange?: (isValid: boolean) => void
  showValidationIcon?: boolean
  className?: string
}

/**
 * Reusable CPF Input component with built-in validation and formatting
 *
 * Features:
 * - Real-time CPF formatting (000.000.000-00)
 * - Brazilian CPF validation using @shared/utils
 * - Visual validation indicators
 * - Controlled component pattern
 * - Clean API value output (digits only)
 */
export const CPFInput = forwardRef<HTMLInputElement, CPFInputProps>(
  (
    {
      value = '',
      onChange,
      onValidationChange,
      showValidationIcon = true,
      className = '',
      ...props
    },
    ref
  ) => {
    const [displayValue, setDisplayValue] = useState('')
    const [isValid, setIsValid] = useState(false)

    // Update display value when external value changes
    useEffect(() => {
      if (value !== undefined) {
        const cleanValue = value.replace(/\D/g, '')
        const formattedValue = formatCPF(cleanValue)
        setDisplayValue(formattedValue)

        const valid = cleanValue.length === 11 && validateCPF(cleanValue)
        setIsValid(valid)
        onValidationChange?.(valid)
      }
    }, [value, onValidationChange])

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = event.target.value
      const cleanValue = inputValue.replace(/\D/g, '')

      // Limit to 11 digits (CPF length)
      if (cleanValue.length <= 11) {
        const formattedValue = formatCPF(cleanValue)
        setDisplayValue(formattedValue)

        // Validate CPF
        const valid = cleanValue.length === 11 && validateCPF(cleanValue)
        setIsValid(valid)
        onValidationChange?.(valid)

        // Return clean value to parent
        onChange?.(cleanValue)
      }
    }

    const getInputClassName = () => {
      let classes = className

      if (displayValue) {
        if (isValid) {
          classes += ' border-green-500'
        } else {
          classes += ' border-red-500'
        }
      }

      return classes
    }

    return (
      <div className="relative">
        <Input
          {...props}
          ref={ref}
          type="text"
          value={displayValue}
          onChange={handleChange}
          placeholder="000.000.000-00"
          maxLength={14} // Formatted length
          className={getInputClassName()}
        />

        {/* Validation Icon */}
        {showValidationIcon && displayValue && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {isValid ? (
              <span className="text-lg text-green-600">✓</span>
            ) : (
              <span className="text-lg text-red-600">✗</span>
            )}
          </div>
        )}
      </div>
    )
  }
)

CPFInput.displayName = 'CPFInput'

export default CPFInput
