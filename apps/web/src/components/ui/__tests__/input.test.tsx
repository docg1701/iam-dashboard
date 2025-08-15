import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { describe, it, expect, vi } from 'vitest'

import { Input } from '../input'

describe('Input Component', () => {
  describe('Basic Rendering', () => {
    it('should render input element', () => {
      render(<Input data-testid="input" />)
      const input = screen.getByTestId('input')

      expect(input).toBeInTheDocument()
      expect(input.tagName).toBe('INPUT')
    })

    it('should apply default classes', () => {
      render(<Input data-testid="input" />)
      const input = screen.getByTestId('input')

      expect(input).toHaveClass(
        'flex',
        'h-10',
        'w-full',
        'rounded-md',
        'border',
        'border-input',
        'bg-background',
        'px-3',
        'py-2',
        'text-sm'
      )
    })

    it('should forward all standard input props', () => {
      render(
        <Input
          data-testid="input"
          type="email"
          placeholder="Enter email"
          disabled
          required
          value="test@example.com"
          onChange={() => {}}
        />
      )
      const input = screen.getByTestId('input')

      expect(input).toHaveAttribute('type', 'email')
      expect(input).toHaveAttribute('placeholder', 'Enter email')
      expect(input).toBeDisabled()
      expect(input).toBeRequired()
      expect(input).toHaveValue('test@example.com')
    })

    it('should accept custom className', () => {
      render(<Input className="custom-class" data-testid="input" />)
      const input = screen.getByTestId('input')

      expect(input).toHaveClass('custom-class')
      expect(input).toHaveClass('flex') // Should still have base classes
    })
  })

  describe('Label Functionality', () => {
    it('should render label when provided', () => {
      render(<Input label="Email Address" data-testid="input" />)

      const label = screen.getByText('Email Address')
      const input = screen.getByTestId('input')

      expect(label).toBeInTheDocument()
      expect(label.tagName).toBe('LABEL')
      expect(label).toHaveClass('text-sm', 'font-medium')

      // Label should be associated with input
      expect(label).toHaveAttribute('for', input.id)
    })

    it('should not render label when not provided', () => {
      render(<Input data-testid="input" />)

      expect(screen.queryByText('label')).not.toBeInTheDocument()
    })

    it('should use custom id when provided', () => {
      render(<Input id="custom-id" label="Custom Label" />)

      const input = screen.getByRole('textbox')
      const label = screen.getByText('Custom Label')

      expect(input).toHaveAttribute('id', 'custom-id')
      expect(label).toHaveAttribute('for', 'custom-id')
    })

    it('should generate unique id when not provided', () => {
      render(
        <div>
          <Input label="First Input" data-testid="input1" />
          <Input label="Second Input" data-testid="input2" />
        </div>
      )

      const input1 = screen.getByTestId('input1')
      const input2 = screen.getByTestId('input2')

      expect(input1.id).toBeTruthy()
      expect(input2.id).toBeTruthy()
      expect(input1.id).not.toBe(input2.id)
    })
  })

  describe('Error State', () => {
    it('should display error message when error prop is provided', () => {
      render(<Input error="This field is required" data-testid="input" />)

      const errorMessage = screen.getByText('This field is required')
      const input = screen.getByTestId('input')

      expect(errorMessage).toBeInTheDocument()
      expect(errorMessage.tagName).toBe('P')
      expect(errorMessage).toHaveClass('text-sm', 'text-destructive')

      // Input should have error styling
      expect(input).toHaveClass(
        'border-destructive',
        'focus-visible:ring-destructive'
      )
    })

    it('should not display error message when error prop is not provided', () => {
      render(<Input data-testid="input" />)

      expect(screen.queryByText(/required/i)).not.toBeInTheDocument()
    })

    it('should hide helper text when error is shown', () => {
      render(
        <Input
          error="Error message"
          helperText="Helper text"
          data-testid="input"
        />
      )

      expect(screen.getByText('Error message')).toBeInTheDocument()
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    })
  })

  describe('Helper Text', () => {
    it('should display helper text when provided and no error', () => {
      render(
        <Input helperText="Enter your email address" data-testid="input" />
      )

      const helperText = screen.getByText('Enter your email address')

      expect(helperText).toBeInTheDocument()
      expect(helperText.tagName).toBe('P')
      expect(helperText).toHaveClass('text-sm', 'text-muted-foreground')
    })

    it('should not display helper text when not provided', () => {
      render(<Input data-testid="input" />)

      expect(screen.queryByText(/enter/i)).not.toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('should handle user input correctly', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()

      render(<Input onChange={handleChange} data-testid="input" />)
      const input = screen.getByTestId('input')

      await user.type(input, 'test@example.com')

      expect(handleChange).toHaveBeenCalled()
      expect(input).toHaveValue('test@example.com')
    })

    it('should handle focus and blur events', async () => {
      const user = userEvent.setup()
      const handleFocus = vi.fn()
      const handleBlur = vi.fn()

      render(
        <Input onFocus={handleFocus} onBlur={handleBlur} data-testid="input" />
      )
      const input = screen.getByTestId('input')

      await user.click(input)
      expect(handleFocus).toHaveBeenCalled()

      await user.tab()
      expect(handleBlur).toHaveBeenCalled()
    })

    it('should be accessible via keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <div>
          <Input label="First Input" />
          <Input label="Second Input" />
        </div>
      )

      const firstInput = screen.getByLabelText('First Input')
      const secondInput = screen.getByLabelText('Second Input')

      firstInput.focus()
      expect(firstInput).toHaveFocus()

      await user.tab()
      expect(secondInput).toHaveFocus()
    })
  })

  describe('Ref Forwarding', () => {
    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLInputElement>()
      render(<Input ref={ref} />)

      expect(ref.current).toBeInstanceOf(HTMLInputElement)
    })

    it('should allow calling input methods via ref', () => {
      const ref = React.createRef<HTMLInputElement>()
      render(<Input ref={ref} />)

      expect(ref.current?.focus).toBeDefined()
      expect(ref.current?.blur).toBeDefined()
      expect(ref.current?.select).toBeDefined()
    })
  })

  describe('Input Types', () => {
    it('should handle different input types', () => {
      const { rerender } = render(<Input type="email" data-testid="input" />)
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'email')

      rerender(<Input type="password" data-testid="input" />)
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'password')

      rerender(<Input type="number" data-testid="input" />)
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'number')
    })

    it('should default to text type when not specified', () => {
      render(<Input data-testid="input" />)
      const input = screen.getByTestId('input') as HTMLInputElement

      // HTML input defaults to text type when not specified (in .type property, not attribute)
      expect(input.type).toBe('text')
    })
  })

  describe('Complete Component Integration', () => {
    it('should render complete input with all features', () => {
      render(
        <Input
          id="complete-input"
          label="Complete Input Example"
          type="email"
          placeholder="user@example.com"
          helperText="We'll never share your email"
          data-testid="input"
        />
      )

      const input = screen.getByTestId('input')
      const label = screen.getByText('Complete Input Example')
      const helperText = screen.getByText("We'll never share your email")

      expect(input).toBeInTheDocument()
      expect(label).toBeInTheDocument()
      expect(helperText).toBeInTheDocument()

      expect(input).toHaveAttribute('id', 'complete-input')
      expect(input).toHaveAttribute('type', 'email')
      expect(input).toHaveAttribute('placeholder', 'user@example.com')
      expect(label).toHaveAttribute('for', 'complete-input')
    })

    it('should handle error state overriding helper text', () => {
      render(
        <Input
          label="Error Example"
          helperText="This should be hidden"
          error="This is an error"
          data-testid="input"
        />
      )

      expect(screen.getByText('This is an error')).toBeInTheDocument()
      expect(
        screen.queryByText('This should be hidden')
      ).not.toBeInTheDocument()

      const input = screen.getByTestId('input')
      expect(input).toHaveClass('border-destructive')
    })
  })
})
