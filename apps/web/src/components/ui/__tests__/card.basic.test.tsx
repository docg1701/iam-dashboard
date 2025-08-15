/**
 * Basic tests for Card components
 * CLAUDE.md Compliant: Only external mocking, tests actual component behavior
 */

import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect } from 'vitest'

import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from '../card'

describe('Card Components', () => {
  it('should render Card with all subcomponents', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card Title</CardTitle>
          <CardDescription>Test card description</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Card content goes here</p>
        </CardContent>
        <CardFooter>
          <p>Card footer</p>
        </CardFooter>
      </Card>
    )

    expect(screen.getByText('Test Card Title')).toBeInTheDocument()
    expect(screen.getByText('Test card description')).toBeInTheDocument()
    expect(screen.getByText('Card content goes here')).toBeInTheDocument()
    expect(screen.getByText('Card footer')).toBeInTheDocument()
  })

  it('should apply correct CSS classes', () => {
    render(
      <Card className="custom-card">
        <CardHeader className="custom-header">
          <CardTitle className="custom-title">Title</CardTitle>
          <CardDescription className="custom-desc">Description</CardDescription>
        </CardHeader>
        <CardContent className="custom-content">Content</CardContent>
        <CardFooter className="custom-footer">Footer</CardFooter>
      </Card>
    )

    const card = screen.getByText('Title').closest('[class*="border"]')
    expect(card).toHaveClass('custom-card')
    expect(card).toHaveClass('rounded-lg')
    expect(card).toHaveClass('border')

    expect(screen.getByText('Title')).toHaveClass('custom-title')
    expect(screen.getByText('Description')).toHaveClass('custom-desc')
    expect(screen.getByText('Content')).toHaveClass('custom-content')
    expect(screen.getByText('Footer')).toHaveClass('custom-footer')
  })

  it('should render Card without optional components', () => {
    render(
      <Card>
        <CardContent>Simple card content</CardContent>
      </Card>
    )

    expect(screen.getByText('Simple card content')).toBeInTheDocument()
  })

  it('should forward refs correctly', () => {
    const cardRef = React.createRef<HTMLDivElement>()

    render(
      <Card ref={cardRef}>
        <CardContent>Content</CardContent>
      </Card>
    )

    expect(cardRef.current).toBeInstanceOf(HTMLDivElement)
  })
})
