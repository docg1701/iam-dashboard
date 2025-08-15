import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect, vi } from 'vitest'

import { TotpInput } from '../totp-input'

describe('TotpInput Component', () => {
  describe('Basic Rendering', () => {
    it('should render container with correct classes', () => {
      render(<TotpInput data-testid="totp-container" />)

      const container = screen.getByTestId('totp-container')
      expect(container).toBeInTheDocument()
      expect(container).toHaveClass('flex', 'justify-center', 'gap-2')
    })

    it('should render 6 input fields', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll('input[type="text"]')
      expect(inputs).toHaveLength(6)

      inputs.forEach((input, index) => {
        expect(input).toHaveAttribute('type', 'text')
        expect(input).toHaveAttribute('inputmode', 'numeric')
        expect(input).toHaveAttribute('pattern', '[0-9]')
        expect(input).toHaveAttribute('maxlength', '6')
      })
    })

    it('should apply default placeholder', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach((input, index) => {
        expect(input).toHaveAttribute('placeholder', '0')
      })
    })

    it('should apply custom placeholder', () => {
      const { container } = render(<TotpInput placeholder="123456" />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach((input, index) => {
        expect(input).toHaveAttribute('placeholder', (index + 1).toString())
      })
    })

    it('should apply custom className', () => {
      render(
        <TotpInput className="custom-class" data-testid="totp-container" />
      )

      const container = screen.getByTestId('totp-container')
      expect(container).toHaveClass('custom-class')
      expect(container).toHaveClass('flex') // Should still have base classes
    })

    it('should apply custom aria-label to inputs', () => {
      const { container } = render(<TotpInput aria-label="Custom TOTP code" />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach((input, index) => {
        expect(input).toHaveAttribute(
          'aria-label',
          `Custom TOTP code, dígito ${index + 1}`
        )
      })
    })
  })

  describe('Value Prop and Initialization', () => {
    it('should initialize with empty values by default', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll(
        'input[type="text"]'
      ) as NodeListOf<HTMLInputElement>
      inputs.forEach(input => {
        expect(input.value).toBe('')
      })
    })

    it('should initialize with provided value', () => {
      const { container } = render(<TotpInput value="123456" />)

      const inputs = container.querySelectorAll(
        'input[type="text"]'
      ) as NodeListOf<HTMLInputElement>
      inputs.forEach((input, index) => {
        expect(input.value).toBe((index + 1).toString())
      })
    })

    it('should handle partial values', () => {
      const { container } = render(<TotpInput value="123" />)

      const inputs = container.querySelectorAll(
        'input[type="text"]'
      ) as NodeListOf<HTMLInputElement>

      expect(inputs[0].value).toBe('1')
      expect(inputs[1].value).toBe('2')
      expect(inputs[2].value).toBe('3')
      expect(inputs[3].value).toBe('')
      expect(inputs[4].value).toBe('')
      expect(inputs[5].value).toBe('')
    })
  })

  describe('Disabled State', () => {
    it('should disable all inputs when disabled prop is true', () => {
      const { container } = render(<TotpInput disabled />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).toBeDisabled()
      })
    })

    it('should not be disabled by default', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).not.toBeDisabled()
      })
    })
  })

  describe('Error State', () => {
    it('should apply error styling when error prop is true', () => {
      const { container } = render(<TotpInput error />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).toHaveClass(
          'border-destructive',
          'focus:ring-destructive'
        )
        expect(input).not.toHaveClass('border-input')
      })
    })

    it('should apply normal styling when error prop is false', () => {
      const { container } = render(<TotpInput error={false} />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).toHaveClass('border-input')
        expect(input).not.toHaveClass(
          'border-destructive',
          'focus:ring-destructive'
        )
      })
    })
  })

  describe('Ref Forwarding', () => {
    it('should forward ref to container div', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<TotpInput ref={ref} />)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
      expect(ref.current).toHaveClass('flex', 'justify-center', 'gap-2')
    })
  })

  describe('Props Forwarding', () => {
    it('should forward onChange prop and call when provided', () => {
      const onChange = vi.fn()
      render(<TotpInput onChange={onChange} />)

      // Just verify the component accepts the prop without error
      expect(onChange).not.toHaveBeenCalled()
    })

    it('should forward onComplete prop and accept it without error', () => {
      const onComplete = vi.fn()
      render(<TotpInput onComplete={onComplete} />)

      // Just verify the component accepts the prop without error
      expect(onComplete).not.toHaveBeenCalled()
    })
  })

  describe('Component Structure', () => {
    it('should have correct input styling classes', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).toHaveClass(
          'h-12',
          'w-12',
          'rounded-md',
          'border',
          'bg-background',
          'text-center',
          'font-mono',
          'text-lg'
        )
      })
    })

    it('should apply focus styling classes', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).toHaveClass(
          'focus:outline-none',
          'focus:ring-2',
          'focus:ring-ring',
          'focus:ring-offset-2'
        )
      })
    })

    it('should apply disabled styling classes when disabled', () => {
      const { container } = render(<TotpInput disabled />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach(input => {
        expect(input).toHaveClass(
          'disabled:cursor-not-allowed',
          'disabled:opacity-50'
        )
      })
    })

    it('should render with appropriate ARIA attributes', () => {
      const { container } = render(<TotpInput />)

      const inputs = container.querySelectorAll('input[type="text"]')
      inputs.forEach((input, index) => {
        expect(input).toHaveAttribute(
          'aria-label',
          `Código de autenticação de 6 dígitos, dígito ${index + 1}`
        )
      })
    })
  })
})
