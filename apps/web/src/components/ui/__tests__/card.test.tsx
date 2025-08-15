import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, it, expect } from 'vitest'

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../card'

describe('Card Components', () => {
  describe('Card', () => {
    it('should render a div with correct classes', () => {
      render(<Card data-testid="card">Card content</Card>)
      const card = screen.getByTestId('card')

      expect(card).toBeInTheDocument()
      expect(card.tagName).toBe('DIV')
      expect(card).toHaveClass(
        'rounded-lg',
        'border',
        'bg-card',
        'text-card-foreground',
        'shadow-sm'
      )
      expect(card).toHaveTextContent('Card content')
    })

    it('should accept custom className', () => {
      render(
        <Card className="custom-class" data-testid="card">
          Content
        </Card>
      )
      const card = screen.getByTestId('card')

      expect(card).toHaveClass('custom-class')
      expect(card).toHaveClass('rounded-lg') // Should still have base classes
    })

    it('should forward all props', () => {
      render(
        <Card data-testid="card" id="test-card" role="region">
          Content
        </Card>
      )
      const card = screen.getByTestId('card')

      expect(card).toHaveAttribute('id', 'test-card')
      expect(card).toHaveAttribute('role', 'region')
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<Card ref={ref}>Content</Card>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
      expect(ref.current).toHaveTextContent('Content')
    })
  })

  describe('CardHeader', () => {
    it('should render with correct default classes', () => {
      render(<CardHeader data-testid="header">Header content</CardHeader>)
      const header = screen.getByTestId('header')

      expect(header).toBeInTheDocument()
      expect(header.tagName).toBe('DIV')
      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6')
      expect(header).toHaveTextContent('Header content')
    })

    it('should accept custom className', () => {
      render(
        <CardHeader className="header-custom" data-testid="header">
          Content
        </CardHeader>
      )
      const header = screen.getByTestId('header')

      expect(header).toHaveClass('header-custom')
      expect(header).toHaveClass('flex') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<CardHeader ref={ref}>Header</CardHeader>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('CardTitle', () => {
    it('should render as h3 with correct classes', () => {
      render(<CardTitle data-testid="title">Card Title</CardTitle>)
      const title = screen.getByTestId('title')

      expect(title).toBeInTheDocument()
      expect(title.tagName).toBe('H3')
      expect(title).toHaveClass(
        'text-2xl',
        'font-semibold',
        'leading-none',
        'tracking-tight'
      )
      expect(title).toHaveTextContent('Card Title')
    })

    it('should accept custom className', () => {
      render(
        <CardTitle className="title-custom" data-testid="title">
          Title
        </CardTitle>
      )
      const title = screen.getByTestId('title')

      expect(title).toHaveClass('title-custom')
      expect(title).toHaveClass('text-2xl') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLParagraphElement>()
      render(<CardTitle ref={ref}>Title</CardTitle>)

      expect(ref.current).toBeInstanceOf(HTMLHeadingElement)
    })
  })

  describe('CardDescription', () => {
    it('should render as p with correct classes', () => {
      render(
        <CardDescription data-testid="description">
          Description text
        </CardDescription>
      )
      const description = screen.getByTestId('description')

      expect(description).toBeInTheDocument()
      expect(description.tagName).toBe('P')
      expect(description).toHaveClass('text-sm', 'text-muted-foreground')
      expect(description).toHaveTextContent('Description text')
    })

    it('should accept custom className', () => {
      render(
        <CardDescription className="desc-custom" data-testid="description">
          Desc
        </CardDescription>
      )
      const description = screen.getByTestId('description')

      expect(description).toHaveClass('desc-custom')
      expect(description).toHaveClass('text-sm') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLParagraphElement>()
      render(<CardDescription ref={ref}>Description</CardDescription>)

      expect(ref.current).toBeInstanceOf(HTMLParagraphElement)
    })
  })

  describe('CardContent', () => {
    it('should render with correct default classes', () => {
      render(<CardContent data-testid="content">Card content</CardContent>)
      const content = screen.getByTestId('content')

      expect(content).toBeInTheDocument()
      expect(content.tagName).toBe('DIV')
      expect(content).toHaveClass('p-6', 'pt-0')
      expect(content).toHaveTextContent('Card content')
    })

    it('should accept custom className', () => {
      render(
        <CardContent className="content-custom" data-testid="content">
          Content
        </CardContent>
      )
      const content = screen.getByTestId('content')

      expect(content).toHaveClass('content-custom')
      expect(content).toHaveClass('p-6') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<CardContent ref={ref}>Content</CardContent>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('CardFooter', () => {
    it('should render with correct default classes', () => {
      render(<CardFooter data-testid="footer">Footer content</CardFooter>)
      const footer = screen.getByTestId('footer')

      expect(footer).toBeInTheDocument()
      expect(footer.tagName).toBe('DIV')
      expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0')
      expect(footer).toHaveTextContent('Footer content')
    })

    it('should accept custom className', () => {
      render(
        <CardFooter className="footer-custom" data-testid="footer">
          Footer
        </CardFooter>
      )
      const footer = screen.getByTestId('footer')

      expect(footer).toHaveClass('footer-custom')
      expect(footer).toHaveClass('flex') // Should still have base classes
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<CardFooter ref={ref}>Footer</CardFooter>)

      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('Card Component Integration', () => {
    it('should render complete card structure correctly', () => {
      render(
        <Card data-testid="complete-card">
          <CardHeader data-testid="card-header">
            <CardTitle data-testid="card-title">Test Card</CardTitle>
            <CardDescription data-testid="card-description">
              This is a test card description
            </CardDescription>
          </CardHeader>
          <CardContent data-testid="card-content">
            This is the main content of the card
          </CardContent>
          <CardFooter data-testid="card-footer">
            <button>Action Button</button>
          </CardFooter>
        </Card>
      )

      // Verify all parts are rendered
      expect(screen.getByTestId('complete-card')).toBeInTheDocument()
      expect(screen.getByTestId('card-header')).toBeInTheDocument()
      expect(screen.getByTestId('card-title')).toBeInTheDocument()
      expect(screen.getByTestId('card-description')).toBeInTheDocument()
      expect(screen.getByTestId('card-content')).toBeInTheDocument()
      expect(screen.getByTestId('card-footer')).toBeInTheDocument()

      // Verify content
      expect(screen.getByText('Test Card')).toBeInTheDocument()
      expect(
        screen.getByText('This is a test card description')
      ).toBeInTheDocument()
      expect(
        screen.getByText('This is the main content of the card')
      ).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: 'Action Button' })
      ).toBeInTheDocument()
    })

    it('should handle partial card structures', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Simple Card</CardTitle>
          </CardHeader>
          <CardContent>Just content, no footer</CardContent>
        </Card>
      )

      expect(screen.getByText('Simple Card')).toBeInTheDocument()
      expect(screen.getByText('Just content, no footer')).toBeInTheDocument()
    })
  })
})
