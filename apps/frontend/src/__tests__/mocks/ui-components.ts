/**
 * Comprehensive shadcn/ui component mocks for testing
 * 
 * Provides consistent mock implementations for all shadcn/ui components
 * used in the permission system components, ensuring proper test rendering.
 */

import React from 'react'
import { vi } from 'vitest'

// Base mock component factory
const createMockComponent = (displayName: string, additionalProps?: Record<string, any>) => {
  const MockComponent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & any>((props, ref) => {
    const { children, className, asChild, ...restProps } = props
    
    // Handle asChild pattern used by Radix UI
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...restProps,
        className: `${children.props.className || ''} ${className || ''}`.trim(),
        ref,
      })
    }
    
    return React.createElement('div', {
      ref,
      'data-testid': displayName.toLowerCase().replace(/([A-Z])/g, '-$1').substring(1),
      className: className || `mock-${displayName.toLowerCase()}`,
      ...restProps,
      ...additionalProps,
    }, children)
  })
  
  MockComponent.displayName = displayName
  return MockComponent
}

// Dialog components
export const Dialog = createMockComponent('Dialog')
export const DialogContent = createMockComponent('DialogContent', { 'data-testid': 'dialog-content' })
export const DialogHeader = createMockComponent('DialogHeader', { 'data-testid': 'dialog-header' })
export const DialogTitle = createMockComponent('DialogTitle', { 'data-testid': 'dialog-title' })
export const DialogDescription = createMockComponent('DialogDescription', { 'data-testid': 'dialog-description' })
export const DialogFooter = createMockComponent('DialogFooter', { 'data-testid': 'dialog-footer' })

// Dialog trigger needs special handling
export const DialogTrigger = React.forwardRef<HTMLButtonElement, any>((props, ref) => {
  const { children, asChild, ...restProps } = props
  
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      ...restProps,
      ref,
      'data-testid': 'dialog-trigger',
    })
  }
  
  return React.createElement('button', {
    ref,
    'data-testid': 'dialog-trigger',
    ...restProps,
  }, children)
})
DialogTrigger.displayName = 'DialogTrigger'

// Card components
export const Card = createMockComponent('Card', { 'data-testid': 'card' })
export const CardContent = createMockComponent('CardContent', { 'data-testid': 'card-content' })
export const CardHeader = createMockComponent('CardHeader', { 'data-testid': 'card-header' })
export const CardTitle = createMockComponent('CardTitle', { 'data-testid': 'card-title' })
export const CardDescription = createMockComponent('CardDescription', { 'data-testid': 'card-description' })
export const CardFooter = createMockComponent('CardFooter', { 'data-testid': 'card-footer' })

// Button component with variants
export const Button = React.forwardRef<HTMLButtonElement, any>((props, ref) => {
  const { children, variant = 'default', size = 'default', asChild, disabled, ...restProps } = props
  
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      ...restProps,
      ref,
      'data-variant': variant,
      'data-size': size,
      disabled,
    })
  }
  
  return React.createElement('button', {
    ref,
    'data-testid': 'button',
    'data-variant': variant,
    'data-size': size,
    disabled,
    type: props.type || 'button',
    ...restProps,
  }, children)
})
Button.displayName = 'Button'

// Alert components
export const Alert = createMockComponent('Alert', { 'data-testid': 'alert' })
export const AlertDescription = createMockComponent('AlertDescription', { 'data-testid': 'alert-description' })

// Badge component
export const Badge = createMockComponent('Badge', { 'data-testid': 'badge' })

// Input component
export const Input = React.forwardRef<HTMLInputElement, any>((props, ref) => {
  const { type = 'text', ...restProps } = props
  return React.createElement('input', {
    ref,
    'data-testid': 'input',
    type,
    ...restProps,
  })
})
Input.displayName = 'Input'

// Label component
export const Label = createMockComponent('Label', { 'data-testid': 'label' })

// Checkbox component
export const Checkbox = React.forwardRef<HTMLInputElement, any>((props, ref) => {
  const { checked, onCheckedChange, ...restProps } = props
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onCheckedChange) {
      onCheckedChange(e.target.checked)
    }
  }
  
  return React.createElement('input', {
    ref,
    'data-testid': 'checkbox',
    type: 'checkbox',
    checked,
    onChange: handleChange,
    ...restProps,
  })
})
Checkbox.displayName = 'Checkbox'

