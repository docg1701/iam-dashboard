import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect, vi } from 'vitest'

import {
  Toast,
  ToastAction,
  ToastClose,
  ToastDescription,
  ToastTitle,
  ToastViewport,
  ToastProvider,
} from '../toast'

// Mock the Radix UI primitives to focus on our component logic
vi.mock('@radix-ui/react-toast', () => ({
  Provider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="toast-provider">{children}</div>
  ),
  Viewport: React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
    function MockViewport({ className, children, ...props }, ref) {
      return (
        <div
          ref={ref}
          className={className}
          data-testid="toast-viewport"
          {...props}
        >
          {children}
        </div>
      )
    }
  ),
  Root: React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
    function MockRoot({ className, children, ...props }, ref) {
      return (
        <div
          ref={ref}
          className={className}
          data-testid="toast-root"
          {...props}
        >
          {children}
        </div>
      )
    }
  ),
  Action: React.forwardRef<HTMLButtonElement, React.ComponentProps<'button'>>(
    function MockAction({ className, children, ...props }, ref) {
      return (
        <button
          ref={ref}
          className={className}
          data-testid="toast-action"
          {...props}
        >
          {children}
        </button>
      )
    }
  ),
  Close: React.forwardRef<HTMLButtonElement, React.ComponentProps<'button'>>(
    function MockClose({ className, children, ...props }, ref) {
      return (
        <button
          ref={ref}
          className={className}
          data-testid="toast-close"
          {...props}
        >
          {children}
        </button>
      )
    }
  ),
  Title: React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
    function MockTitle({ className, children, ...props }, ref) {
      return (
        <div
          ref={ref}
          className={className}
          data-testid="toast-title"
          {...props}
        >
          {children}
        </div>
      )
    }
  ),
  Description: React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
    function MockDescription({ className, children, ...props }, ref) {
      return (
        <div
          ref={ref}
          className={className}
          data-testid="toast-description"
          {...props}
        >
          {children}
        </div>
      )
    }
  ),
}))

// Mock lucide-react
vi.mock('lucide-react', () => ({
  X: ({ className, ...props }: React.ComponentProps<'svg'>) => (
    <svg className={className} data-testid="x-icon" {...props}>
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  ),
}))

