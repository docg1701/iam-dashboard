/**
 * Component Test Utilities
 * 
 * Advanced utilities for testing complex component behavior including
 * state changes, conditional rendering, and realistic user interactions.
 */

import { vi } from 'vitest'
import React from 'react'
import { fireEvent, waitFor } from '@testing-library/react'

/**
 * Enhanced Select Mock that can simulate real select interactions
 */
export const createEnhancedSelectMock = (testId: string = 'select') => {
  const SelectWrapper = ({ children, value, onValueChange, disabled, ...props }: any) => {
    const [isOpen, setIsOpen] = React.useState(false)
    const [currentValue, setCurrentValue] = React.useState(value)

    const handleSelect = (itemValue: string) => {
      setCurrentValue(itemValue)
      setIsOpen(false)
      if (onValueChange) {
        onValueChange(itemValue)
      }
    }

    React.useEffect(() => {
      setCurrentValue(value)
    }, [value])

    return (
      <div
        data-testid={testId}
        data-value={currentValue}
        data-disabled={disabled}
        data-open={isOpen}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        {...props}
      >
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, {
              onSelect: handleSelect,
              isOpen,
              currentValue,
            })
          }
          return child
        })}
      </div>
    )
  }

  const SelectContent = ({ children, onSelect, isOpen }: any) => {
    if (!isOpen) return null
    
    return (
      <div data-testid="select-content">
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, { onSelect })
          }
          return child
        })}
      </div>
    )
  }

  const SelectItem = ({ children, value, onSelect }: any) => {
    return (
      <div
        data-testid="select-item"
        data-value={value}
        onClick={() => onSelect?.(value)}
        style={{ cursor: 'pointer' }}
      >
        {children}
      </div>
    )
  }

  const SelectTrigger = ({ children }: any) => (
    <div data-testid="select-trigger">{children}</div>
  )

  const SelectValue = ({ placeholder, currentValue }: any) => (
    <div data-testid="select-value">
      {currentValue || placeholder}
    </div>
  )

  return {
    Select: SelectWrapper,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  }
}

/**
 * Enhanced Alert Mock that shows/hides based on conditions
 */
export const createEnhancedAlertMock = () => {
  const Alert = ({ children, variant, className, style, ...props }: any) => {
    return (
      <div
        data-testid="alert"
        data-variant={variant}
        className={className}
        style={style}
        {...props}
      >
        {children}
      </div>
    )
  }

  const AlertDescription = ({ children, ...props }: any) => (
    <div data-testid="alert-description" {...props}>
      {children}
    </div>
  )

  return {
    Alert,
    AlertDescription,
  }
}

/**
 * Enhanced Dialog Mock with proper open/close state management
 */
export const createEnhancedDialogMock = () => {
  const Dialog = ({ children, open, onOpenChange }: any) => {
    if (!open) return null
    
    return (
      <div data-testid="dialog" data-open={open}>
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, { onOpenChange })
          }
          return child
        })}
      </div>
    )
  }

  const DialogContent = ({ children, ...props }: any) => (
    <div data-testid="dialog-content" {...props}>
      {children}
    </div>
  )

  const DialogHeader = ({ children, ...props }: any) => (
    <div data-testid="dialog-header" {...props}>
      {children}
    </div>
  )

  const DialogTitle = ({ children, ...props }: any) => (
    <div data-testid="dialog-title" {...props}>
      {children}
    </div>
  )

  const DialogDescription = ({ children, ...props }: any) => (
    <div data-testid="dialog-description" {...props}>
      {children}
    </div>
  )

  const DialogFooter = ({ children, ...props }: any) => (
    <div data-testid="dialog-footer" {...props}>
      {children}
    </div>
  )

  return {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
  }
}

/**
 * Enhanced Button Mock with proper event handling
 */
export const createEnhancedButtonMock = () => {
  const Button = ({
    children,
    onClick,
    disabled,
    variant = 'default',
    size = 'default',
    type = 'button',
    ...props
  }: any) => {
    const handleClick = (e: React.MouseEvent) => {
      if (!disabled && onClick) {
        onClick(e)
      }
    }

    return (
      <button
        data-testid="button"
        data-variant={variant}
        data-size={size}
        type={type}
        disabled={disabled}
        onClick={handleClick}
        {...props}
      >
        {children}
      </button>
    )
  }

  return { Button }
}

/**
 * Enhanced Card Mock components
 */
