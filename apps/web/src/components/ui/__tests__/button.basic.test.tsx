/**
 * Basic tests for Button component
 * CLAUDE.md Compliant: Only external mocking, tests actual component behavior
 */

import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect } from 'vitest'

import { Button } from '../button'

describe('Button Component', () => {
  it('should render with default props', () => {
    render(<Button>Click me</Button>)

    const button = screen.getByRole('button', { name: 'Click me' })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('bg-primary')
  })

  it('should render different variants', () => {
    render(
      <div>
        <Button variant="secondary">Secondary</Button>
        <Button variant="destructive">Destructive</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="link">Link</Button>
      </div>
    )

    expect(screen.getByText('Secondary')).toHaveClass('bg-secondary')
    expect(screen.getByText('Destructive')).toHaveClass('bg-destructive')
    expect(screen.getByText('Outline')).toHaveClass('border-input')
    expect(screen.getByText('Ghost')).toHaveClass('hover:bg-accent')
    expect(screen.getByText('Link')).toHaveClass('text-primary')
  })

  it('should render different sizes', () => {
    render(
      <div>
        <Button size="sm">Small</Button>
        <Button size="lg">Large</Button>
        <Button size="icon">Icon</Button>
      </div>
    )

    expect(screen.getByText('Small')).toHaveClass('h-9')
    expect(screen.getByText('Large')).toHaveClass('h-11')
    expect(screen.getByText('Icon')).toHaveClass('h-10')
  })

  it('should handle disabled state', () => {
    render(<Button disabled>Disabled</Button>)

    const button = screen.getByRole('button', { name: 'Disabled' })
    expect(button).toBeDisabled()
    expect(button).toHaveClass('disabled:pointer-events-none')
  })

  it('should render as child component when asChild is true', () => {
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>
    )

    const link = screen.getByRole('link', { name: 'Link Button' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/test')
  })
})