describe('Toast Components', () => {
  describe('ToastProvider', () => {
    it('should render provider wrapper', () => {
      render(
        <ToastProvider>
          <div>Toast content</div>
        </ToastProvider>
      )

      const provider = screen.getByTestId('toast-provider')
      expect(provider).toBeInTheDocument()
      expect(provider).toHaveTextContent('Toast content')
    })
  })

  describe('ToastViewport', () => {
    it('should render with correct default classes', () => {
      render(<ToastViewport>Viewport content</ToastViewport>)

      const viewport = screen.getByTestId('toast-viewport')
      expect(viewport).toBeInTheDocument()
      expect(viewport).toHaveClass(
        'fixed',
        'top-0',
        'z-[100]',
        'flex',
        'max-h-screen',
        'w-full',
        'flex-col-reverse',
        'p-4'
      )
      expect(viewport).toHaveTextContent('Viewport content')
    })

    it('should accept custom className', () => {
      render(<ToastViewport className="custom-viewport">Content</ToastViewport>)

      const viewport = screen.getByTestId('toast-viewport')
      expect(viewport).toHaveClass('custom-viewport')
      expect(viewport).toHaveClass('fixed') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<ToastViewport ref={ref}>Content</ToastViewport>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('Toast', () => {
    it('should render with default variant classes', () => {
      render(<Toast>Toast content</Toast>)

      const toast = screen.getByTestId('toast-root')
      expect(toast).toBeInTheDocument()
      expect(toast).toHaveClass('border', 'bg-background', 'text-foreground')
      expect(toast).toHaveTextContent('Toast content')
    })

    it('should render with destructive variant classes', () => {
      render(<Toast variant="destructive">Destructive toast</Toast>)

      const toast = screen.getByTestId('toast-root')
      expect(toast).toHaveClass(
        'destructive',
        'border-destructive',
        'bg-destructive',
        'text-destructive-foreground'
      )
      expect(toast).toHaveTextContent('Destructive toast')
    })

    it('should accept custom className', () => {
      render(<Toast className="custom-toast">Content</Toast>)

      const toast = screen.getByTestId('toast-root')
      expect(toast).toHaveClass('custom-toast')
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<Toast ref={ref}>Content</Toast>)

      expect(ref.current).toBeDefined()
    })

    it('should forward all props', () => {
      render(
        <Toast id="test-toast" role="alert">
          Content
        </Toast>
      )

      const toast = screen.getByTestId('toast-root')
      expect(toast).toHaveAttribute('id', 'test-toast')
      expect(toast).toHaveAttribute('role', 'alert')
    })
  })

  describe('ToastAction', () => {
    it('should render with correct default classes', () => {
      render(<ToastAction>Action Button</ToastAction>)

      const action = screen.getByTestId('toast-action')
      expect(action).toBeInTheDocument()
      expect(action.tagName).toBe('BUTTON')
      expect(action).toHaveClass(
        'inline-flex',
        'h-8',
        'shrink-0',
        'items-center',
        'justify-center',
        'rounded-md',
        'border',
        'bg-transparent'
      )
      expect(action).toHaveTextContent('Action Button')
    })

    it('should accept custom className', () => {
      render(<ToastAction className="custom-action">Action</ToastAction>)

      const action = screen.getByTestId('toast-action')
      expect(action).toHaveClass('custom-action')
      expect(action).toHaveClass('inline-flex') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>()
      render(<ToastAction ref={ref}>Action</ToastAction>)

      expect(ref.current).toBeDefined()
    })

    it('should forward all props', () => {
      render(
        <ToastAction onClick={() => {}} disabled>
          Action
        </ToastAction>
      )

      const action = screen.getByTestId('toast-action')
      expect(action).toBeDisabled()
    })
  })

  describe('ToastClose', () => {
    it('should render with correct default classes and icon', () => {
      render(<ToastClose />)

      const close = screen.getByTestId('toast-close')
      const icon = screen.getByTestId('x-icon')

      expect(close).toBeInTheDocument()
      expect(close.tagName).toBe('BUTTON')
      expect(close).toHaveClass(
        'absolute',
        'right-2',
        'top-2',
        'rounded-md',
        'p-1',
        'text-foreground/50'
      )
      expect(close).toHaveAttribute('toast-close', '')
      expect(icon).toBeInTheDocument()
      expect(icon).toHaveClass('h-4', 'w-4')
    })

    it('should accept custom className', () => {
      render(<ToastClose className="custom-close" />)

      const close = screen.getByTestId('toast-close')
      expect(close).toHaveClass('custom-close')
      expect(close).toHaveClass('absolute') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>()
      render(<ToastClose ref={ref} />)

      expect(ref.current).toBeDefined()
    })

    it('should forward all props', () => {
      render(<ToastClose onClick={() => {}} aria-label="Close toast" />)

      const close = screen.getByTestId('toast-close')
      expect(close).toHaveAttribute('aria-label', 'Close toast')
    })
  })

  describe('ToastTitle', () => {
    it('should render with correct default classes', () => {
      render(<ToastTitle>Toast Title</ToastTitle>)

      const title = screen.getByTestId('toast-title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass('text-sm', 'font-semibold')
      expect(title).toHaveTextContent('Toast Title')
    })

    it('should accept custom className', () => {
      render(<ToastTitle className="custom-title">Title</ToastTitle>)

      const title = screen.getByTestId('toast-title')
      expect(title).toHaveClass('custom-title')
      expect(title).toHaveClass('text-sm') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<ToastTitle ref={ref}>Title</ToastTitle>)

      expect(ref.current).toBeDefined()
    })

    it('should forward all props', () => {
      render(<ToastTitle id="toast-title">Title</ToastTitle>)

      const title = screen.getByTestId('toast-title')
      expect(title).toHaveAttribute('id', 'toast-title')
    })
  })

  describe('ToastDescription', () => {
    it('should render with correct default classes', () => {
      render(<ToastDescription>Toast description text</ToastDescription>)

      const description = screen.getByTestId('toast-description')
      expect(description).toBeInTheDocument()
      expect(description).toHaveClass('text-sm', 'opacity-90')
      expect(description).toHaveTextContent('Toast description text')
    })

    it('should accept custom className', () => {
      render(
        <ToastDescription className="custom-desc">Description</ToastDescription>
      )

      const description = screen.getByTestId('toast-description')
      expect(description).toHaveClass('custom-desc')
      expect(description).toHaveClass('text-sm') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<ToastDescription ref={ref}>Description</ToastDescription>)

      expect(ref.current).toBeDefined()
    })

    it('should forward all props', () => {
      render(<ToastDescription id="toast-desc">Description</ToastDescription>)

      const description = screen.getByTestId('toast-description')
      expect(description).toHaveAttribute('id', 'toast-desc')
    })
  })

  describe('Toast Component Integration', () => {
    it('should render complete toast with all components', () => {
      render(
        <ToastProvider>
          <ToastViewport>
            <Toast variant="default">
              <ToastTitle>Success</ToastTitle>
              <ToastDescription>
                Operation completed successfully
              </ToastDescription>
              <ToastAction>Undo</ToastAction>
              <ToastClose />
            </Toast>
          </ToastViewport>
        </ToastProvider>
      )

      expect(screen.getByTestId('toast-provider')).toBeInTheDocument()
      expect(screen.getByTestId('toast-viewport')).toBeInTheDocument()
      expect(screen.getByTestId('toast-root')).toBeInTheDocument()
      expect(screen.getByTestId('toast-title')).toHaveTextContent('Success')
      expect(screen.getByTestId('toast-description')).toHaveTextContent(
        'Operation completed successfully'
      )
      expect(screen.getByTestId('toast-action')).toHaveTextContent('Undo')
      expect(screen.getByTestId('toast-close')).toBeInTheDocument()
      expect(screen.getByTestId('x-icon')).toBeInTheDocument()
    })

    it('should render destructive toast correctly', () => {
      render(
        <Toast variant="destructive">
          <ToastTitle>Error</ToastTitle>
          <ToastDescription>Something went wrong</ToastDescription>
          <ToastClose />
        </Toast>
      )

      const toast = screen.getByTestId('toast-root')
      expect(toast).toHaveClass('destructive', 'border-destructive')
      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should render minimal toast with just description', () => {
      render(
        <Toast>
          <ToastDescription>Simple message</ToastDescription>
        </Toast>
      )

      expect(screen.getByText('Simple message')).toBeInTheDocument()
      expect(screen.queryByTestId('toast-title')).not.toBeInTheDocument()
      expect(screen.queryByTestId('toast-action')).not.toBeInTheDocument()
    })
  })
})
