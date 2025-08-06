/**
 * Basic Component Rendering Test
 * Tests fundamental UI component rendering and interaction
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../button'
import { Input } from '../input'
import { Card, CardContent, CardHeader, CardTitle } from '../card'
import { Badge } from '../badge'

describe('Basic Component Rendering', () => {
  describe('Button Component', () => {
    it('should render button with correct text', () => {
      render(<Button>Click me</Button>)
      
      const button = screen.getByRole('button', { name: /click me/i })
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('Click me')
    })

    it('should handle click events with real callback function', async () => {
      const user = userEvent.setup()
      
      // Real callback function that tracks state - no vi.fn()
      let clickCount = 0
      const handleClick = () => {
        clickCount += 1
      }
      
      render(<Button onClick={handleClick}>Click me</Button>)
      
      const button = screen.getByRole('button', { name: /click me/i })
      await user.click(button)
      
      expect(clickCount).toBe(1)
    })

    it('should render different button variants', () => {
      const { rerender } = render(<Button variant="default">Default</Button>)
      const defaultButton = screen.getByRole('button')
      expect(defaultButton).toBeInTheDocument()
      
      rerender(<Button variant="destructive">Destructive</Button>)
      const destructiveButton = screen.getByRole('button')
      expect(destructiveButton).toBeInTheDocument()
      expect(destructiveButton).toHaveTextContent('Destructive')
    })

    it('should handle disabled state', () => {
      render(<Button disabled>Disabled Button</Button>)
      
      const button = screen.getByRole('button', { name: /disabled button/i })
      expect(button).toBeDisabled()
    })

    it('should render loading state', () => {
      render(<Button disabled>Loading...</Button>)
      
      const button = screen.getByRole('button', { name: /loading/i })
      expect(button).toBeInTheDocument()
      expect(button).toBeDisabled()
    })
  })

  describe('Input Component', () => {
    it('should render input with placeholder', () => {
      render(<Input placeholder="Enter your name" />)
      
      const input = screen.getByPlaceholderText('Enter your name')
      expect(input).toBeInTheDocument()
    })

    it('should handle value changes', async () => {
      const user = userEvent.setup()
      
      render(<Input placeholder="Type here" />)
      
      const input = screen.getByPlaceholderText('Type here')
      await user.type(input, 'Hello World')
      
      expect(input).toHaveValue('Hello World')
    })

    it('should handle controlled input with real change handler', async () => {
      const user = userEvent.setup()
      
      // Real change handler that tracks state - no vi.fn()
      let inputValue = 'initial'
      let changeCount = 0
      const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        inputValue = event.target.value
        changeCount += 1
      }
      
      render(<Input value={inputValue} onChange={handleChange} />)
      
      const input = screen.getByDisplayValue('initial')
      await user.clear(input)
      await user.type(input, 'new value')
      
      // onChange should be called for each keystroke
      expect(changeCount).toBeGreaterThan(0)
    })

    it('should render input with different types', () => {
      const { rerender } = render(<Input type="text" placeholder="Text input" />)
      let input = screen.getByPlaceholderText('Text input')
      expect(input).toHaveAttribute('type', 'text')
      
      rerender(<Input type="password" placeholder="Password input" />)
      input = screen.getByPlaceholderText('Password input')
      expect(input).toHaveAttribute('type', 'password')
      
      rerender(<Input type="email" placeholder="Email input" />)
      input = screen.getByPlaceholderText('Email input')
      expect(input).toHaveAttribute('type', 'email')
    })

    it('should handle disabled state', () => {
      render(<Input disabled placeholder="Disabled input" />)
      
      const input = screen.getByPlaceholderText('Disabled input')
      expect(input).toBeDisabled()
    })
  })

  describe('Card Component', () => {
    it('should render card with header and content', () => {
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

    it('should render card without header', () => {
      render(
        <Card>
          <CardContent>
            <p>Just content</p>
          </CardContent>
        </Card>
      )
      
      expect(screen.getByText('Just content')).toBeInTheDocument()
    })

    it('should handle complex card content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>User Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Name: John Doe</p>
            <p>Email: john@example.com</p>
            <Button>Edit Profile</Button>
          </CardContent>
        </Card>
      )
      
      expect(screen.getByText('User Profile')).toBeInTheDocument()
      expect(screen.getByText('Name: John Doe')).toBeInTheDocument()
      expect(screen.getByText('Email: john@example.com')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /edit profile/i })).toBeInTheDocument()
    })
  })

  describe('Badge Component', () => {
    it('should render badge with text', () => {
      render(<Badge>Active</Badge>)
      
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('should render different badge variants', () => {
      const { rerender } = render(<Badge variant="default">Default</Badge>)
      expect(screen.getByText('Default')).toBeInTheDocument()
      
      rerender(<Badge variant="secondary">Secondary</Badge>)
      expect(screen.getByText('Secondary')).toBeInTheDocument()
      
      rerender(<Badge variant="destructive">Destructive</Badge>)
      expect(screen.getByText('Destructive')).toBeInTheDocument()
    })

    it('should render badge with custom content', () => {
      render(
        <Badge>
          <span>Status: </span>
          <strong>Online</strong>
        </Badge>
      )
      
      expect(screen.getByText('Status:')).toBeInTheDocument()
      expect(screen.getByText('Online')).toBeInTheDocument()
    })
  })

  describe('Component Interaction', () => {
    it('should handle form-like interactions with real handlers', async () => {
      const user = userEvent.setup()
      
      // Real submit handler that tracks state - no vi.fn()
      let submitCalled = false
      let formData = { username: '', password: '' }
      
      const handleSubmit = () => {
        submitCalled = true
      }
      
      const TestForm = () => (
        <Card>
          <CardHeader>
            <CardTitle>Login Form</CardTitle>
          </CardHeader>
          <CardContent>
            <div>
              <Input placeholder="Username" data-testid="username" />
            </div>
            <div>
              <Input type="password" placeholder="Password" data-testid="password" />
            </div>
            <Button onClick={handleSubmit} data-testid="submit">
              Login
            </Button>
          </CardContent>
        </Card>
      )
      
      render(<TestForm />)
      
      // Fill form
      const usernameInput = screen.getByTestId('username')
      const passwordInput = screen.getByTestId('password')
      const submitButton = screen.getByTestId('submit')
      
      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)
      
      expect(usernameInput).toHaveValue('testuser')
      expect(passwordInput).toHaveValue('password123')
      expect(submitCalled).toBe(true)
    })

    it('should handle keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <div>
          <Button>First Button</Button>
          <Button>Second Button</Button>
          <Input placeholder="Input field" />
        </div>
      )
      
      const firstButton = screen.getByText('First Button')
      const secondButton = screen.getByText('Second Button')
      const input = screen.getByPlaceholderText('Input field')
      
      // Start focus on first button
      firstButton.focus()
      expect(firstButton).toHaveFocus()
      
      // Tab to second button
      await user.tab()
      expect(secondButton).toHaveFocus()
      
      // Tab to input
      await user.tab()
      expect(input).toHaveFocus()
    })

    it('should handle accessibility attributes', () => {
      render(
        <div>
          <Button aria-label="Close dialog">×</Button>
          <Input aria-label="Search query" placeholder="Search..." />
          <Badge role="status" aria-live="polite">2 new messages</Badge>
        </div>
      )
      
      const closeButton = screen.getByLabelText('Close dialog')
      const searchInput = screen.getByLabelText('Search query')
      const statusBadge = screen.getByRole('status')
      
      expect(closeButton).toBeInTheDocument()
      expect(searchInput).toBeInTheDocument()
      expect(statusBadge).toBeInTheDocument()
      expect(statusBadge).toHaveAttribute('aria-live', 'polite')
    })
  })

  describe('Responsive and CSS Behavior', () => {
    it('should apply CSS classes correctly', () => {
      render(<Button className="custom-class">Styled Button</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    it('should handle conditional styling', () => {
      const isActive = true
      
      render(
        <Button className={isActive ? 'active-state' : 'inactive-state'}>
          Conditional Button
        </Button>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('active-state')
      expect(button).not.toHaveClass('inactive-state')
    })

    it('should render components with proper structure', () => {
      render(
        <Card data-testid="card-container">
          <CardHeader data-testid="card-header">
            <CardTitle>Structured Card</CardTitle>
          </CardHeader>
          <CardContent data-testid="card-content">
            Content
          </CardContent>
        </Card>
      )
      
      const card = screen.getByTestId('card-container')
      const header = screen.getByTestId('card-header')
      const content = screen.getByTestId('card-content')
      
      expect(card).toContainElement(header)
      expect(card).toContainElement(content)
    })
  })
})