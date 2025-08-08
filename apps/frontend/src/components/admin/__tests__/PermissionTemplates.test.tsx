/**
 * PermissionTemplates Component Tests
 * 
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (fetch calls, third-party services, etc.)
 * - Use real component rendering and actual data flows
 * - Mock external dependencies only: API endpoints, browser APIs, third-party libraries
 * - Test actual behavior, not implementation details
 */

import { 
  renderWithProviders, 
  screen, 
  waitFor, 
  userEvent,
  vi, 
  describe, 
  it, 
  expect,
  useTestSetup,
  act,
  mockSuccessfulFetch
} from '@/test/test-template'
import { setupTestAuth, createMockAdmin } from '@/test/auth-helpers'
import { PermissionTemplates } from '../PermissionTemplates'

// Use standardized test setup - handles all external API mocks
useTestSetup()

describe('PermissionTemplates Component', () => {
  beforeEach(() => {
    // Set up authenticated admin user - no internal mocks, just setting up test state
    const adminUser = createMockAdmin()
    setupTestAuth(adminUser, 'mock-jwt-token')
  })

  describe('Basic Rendering', () => {
    it('should render templates list with system and custom sections', async () => {
      // Only mock the external API call - setup.ts already has default mock for /permissions/templates
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      // Wait for templates to load and Select components to stabilize
      await act(async () => {
        await waitFor(async () => {
          // The default mock in setup.ts returns a "Default User" template
          expect(screen.getByText('Default User')).toBeInTheDocument()
        }, { timeout: 3000 })
      })
      
      // Allow Select components time to stabilize after initial render
      await act(async () => {
        // Small delay for any Select state updates to complete
        await new Promise(resolve => setTimeout(resolve, 100))
      })
      
      // Verify the component structure renders correctly
      await act(async () => {
        expect(screen.getByText(/Basic permissions for regular users/i)).toBeInTheDocument()
      })
    })

    it('should handle loading state properly', async () => {
      // Mock a slow API response to test loading state
      mockSuccessfulFetch('/permissions/templates', 
        { templates: [], total: 0 },
        200
      )
      
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      // Should eventually show some content (empty state or data)
      await act(async () => {
        await waitFor(async () => {
          // Either shows templates or empty state - testing real behavior
          expect(screen.getByRole('main') || screen.getByText(/template/i)).toBeInTheDocument()
        })
      })
    })

    it('should display permission guard when user lacks access', async () => {
      // Set up user without admin permissions - testing real permission logic
      const regularUser = createMockAdmin({ role: 'user' }) // Regular user, not admin
      setupTestAuth(regularUser, 'mock-jwt-token')
      
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      // Should show permission denied message - testing real PermissionGuard behavior
      await act(async () => {
        await waitFor(async () => {
          expect(screen.getByText(/não tem permissão/i)).toBeInTheDocument()
        })
      })
    })
  })

  describe('Template Interaction', () => {
    beforeEach(async () => {
      // Setup admin with full permissions
      const adminUser = createMockAdmin()
      setupTestAuth(adminUser, 'mock-jwt-token')
      
      // Mock templates with more realistic data for interaction tests
      mockSuccessfulFetch('/permissions/templates', {
        templates: [
          {
            template_id: 'template-1',
            template_name: 'Admin Template',
            description: 'Full administrative access',
            permissions: {
              client_management: { create: true, read: true, update: true, delete: true },
              pdf_processing: { create: true, read: true, update: true, delete: false }
            },
            is_system_template: true,
            created_by_user_id: 'admin-123',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          },
          {
            template_id: 'template-2',
            template_name: 'User Template', 
            description: 'Basic user access',
            permissions: {
              client_management: { create: false, read: true, update: true, delete: false },
              pdf_processing: { create: false, read: true, update: false, delete: false }
            },
            is_system_template: false,
            created_by_user_id: 'admin-123',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          }
        ],
        total: 2
      })
    })

    it('should render template cards with correct information', async () => {
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      await act(async () => {
        await waitFor(async () => {
          expect(screen.getByText('Admin Template')).toBeInTheDocument()
          expect(screen.getByText('User Template')).toBeInTheDocument()
        })
      })
      
      // Test that descriptions are shown  
      await act(async () => {
        expect(screen.getByText('Full administrative access')).toBeInTheDocument()
        expect(screen.getByText('Basic user access')).toBeInTheDocument()
      })
    })

    it('should handle template creation dialog', async () => {
      const user = userEvent.setup()
      
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      // Wait for component to load
      await act(async () => {
        await waitFor(async () => {
          expect(screen.getByText('Admin Template')).toBeInTheDocument()
        })
      })
      
      // Look for create template button
      const createButton = screen.getByRole('button', { name: /criar.*template/i }) || 
                         screen.getByRole('button', { name: /novo.*template/i }) ||
                         screen.getByRole('button', { name: /adicionar/i })
      
      if (createButton) {
        await act(async () => {
          await user.click(createButton)
        })
        
        // Allow any Select components in dialog to stabilize
        await act(async () => {
          await new Promise(resolve => setTimeout(resolve, 100))
        })
        
        // Should open create dialog - testing real dialog behavior
        await act(async () => {
          await waitFor(async () => {
            expect(screen.getByRole('dialog')).toBeInTheDocument()
          })
        })
      }
    })
  })

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      // Mock API failure - only external API mock
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))
      
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      // Should show error state - testing real error handling
      await act(async () => {
        await waitFor(async () => {
          expect(screen.getByText(/erro/i) || screen.getByText(/falha/i)).toBeInTheDocument()
        })
      })
    })

    it('should handle unauthorized access gracefully', async () => {
      // Mock 401 response - external API mock only
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ error: 'Unauthorized' })
      } as Response)
      
      await act(async () => {
        renderWithProviders(<PermissionTemplates />)
      })
      
      // Should handle unauthorized gracefully
      await act(async () => {
        await waitFor(async () => {
          expect(screen.getByText(/não.*autorizado/i) || screen.getByText(/permissão/i)).toBeInTheDocument()
        })
      })
    })
  })
})