export const createEnhancedCardMock = () => {
  const Card = ({ children, className, ...props }: any) => (
    <div data-testid="card" className={className} {...props}>
      {children}
    </div>
  )

  const CardHeader = ({ children, className, ...props }: any) => (
    <div data-testid="card-header" className={className} {...props}>
      {children}
    </div>
  )

  const CardTitle = ({ children, className, ...props }: any) => (
    <div data-testid="card-title" className={className} {...props}>
      {children}
    </div>
  )

  const CardContent = ({ children, className, ...props }: any) => (
    <div data-testid="card-content" className={className} {...props}>
      {children}
    </div>
  )

  return {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
  }
}

/**
 * Utility to simulate complex user interactions
 */
export const simulateSelectOption = async (selectElement: HTMLElement, optionValue: string) => {
  // Click to open the select
  fireEvent.click(selectElement)
  
  // Wait for content to appear
  await waitFor(() => {
    const content = document.querySelector('[data-testid="select-content"]')
    expect(content).toBeInTheDocument()
  })

  // Find and click the specific option
  const option = document.querySelector(`[data-testid="select-item"][data-value="${optionValue}"]`)
  if (option) {
    fireEvent.click(option)
  }

  // Wait for the select to close and state to update
  await waitFor(() => {
    expect(selectElement).toHaveAttribute('data-value', optionValue)
  })
}

/**
 * Utility to simulate form completion
 */
export const fillForm = async (formData: Record<string, string>) => {
  for (const [fieldName, value] of Object.entries(formData)) {
    const field = document.querySelector(`[name="${fieldName}"]`) as HTMLInputElement
    if (field) {
      fireEvent.change(field, { target: { value } })
      await waitFor(() => {
        expect(field.value).toBe(value)
      })
    }
  }
}

/**
 * Utility to verify conditional rendering
 */
export const waitForConditionalElement = async (
  testId: string,
  shouldExist: boolean = true,
  timeout: number = 1000
) => {
  if (shouldExist) {
    await waitFor(
      () => {
        const element = document.querySelector(`[data-testid="${testId}"]`)
        expect(element).toBeInTheDocument()
        return element
      },
      { timeout }
    )
  } else {
    await waitFor(
      () => {
        const element = document.querySelector(`[data-testid="${testId}"]`)
        expect(element).not.toBeInTheDocument()
      },
      { timeout }
    )
  }
}

/**
 * Mock factory for complete UI component sets
 */
export const createUIComponentMockSet = () => {
  const selectMocks = createEnhancedSelectMock()
  const alertMocks = createEnhancedAlertMock()
  const dialogMocks = createEnhancedDialogMock()
  const buttonMocks = createEnhancedButtonMock()
  const cardMocks = createEnhancedCardMock()

  return {
    ...selectMocks,
    ...alertMocks,
    ...dialogMocks,
    ...buttonMocks,
    ...cardMocks,
    
    // Additional simple mocks
    Label: ({ children, htmlFor, ...props }: any) => (
      <label data-testid="label" htmlFor={htmlFor} {...props}>
        {children}
      </label>
    ),
    
    Textarea: ({ ...props }: any) => (
      <textarea data-testid="textarea" {...props} />
    ),

    Progress: ({ value, ...props }: any) => (
      <div data-testid="progress" data-value={value} {...props} />
    ),
  }
}

/**
 * Test scenario helpers for permission components
 */
export const permissionTestScenarios = {
  /**
   * Simulate selecting a dangerous operation that should show warnings
   */
  simulateDangerousOperation: async (operationType: 'grant_all' | 'revoke_all') => {
    const selectElements = document.querySelectorAll('[data-testid="select"]')
    const operationSelect = selectElements[0] as HTMLElement
    
    if (operationSelect) {
      await simulateSelectOption(operationSelect, operationType)
      
      // Wait for the alert to appear
      await waitForConditionalElement('alert', true)
      
      return document.querySelector('[data-testid="alert"]')
    }
    
    return null
  },

  /**
   * Simulate completing a bulk permission form
   */
  completeBulkPermissionForm: async (operationType: string, changeReason: string) => {
    // Select operation type
    const selectElements = document.querySelectorAll('[data-testid="select"]')
    if (selectElements.length > 0) {
      await simulateSelectOption(selectElements[0] as HTMLElement, operationType)
    }

    // Fill change reason
    const textarea = document.querySelector('[data-testid="textarea"]') as HTMLTextAreaElement
    if (textarea) {
      fireEvent.change(textarea, { target: { value: changeReason } })
    }

    return {
      operationType,
      changeReason,
      isComplete: true,
    }
  },
}

export default {
  createEnhancedSelectMock,
  createEnhancedAlertMock,
  createEnhancedDialogMock,
  createEnhancedButtonMock,
  createEnhancedCardMock,
  createUIComponentMockSet,
  simulateSelectOption,
  fillForm,
  waitForConditionalElement,
  permissionTestScenarios,
}