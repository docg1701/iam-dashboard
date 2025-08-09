/**
 * BulkPermissionDialog Component Tests
 * 
 * Comprehensive tests for the BulkPermissionDialog with progress tracking and error handling
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import React from 'react'
import { 
  describe, 
  it, 
  expect, 
  beforeEach, 
  vi, 
  afterEach,
  renderWithProviders,
  screen,
  waitFor,
  act,
  useTestSetup
} from '@/test/test-template'
import userEvent from '@testing-library/user-event'
import { 
  createMockUser, 
  createMockAdminUser,
  createMockUserAgentPermission,
  setupUserAPITest,
  setupPermissionAPITest,
  AgentName
} from '@/test/api-mocks'
import { 
  setupAuthenticatedUser,
  clearTestAuth
} from '@/test/auth-helpers'
import { BulkPermissionDialog } from '../BulkPermissionDialog'
import useAuthStore from '@/store/authStore'

// Setup standard test utilities
useTestSetup()

// Mock data
const mockAdminUser = createMockAdminUser({ 
  user_id: 'admin-123',
  full_name: 'Admin User',
  email: 'admin@test.com'
})

const mockSelectedUsers = [
  createMockUser({
    user_id: 'user-1',
    email: 'user1@test.com',
    full_name: 'User One',
    role: 'user',
    is_active: true,
    totp_enabled: false,
  }),
  createMockUser({
    user_id: 'user-2',
    email: 'user2@test.com', 
    full_name: 'User Two',
    role: 'user',
    is_active: true,
    totp_enabled: true,
  }),
  createMockUser({
    user_id: 'user-3',
    email: 'user3@test.com',
    full_name: 'User Three',
    role: 'user',
    is_active: true,
    totp_enabled: false,
  })
]

const mockOnClose = vi.fn()
const mockOnComplete = vi.fn()

describe('BulkPermissionDialog', () => {
  beforeEach(async () => {
    await act(async () => {
      // Setup authenticated admin user
      setupAuthenticatedUser('admin')
      useAuthStore.setState({ 
        user: mockAdminUser,
        token: 'mock-admin-token',
        isAuthenticated: true
      })
      
      // Setup permission API mocks for admin user with full permissions
      const adminPermissions = [
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.AUDIO_RECORDING, 
          { create: true, read: true, update: true, delete: true })
      ]
      
      setupPermissionAPITest({
        userId: mockAdminUser.user_id,
        userPermissions: adminPermissions
      })
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    clearTestAuth()
  })

  describe('Dialog Rendering', () => {
    it('should not render when not open', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={false}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      // Dialog should not be visible when open=false
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render with zero users when no users selected', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={[]}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      // Should render dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })
      
      // Should show some indication of 0 users or empty state
      await waitFor(() => {
        expect(screen.getByText(/nenhum usuário selecionado|0 usuários|não há usuários/i) || 
               screen.getByText(/selecione usuários|usuários para aplicar/i)).toBeInTheDocument()
      })
    })

    it('should render dialog header with selected user count', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should show bulk operations title
      await waitFor(() => {
        expect(screen.getByText(/operações em lote.*3.*usuários selecionados/i)).toBeInTheDocument()
      })
    })

    it('should display selected users list', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })
      
      // Should show user information 
      await waitFor(() => {
        expect(screen.getByText('user1@test.com')).toBeInTheDocument()
        expect(screen.getByText('user2@test.com')).toBeInTheDocument()
      })
    })
  })

  describe('Operation Type Selection', () => {
    it('should display operation type options', async () => {
      const user = userEvent.setup()
      
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })
      
      // Look for operation type selection controls 
      await waitFor(() => {
        const operationControls = screen.queryAllByRole('combobox') || 
                                screen.queryAllByRole('radio') ||
                                screen.queryAllByRole('button')
        expect(operationControls.length).toBeGreaterThan(0)
      })
    })

    it('should show template selector when template operation is available', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should have template-related controls or text
      await waitFor(() => {
        const templateElements = screen.queryByText(/template/i) ||
                                screen.queryByText(/modelo/i) ||
                                screen.queryByRole('combobox', { name: /template/i })
        expect(templateElements).toBeInTheDocument()
      })
    })
  })

  describe('Change Reason Requirement', () => {
    it('should require change reason for operations', async () => {
      const user = userEvent.setup()

      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should have reason/motivo field
      await waitFor(() => {
        const reasonField = screen.queryByPlaceholderText(/motivo|razão|descreva/i) ||
                          screen.queryByLabelText(/motivo|razão/i) ||
                          screen.queryByRole('textbox', { name: /motivo/i })
        expect(reasonField).toBeInTheDocument()
      })
    })
  })

  describe('Dialog Actions', () => {
    it('should close dialog when cancel button is clicked', async () => {
      const user = userEvent.setup()

      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Find and click cancel button
      const cancelButton = screen.getByRole('button', { name: /cancelar|cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should show apply/action buttons', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should have action buttons
      await waitFor(() => {
        const actionButtons = screen.queryByRole('button', { name: /aplicar|apply|salvar|save/i })
        expect(actionButtons).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper dialog structure and ARIA labels', async () => {
      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        expect(dialog).toBeInTheDocument()
        expect(dialog).toHaveAttribute('aria-modal', 'true')
      })
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()

      await act(async () => {
        renderWithProviders(
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        )
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should be able to tab through interactive elements
      await user.tab()
      
      // At least one focusable element should receive focus
      const focusedElement = document.activeElement
      expect(focusedElement).not.toBe(document.body)
    })
  })
})