// Select components
export const Select = ({ children, onValueChange, value, defaultValue, disabled, ...props }: any) => {
  return React.createElement('div', {
    'data-testid': 'select',
    'data-value': value || defaultValue,
    'data-disabled': disabled,
    ...props,
  }, children)
}

export const SelectContent = createMockComponent('SelectContent', { 'data-testid': 'select-content' })
export const SelectItem = ({ children, value, ...props }: any) => {
  return React.createElement('div', {
    'data-testid': 'select-item',
    'data-value': value,
    ...props,
  }, children)
}
export const SelectTrigger = createMockComponent('SelectTrigger', { 'data-testid': 'select-trigger' })
export const SelectValue = ({ placeholder, ...props }: any) => {
  return React.createElement('span', {
    'data-testid': 'select-value',
    'data-placeholder': placeholder,
    ...props,
  }, placeholder)
}

// Table components
export const Table = createMockComponent('Table', { 'data-testid': 'table', role: 'table' })
export const TableHeader = createMockComponent('TableHeader', { 'data-testid': 'table-header', role: 'rowgroup' })
export const TableBody = createMockComponent('TableBody', { 'data-testid': 'table-body', role: 'rowgroup' })
export const TableRow = createMockComponent('TableRow', { 'data-testid': 'table-row', role: 'row' })
export const TableHead = createMockComponent('TableHead', { 'data-testid': 'table-head', role: 'columnheader' })
export const TableCell = createMockComponent('TableCell', { 'data-testid': 'table-cell', role: 'cell' })

// Tabs components
export const Tabs = ({ children, value, onValueChange, defaultValue, ...props }: any) => {
  return React.createElement('div', {
    'data-testid': 'tabs',
    'data-value': value || defaultValue,
    ...props,
  }, children)
}
export const TabsList = createMockComponent('TabsList', { 'data-testid': 'tabs-list' })
export const TabsTrigger = ({ children, value, ...props }: any) => {
  return React.createElement('button', {
    'data-testid': 'tabs-trigger',
    'data-value': value,
    type: 'button',
    ...props,
  }, children)
}
export const TabsContent = ({ children, value, ...props }: any) => {
  return React.createElement('div', {
    'data-testid': 'tabs-content',
    'data-value': value,
    ...props,
  }, children)
}

// Tooltip components (often used in permission interfaces)
export const Tooltip = ({ children }: any) => children
export const TooltipContent = createMockComponent('TooltipContent', { 'data-testid': 'tooltip-content' })
export const TooltipProvider = ({ children }: any) => children
export const TooltipTrigger = ({ children }: any) => children

// Form components
export const Form = createMockComponent('Form', { 'data-testid': 'form' })
export const FormField = ({ children, control, name, render }: any) => {
  const mockFieldProps = {
    field: {
      name,
      value: '',
      onChange: vi.fn(),
      onBlur: vi.fn(),
    },
    fieldState: {
      error: null,
      isDirty: false,
      isTouched: false,
    },
    formState: {
      isSubmitting: false,
      isValid: true,
    },
  }
  
  return render ? render(mockFieldProps) : children
}
export const FormItem = createMockComponent('FormItem', { 'data-testid': 'form-item' })
export const FormLabel = createMockComponent('FormLabel', { 'data-testid': 'form-label' })
export const FormControl = createMockComponent('FormControl', { 'data-testid': 'form-control' })
export const FormMessage = createMockComponent('FormMessage', { 'data-testid': 'form-message' })
export const FormDescription = createMockComponent('FormDescription', { 'data-testid': 'form-description' })

// Pagination components (used in permission lists)
export const Pagination = createMockComponent('Pagination', { 'data-testid': 'pagination' })
export const PaginationContent = createMockComponent('PaginationContent', { 'data-testid': 'pagination-content' })
export const PaginationItem = createMockComponent('PaginationItem', { 'data-testid': 'pagination-item' })
export const PaginationLink = createMockComponent('PaginationLink', { 'data-testid': 'pagination-link' })
export const PaginationNext = createMockComponent('PaginationNext', { 'data-testid': 'pagination-next' })
export const PaginationPrevious = createMockComponent('PaginationPrevious', { 'data-testid': 'pagination-previous' })

// Separator component
export const Separator = createMockComponent('Separator', { 'data-testid': 'separator' })

// Progress component
export const Progress = ({ value, max = 100, ...props }: any) => {
  return React.createElement('div', {
    'data-testid': 'progress',
    'data-value': value,
    'data-max': max,
    role: 'progressbar',
    'aria-valuenow': value,
    'aria-valuemax': max,
    ...props,
  })
}

