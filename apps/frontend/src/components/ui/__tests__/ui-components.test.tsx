/**
 * UI Components Integration Tests
 * 
 * Simple tests for UI components without complex form dependencies
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

// Import simple UI components to test
import { Button } from '../button'
import { Badge } from '../badge'
import { Card, CardContent, CardHeader, CardTitle } from '../card'
import { Alert, AlertDescription } from '../alert'
import { Progress } from '../progress'

describe('Button Component Tests', () => {
  it('renders button with text', () => {
    render(<Button>Test Button</Button>)
    expect(screen.getByRole('button', { name: 'Test Button' })).toBeInTheDocument()
  })

  it('handles click events', () => {
    let clicked = false
    const handleClick = () => { clicked = true }
    
    render(<Button onClick={handleClick}>Click Me</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(clicked).toBe(true)
  })

  it('renders different variants correctly', () => {
    render(
      <>
        <Button variant="default">Default</Button>
        <Button variant="destructive">Destructive</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="secondary">Secondary</Button>
      </>
    )

    expect(screen.getByRole('button', { name: 'Default' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Destructive' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Outline' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Secondary' })).toBeInTheDocument()
  })

  it('can be disabled', () => {
    render(<Button disabled>Disabled Button</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })
})

describe('Badge Component Tests', () => {
  it('renders badge with text', () => {
    render(<Badge>Test Badge</Badge>)
    expect(screen.getByText('Test Badge')).toBeInTheDocument()
  })

  it('renders different variants', () => {
    render(
      <>
        <Badge variant="default">Default</Badge>
        <Badge variant="secondary">Secondary</Badge>
        <Badge variant="destructive">Destructive</Badge>
        <Badge variant="outline">Outline</Badge>
      </>
    )

    expect(screen.getByText('Default')).toBeInTheDocument()
    expect(screen.getByText('Secondary')).toBeInTheDocument()
    expect(screen.getByText('Destructive')).toBeInTheDocument()
    expect(screen.getByText('Outline')).toBeInTheDocument()
  })
})

describe('Card Component Tests', () => {
  it('renders card structure correctly', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card content goes here</p>
        </CardContent>
      </Card>
    )

    expect(screen.getByText('Card Title')).toBeInTheDocument()
    expect(screen.getByText('Card content goes here')).toBeInTheDocument()
  })

  it('applies correct CSS classes', () => {
    render(
      <Card data-testid="test-card">
        <CardContent>Content</CardContent>
      </Card>
    )

    const card = screen.getByTestId('test-card')
    expect(card).toHaveClass('bg-card', 'border', 'shadow-sm')
  })
})

describe('Alert Component Tests', () => {
  it('renders alert with description', () => {
    render(
      <Alert>
        <AlertDescription>
          This is an alert description
        </AlertDescription>
      </Alert>
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('This is an alert description')).toBeInTheDocument()
  })

  it('renders different variants', () => {
    render(
      <>
        <Alert variant="default">
          <AlertDescription>Default alert</AlertDescription>
        </Alert>
        <Alert variant="destructive">
          <AlertDescription>Destructive alert</AlertDescription>
        </Alert>
      </>
    )

    expect(screen.getByText('Default alert')).toBeInTheDocument()
    expect(screen.getByText('Destructive alert')).toBeInTheDocument()
  })
})

describe('Progress Component Tests', () => {
  it('renders progress bar', () => {
    render(<Progress value={50} aria-label="Loading progress" />)
    
    const progressBar = screen.getByLabelText('Loading progress')
    expect(progressBar).toBeInTheDocument()
  })

  it('handles different progress values', () => {
    render(
      <>
        <Progress value={0} aria-label="0% progress" />
        <Progress value={25} aria-label="25% progress" />
        <Progress value={50} aria-label="50% progress" />
        <Progress value={75} aria-label="75% progress" />
        <Progress value={100} aria-label="100% progress" />
      </>
    )

    expect(screen.getByLabelText('0% progress')).toBeInTheDocument()
    expect(screen.getByLabelText('25% progress')).toBeInTheDocument()
    expect(screen.getByLabelText('50% progress')).toBeInTheDocument()
    expect(screen.getByLabelText('75% progress')).toBeInTheDocument()
    expect(screen.getByLabelText('100% progress')).toBeInTheDocument()
  })
})

describe('Component Composition Tests', () => {
  it('renders complex component composition', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Dashboard Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert>
              <AlertDescription>
                System is running normally
              </AlertDescription>
            </Alert>
            
            <div>
              <p className="text-sm text-muted-foreground mb-2">Upload Progress</p>
              <Progress value={75} aria-label="Upload progress" />
            </div>
            
            <div className="flex gap-2">
              <Badge variant="secondary">Active</Badge>
              <Badge variant="outline">Monitoring</Badge>
            </div>
            
            <Button className="w-full">Refresh Status</Button>
          </div>
        </CardContent>
      </Card>
    )

    // Verify all components render together correctly
    expect(screen.getByText('Dashboard Status')).toBeInTheDocument()
    expect(screen.getByText('System is running normally')).toBeInTheDocument()
    expect(screen.getByText('Upload Progress')).toBeInTheDocument()
    expect(screen.getByLabelText('Upload progress')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Monitoring')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Refresh Status' })).toBeInTheDocument()
  })
})