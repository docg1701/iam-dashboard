import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect } from 'vitest'

import { Alert, AlertTitle, AlertDescription } from '../alert'

describe('Alert Components', () => {
  describe('Alert', () => {
    it('should render with default variant', () => {
      render(<Alert data-testid="alert">Alert content</Alert>)
      const alert = screen.getByTestId('alert')

      expect(alert).toBeInTheDocument()
      expect(alert.tagName).toBe('DIV')
      expect(alert).toHaveAttribute('role', 'alert')
      expect(alert).toHaveClass(
        'relative',
        'w-full',
        'rounded-lg',
        'border',
        'p-4'
      )
      expect(alert).toHaveClass('bg-background', 'text-foreground') // default variant classes
      expect(alert).toHaveTextContent('Alert content')
    })

    it('should render with destructive variant', () => {
      render(
        <Alert variant="destructive" data-testid="alert">
          Destructive alert
        </Alert>
      )
      const alert = screen.getByTestId('alert')

      expect(alert).toHaveClass('border-destructive/50', 'text-destructive')
      expect(alert).toHaveTextContent('Destructive alert')
    })

    it('should accept custom className', () => {
      render(
        <Alert className="custom-alert" data-testid="alert">
          Content
        </Alert>
      )
      const alert = screen.getByTestId('alert')

      expect(alert).toHaveClass('custom-alert')
      expect(alert).toHaveClass('relative') // Should still have base classes
    })

    it('should forward all props', () => {
      render(
        <Alert data-testid="alert" id="test-alert" aria-label="Test alert">
          Content
        </Alert>
      )
      const alert = screen.getByTestId('alert')

      expect(alert).toHaveAttribute('id', 'test-alert')
      expect(alert).toHaveAttribute('aria-label', 'Test alert')
      expect(alert).toHaveAttribute('role', 'alert') // Should always have alert role
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<Alert ref={ref}>Content</Alert>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
      expect(ref.current).toHaveTextContent('Content')
    })

    it('should handle empty content', () => {
      render(<Alert data-testid="alert" />)
      const alert = screen.getByTestId('alert')

      expect(alert).toBeInTheDocument()
      expect(alert).toBeEmptyDOMElement()
    })
  })

  describe('AlertTitle', () => {
    it('should render as h5 with correct classes', () => {
      render(<AlertTitle data-testid="title">Alert Title</AlertTitle>)
      const title = screen.getByTestId('title')

      expect(title).toBeInTheDocument()
      expect(title.tagName).toBe('H5')
      expect(title).toHaveClass(
        'mb-1',
        'font-medium',
        'leading-none',
        'tracking-tight'
      )
      expect(title).toHaveTextContent('Alert Title')
    })

    it('should accept custom className', () => {
      render(
        <AlertTitle className="custom-title" data-testid="title">
          Title
        </AlertTitle>
      )
      const title = screen.getByTestId('title')

      expect(title).toHaveClass('custom-title')
      expect(title).toHaveClass('mb-1') // Should still have base classes
    })

    it('should forward all props', () => {
      render(
        <AlertTitle data-testid="title" id="alert-title">
          Title
        </AlertTitle>
      )
      const title = screen.getByTestId('title')

      expect(title).toHaveAttribute('id', 'alert-title')
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLParagraphElement>()
      render(<AlertTitle ref={ref}>Title</AlertTitle>)

      expect(ref.current).toBeInstanceOf(HTMLHeadingElement)
    })
  })

  describe('AlertDescription', () => {
    it('should render as div with correct classes', () => {
      render(
        <AlertDescription data-testid="description">
          Alert description text
        </AlertDescription>
      )
      const description = screen.getByTestId('description')

      expect(description).toBeInTheDocument()
      expect(description.tagName).toBe('DIV')
      expect(description).toHaveClass('text-sm', '[&_p]:leading-relaxed')
      expect(description).toHaveTextContent('Alert description text')
    })

    it('should accept custom className', () => {
      render(
        <AlertDescription className="custom-desc" data-testid="description">
          Description
        </AlertDescription>
      )
      const description = screen.getByTestId('description')

      expect(description).toHaveClass('custom-desc')
      expect(description).toHaveClass('text-sm') // Should still have base classes
    })

    it('should forward all props', () => {
      render(
        <AlertDescription data-testid="description" id="alert-desc">
          Description
        </AlertDescription>
      )
      const description = screen.getByTestId('description')

      expect(description).toHaveAttribute('id', 'alert-desc')
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLParagraphElement>()
      render(<AlertDescription ref={ref}>Description</AlertDescription>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })

    it('should handle rich content with paragraphs', () => {
      render(
        <AlertDescription data-testid="description">
          <p>First paragraph</p>
          <p>Second paragraph</p>
        </AlertDescription>
      )
      const description = screen.getByTestId('description')

      expect(description).toHaveTextContent('First paragraphSecond paragraph')
      expect(description.querySelectorAll('p')).toHaveLength(2)
    })
  })

  describe('Alert Component Integration', () => {
    it('should render complete alert with title and description', () => {
      render(
        <Alert data-testid="complete-alert">
          <AlertTitle data-testid="alert-title">Information</AlertTitle>
          <AlertDescription data-testid="alert-description">
            This is an informational alert with both title and description.
          </AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('complete-alert')
      const title = screen.getByTestId('alert-title')
      const description = screen.getByTestId('alert-description')

      expect(alert).toBeInTheDocument()
      expect(title).toBeInTheDocument()
      expect(description).toBeInTheDocument()

      expect(title).toHaveTextContent('Information')
      expect(description).toHaveTextContent(
        'This is an informational alert with both title and description.'
      )
    })

    it('should render destructive alert with icon space', () => {
      render(
        <Alert variant="destructive" data-testid="error-alert">
          <svg data-testid="alert-icon" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" />
          </svg>
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>Something went wrong.</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('error-alert')
      const icon = screen.getByTestId('alert-icon')

      expect(alert).toHaveClass('text-destructive')
      expect(icon).toBeInTheDocument()
      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.getByText('Something went wrong.')).toBeInTheDocument()
    })

    it('should render alert with only description', () => {
      render(
        <Alert>
          <AlertDescription>
            Simple alert with just a description.
          </AlertDescription>
        </Alert>
      )

      expect(
        screen.getByText('Simple alert with just a description.')
      ).toBeInTheDocument()
      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })

    it('should render alert with only title', () => {
      render(
        <Alert>
          <AlertTitle>Just a title</AlertTitle>
        </Alert>
      )

      expect(screen.getByText('Just a title')).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 5 })).toBeInTheDocument()
    })

    it('should handle complex content structure', () => {
      render(
        <Alert variant="destructive">
          <svg data-testid="icon" width="16" height="16" />
          <AlertTitle>System Error</AlertTitle>
          <AlertDescription>
            <p>The following issues were found:</p>
            <ul>
              <li>Database connection failed</li>
              <li>Cache server unreachable</li>
            </ul>
            <p>Please contact support if the problem persists.</p>
          </AlertDescription>
        </Alert>
      )

      expect(screen.getByText('System Error')).toBeInTheDocument()
      expect(
        screen.getByText('The following issues were found:')
      ).toBeInTheDocument()
      expect(screen.getByText('Database connection failed')).toBeInTheDocument()
      expect(screen.getByText('Cache server unreachable')).toBeInTheDocument()
      expect(
        screen.getByText('Please contact support if the problem persists.')
      ).toBeInTheDocument()
      expect(screen.getByTestId('icon')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have correct ARIA role', () => {
      render(<Alert>Alert content</Alert>)
      const alert = screen.getByRole('alert')

      expect(alert).toBeInTheDocument()
      expect(alert).toHaveTextContent('Alert content')
    })

    it('should maintain accessibility with custom props', () => {
      render(
        <Alert aria-label="Custom alert" aria-describedby="alert-desc">
          <AlertTitle id="alert-title">Title</AlertTitle>
          <AlertDescription id="alert-desc">Description</AlertDescription>
        </Alert>
      )

      const alert = screen.getByRole('alert')
      expect(alert).toHaveAttribute('aria-label', 'Custom alert')
      expect(alert).toHaveAttribute('aria-describedby', 'alert-desc')
    })

    it('should work with screen readers', () => {
      render(
        <Alert>
          <AlertTitle>Accessibility Test</AlertTitle>
          <AlertDescription>
            This alert should be announced by screen readers
          </AlertDescription>
        </Alert>
      )

      const alert = screen.getByRole('alert')
      const title = screen.getByRole('heading', { level: 5 })

      expect(alert).toBeInTheDocument()
      expect(title).toBeInTheDocument()
      expect(title).toHaveTextContent('Accessibility Test')
    })
  })
})
