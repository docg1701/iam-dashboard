# Test Infrastructure Documentation

This document provides comprehensive guidance for testing permission system components with proper mock infrastructure and realistic component behavior simulation.

## 🏗️ Test Infrastructure Overview

### Global Test Setup (`/src/test/setup.ts`)
- **Global mocks**: Core APIs, auth store, navigation, React Hook Form, TanStack Query
- **Browser environment**: jsdom with proper DOM APIs
- **Accessibility setup**: ResizeObserver, scrollIntoView, pointer events
- **Console suppression**: Reduces test noise

### Mock System (`/src/__tests__/mocks/`)
- **API Mocks** (`api.ts`): Complete permission API simulation
- **UI Components** (`ui-components.ts`): Basic shadcn/ui component mocks
- **TanStack Query** (`tanstack-query.ts`): Query/mutation state mocks
- **Test Providers** (`test-providers.tsx`): Provider wrapper for components

### Test Utilities (`/src/__tests__/utils/`)
- **Basic utilities** (`test-utils.ts`): Common test functions and data factories
- **Component utilities** (`component-test-utils.ts`): Advanced component interaction simulation

## 🧪 Testing Permission Components

### 1. Basic Component Testing

```typescript
import { renderWithProviders, screen } from '@/__tests__/utils/test-utils'
import { BulkPermissionDialog } from '@/components/admin/BulkPermissionDialog'

test('should render permission dialog', () => {
  renderWithProviders(
    <BulkPermissionDialog 
      users={mockUsers} 
      open={true} 
      onOpenChange={vi.fn()} 
    />
  )

  expect(screen.getByTestId('dialog')).toBeInTheDocument()
})
```

### 2. Advanced Component State Testing

For components with complex state logic (like conditional alerts), use the enhanced component utilities:

```typescript
import { createUIComponentMockSet, permissionTestScenarios } from '@/__tests__/utils/component-test-utils'

// Mock UI components with enhanced behavior
vi.mock('@/components/ui/select', () => createUIComponentMockSet())
vi.mock('@/components/ui/alert', () => createUIComponentMockSet())

test('should show warning for dangerous operations', async () => {
  render(<BulkPermissionDialog users={users} open={true} onOpenChange={vi.fn()} />)
  
  // Simulate selecting a dangerous operation
  const alertElement = await permissionTestScenarios.simulateDangerousOperation('grant_all')
  
  expect(alertElement).toBeInTheDocument()
  expect(screen.getByText('Atenção:')).toBeInTheDocument()
})
```

### 3. Form Interaction Testing

```typescript
import { fillForm, simulateSelectOption } from '@/__tests__/utils/component-test-utils'

test('should handle form completion', async () => {
  render(<PermissionForm />)
  
  // Fill form fields
  await fillForm({
    changeReason: 'Updated permissions for new policy',
    templateId: 'template-1',
  })
  
  // Select specific options
  const select = screen.getByTestId('select')
  await simulateSelectOption(select, 'grant_all')
  
  // Verify form state
  expect(screen.getByDisplayValue('Updated permissions for new policy')).toBeInTheDocument()
})
```

## 🔧 Mock Configuration Strategies

### Strategy 1: Individual Test Mocks (Recommended for complex components)

When testing components with specific behavior requirements, create local mocks in the test file:

```typescript
// In your test file
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: { children: React.ReactNode; open: boolean }) => {
    if (!open) return null
    return <div data-testid="dialog">{children}</div>
  },
  // ... other dialog components
}))
```

**Pros**: Full control over mock behavior, can simulate exact component logic
**Cons**: More setup per test file

### Strategy 2: Enhanced Global Mocks (Use our component utilities)

Import enhanced mocks that provide realistic component behavior:

```typescript
import { createUIComponentMockSet } from '@/__tests__/utils/component-test-utils'

vi.mock('@/components/ui/select', () => createUIComponentMockSet())
```

**Pros**: Realistic behavior simulation, less setup, consistent across tests
**Cons**: May be too complex for simple tests

### Strategy 3: Hybrid Approach (Current implementation)

