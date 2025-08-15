/**
 * Basic tests for Alert components
 * CLAUDE.md Compliant: Only external mocking, tests actual component behavior
 */

import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect, vi } from 'vitest'

import { Alert, AlertDescription, AlertTitle } from '../alert'

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  AlertCircle: ({ className }: { className?: string }) => (
    <span data-testid="alert-circle-icon" className={className} />
  ),
}))

describe('Alert Components', () => {
  it('should render Alert with title and description', () => {
    render(
      <Alert>
        <AlertTitle>Alert Title</AlertTitle>
        <AlertDescription>This is an alert description</AlertDescription>
      </Alert>
    )

    expect(screen.getByText('Alert Title')).toBeInTheDocument()
    expect(screen.getByText('This is an alert description')).toBeInTheDocument()
  })

  it('should render different alert variants', () => {
    render(
      <div>
        <Alert variant="default">
          <AlertDescription>Default alert</AlertDescription>
        </Alert>
        <Alert variant="destructive">
          <AlertDescription>Destructive alert</AlertDescription>
        </Alert>
      </div>
    )

    const defaultAlert = screen
      .getByText('Default alert')
      .closest('[role="alert"]')
    const destructiveAlert = screen
      .getByText('Destructive alert')
      .closest('[role="alert"]')

    expect(defaultAlert).toHaveClass('border')
    expect(destructiveAlert).toHaveClass('border-destructive/50')
  })

  it('should render alert with icon', () => {
    render(
      <Alert>
        <span data-testid="alert-circle-icon" />
        <AlertTitle>Alert with Icon</AlertTitle>
        <AlertDescription>Alert description</AlertDescription>
      </Alert>
    )

    expect(screen.getByTestId('alert-circle-icon')).toBeInTheDocument()
    expect(screen.getByText('Alert with Icon')).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    render(
      <Alert className="custom-alert">
        <AlertDescription>Custom alert</AlertDescription>
      </Alert>
    )

    const alert = screen.getByText('Custom alert').closest('[role="alert"]')
    expect(alert).toHaveClass('custom-alert')
  })

  it('should forward refs correctly', () => {
    const alertRef = React.createRef<HTMLDivElement>()

    render(
      <Alert ref={alertRef}>
        <AlertDescription>Alert content</AlertDescription>
      </Alert>
    )

    expect(alertRef.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should render alert without title', () => {
    render(
      <Alert>
        <AlertDescription>Just description</AlertDescription>
      </Alert>
    )

    expect(screen.getByText('Just description')).toBeInTheDocument()
  })
})