// Avatar components (for user displays)
export const Avatar = createMockComponent('Avatar', { 'data-testid': 'avatar' })
export const AvatarImage = createMockComponent('AvatarImage', { 'data-testid': 'avatar-image' })
export const AvatarFallback = createMockComponent('AvatarFallback', { 'data-testid': 'avatar-fallback' })

// Switch component (for permission toggles)
export const Switch = React.forwardRef<HTMLInputElement, any>((props, ref) => {
  const { checked, onCheckedChange, disabled, ...restProps } = props
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onCheckedChange && !disabled) {
      onCheckedChange(e.target.checked)
    }
  }
  
  return React.createElement('input', {
    ref,
    'data-testid': 'switch',
    type: 'checkbox',
    role: 'switch',
    checked,
    disabled,
    onChange: handleChange,
    ...restProps,
  })
})
Switch.displayName = 'Switch'

// Popover components (for permission dropdowns)
export const Popover = ({ children }: any) => children
export const PopoverContent = createMockComponent('PopoverContent', { 'data-testid': 'popover-content' })
export const PopoverTrigger = ({ children, asChild }: any) => {
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      'data-testid': 'popover-trigger',
    })
  }
  return React.createElement('div', { 'data-testid': 'popover-trigger' }, children)
}

// Command components (for search functionality)
export const Command = createMockComponent('Command', { 'data-testid': 'command' })
export const CommandInput = React.forwardRef<HTMLInputElement, any>((props, ref) => {
  return React.createElement('input', {
    ref,
    'data-testid': 'command-input',
    role: 'searchbox',
    ...props,
  })
})
CommandInput.displayName = 'CommandInput'
export const CommandList = createMockComponent('CommandList', { 'data-testid': 'command-list' })
export const CommandEmpty = createMockComponent('CommandEmpty', { 'data-testid': 'command-empty' })
export const CommandGroup = createMockComponent('CommandGroup', { 'data-testid': 'command-group' })
export const CommandItem = createMockComponent('CommandItem', { 'data-testid': 'command-item' })

// ScrollArea component
export const ScrollArea = createMockComponent('ScrollArea', { 'data-testid': 'scroll-area' })

// Sheet components (for mobile-friendly dialogs)
export const Sheet = ({ children }: any) => children
export const SheetContent = createMockComponent('SheetContent', { 'data-testid': 'sheet-content' })
export const SheetHeader = createMockComponent('SheetHeader', { 'data-testid': 'sheet-header' })
export const SheetTitle = createMockComponent('SheetTitle', { 'data-testid': 'sheet-title' })
export const SheetDescription = createMockComponent('SheetDescription', { 'data-testid': 'sheet-description' })
export const SheetTrigger = ({ children, asChild }: any) => {
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      'data-testid': 'sheet-trigger',
    })
  }
  return React.createElement('button', { 'data-testid': 'sheet-trigger', type: 'button' }, children)
}

// DropdownMenu components
export const DropdownMenu = ({ children }: any) => children
export const DropdownMenuContent = createMockComponent('DropdownMenuContent', { 'data-testid': 'dropdown-menu-content' })
export const DropdownMenuItem = createMockComponent('DropdownMenuItem', { 'data-testid': 'dropdown-menu-item' })
export const DropdownMenuTrigger = ({ children, asChild }: any) => {
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      'data-testid': 'dropdown-menu-trigger',
    })
  }
  return React.createElement('button', { 'data-testid': 'dropdown-menu-trigger', type: 'button' }, children)
}
export const DropdownMenuSeparator = createMockComponent('DropdownMenuSeparator', { 'data-testid': 'dropdown-menu-separator' })
export const DropdownMenuLabel = createMockComponent('DropdownMenuLabel', { 'data-testid': 'dropdown-menu-label' })

// Skeleton component (for loading states)
export const Skeleton = createMockComponent('Skeleton', { 'data-testid': 'skeleton' })

// Calendar component (for date pickers)
export const Calendar = ({ onSelect, selected, mode = 'single', ...props }: any) => {
  const handleClick = () => {
    if (onSelect && mode === 'single') {
      onSelect(new Date('2024-01-15'))
    }
  }
  
  return React.createElement('div', {
    'data-testid': 'calendar',
    'data-selected': selected ? selected.toISOString() : '',
    'data-mode': mode,
    role: 'dialog',
    onClick: handleClick,
    ...props,
  }, 'Calendar')
}