- Global mocks for APIs, hooks, and basic infrastructure
- Individual test mocks for UI components with specific behavior needs
- Enhanced utilities available for complex interaction testing

## 📊 Mock Data Factories

### User Data
```typescript
import { createMockUser, createMockUsers } from '@/__tests__/utils/test-utils'

const user = createMockUser({ role: 'admin', is_active: true })
const users = createMockUsers(5) // Creates 5 mock users
```

### Permission Data
```typescript
import { createMockUserPermissionMatrix, createMockPermissionTemplate } from '@/__tests__/utils/test-utils'

const permissions = createMockUserPermissionMatrix('user-id', {
  permissions: {
    client_management: { create: true, read: true, update: false, delete: false }
  }
})

const template = createMockPermissionTemplate('template-id', {
  template_name: 'Custom Admin Template'
})
```

## 🚀 Best Practices

### 1. Test Structure
```typescript
describe('ComponentName', () => {
  beforeEach(() => {
    // Setup specific to all tests in this suite
  })

  describe('Rendering', () => {
    it('should render with required props', () => {
      // Basic rendering tests
    })
  })

  describe('User Interactions', () => {
    it('should handle form submission', async () => {
      // Interaction tests with user events
    })
  })

  describe('State Management', () => {
    it('should update state correctly', async () => {
      // State change tests
    })
  })
})
```

### 2. Async Testing
```typescript
test('should handle async operations', async () => {
  const user = userEvent.setup()
  
  render(<Component />)
  
  await user.click(screen.getByRole('button'))
  
  await waitFor(() => {
    expect(screen.getByTestId('success-message')).toBeInTheDocument()
  })
})
```

### 3. Error State Testing
```typescript
test('should display error states', async () => {
  // Mock failed API call
  vi.mocked(mockAPI.createUser).mockRejectedValueOnce(new Error('API Error'))
  
  render(<UserForm />)
  
  await user.click(screen.getByRole('button', { name: /submit/i }))
  
  await waitFor(() => {
    expect(screen.getByText('API Error')).toBeInTheDocument()
  })
})
```

### 4. Accessibility Testing
```typescript
test('should be accessible', () => {
  render(<Component />)
  
  expect(screen.getByRole('dialog')).toBeInTheDocument()
  expect(screen.getByLabelText('Permission Level')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument()
})
```

## 🐛 Common Issues & Solutions

### Issue: Components not rendering properly
**Solution**: Check if UI components are mocked correctly. Use individual test mocks for complex components.

### Issue: State changes not triggering UI updates
**Solution**: Use enhanced component utilities that properly simulate user interactions and state changes.

### Issue: Async operations timing out
**Solution**: Increase timeout in `waitFor()` or ensure proper async/await usage.

### Issue: Mock conflicts between global and local
**Solution**: Use `vi.clearAllMocks()` in `beforeEach()` or be selective about which mocks to apply globally.

## 📝 Testing Checklist

For each permission component, ensure you test:

- [ ] **Basic Rendering**: Component renders with required props
- [ ] **Props Handling**: All props are properly handled and displayed
- [ ] **User Interactions**: Clicks, form inputs, keyboard navigation
- [ ] **State Changes**: Internal state updates correctly
- [ ] **Conditional Rendering**: Elements show/hide based on conditions
- [ ] **Error States**: Proper error handling and display
- [ ] **Loading States**: Loading indicators appear when needed
- [ ] **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- [ ] **Performance**: Large data sets render efficiently
- [ ] **Edge Cases**: Empty states, invalid data, network errors

## 🔄 Continuous Improvement

This test infrastructure is designed to be:

- **Maintainable**: Clear separation between mock types and test utilities
- **Scalable**: Easy to add new mock patterns and utilities
- **Reliable**: Consistent behavior across different test scenarios
- **Developer-friendly**: Good documentation and clear patterns

When you encounter testing challenges not covered here, consider:

1. Adding new utilities to `/src/__tests__/utils/`
2. Creating new mock patterns in `/src/__tests__/mocks/`
3. Updating this documentation with new patterns
4. Sharing solutions with the team

---

*This infrastructure was created as part of Story 1.7 to support comprehensive testing of the permission system components.*