# Frontend Architecture

**Frontend-specific architecture details based on Next.js 15 + React 19 + shadcn/ui with comprehensive custom branding support and integrated UX system**

> ๐ **Quick Navigation**: [Permission Hooks](./permission-integration-guide.md#frontend-permission-patterns) | [Developer Reference](./developer-reference.md#frontend-patterns) | [Permission Guards](./permission-quick-reference.md#frontend-implementation) | [UX Specification](./ux-specification.md) | [UI Design System](./ui-design-system.md) | [Responsive Design](./responsive-design.md)

---

## Table of Contents

1. [Component Architecture](#component-architecture)
2. [UX Integration Architecture](#ux-integration-architecture)
3. [Permission-Aware UI Patterns](#permission-aware-ui-patterns)
4. [Component Integration with UX Patterns](#component-integration-with-ux-patterns)
5. [State Management for UX](#state-management-for-ux)
6. [Responsive Design Architecture](#responsive-design-architecture)
7. [State Management Architecture](#state-management-architecture)
8. [Routing Architecture](#routing-architecture)
9. [Frontend Services Layer](#frontend-services-layer)
10. [Permission System Frontend Architecture](#permission-system-frontend-architecture)
11. [Cross-References to UX Architecture](#cross-references-to-ux-architecture)
12. [Real-time Updates Architecture](#real-time-updates-architecture)

---

### Component Architecture

**Component Organization:**
```
apps/frontend/src/
├── app/                          # Next.js 15 App Router
│   ├── (auth)/                   # Route group for authentication
│   ├── (dashboard)/              # Protected dashboard routes
│   │   ├── clients/              # Client management pages
│   │   ├── users/                # User management pages
│   │   └── admin/                # Admin pages (permissions, system config)
│   │       ├── permissions/      # Permission management interface
│   │       └── system/           # System configuration
│   ├── globals.css               # Global styles + CSS variables
│   ├── layout.tsx                # Root layout with providers
│   └── page.tsx                  # Public homepage
├── components/                   # Reusable UI components
│   ├── ui/                       # shadcn/ui base components
│   ├── forms/                    # Complex form components
│   ├── layout/                   # Layout components
│   ├── common/                   # Common components
│   │   ├── PermissionGuard.tsx   # Permission-based conditional rendering
│   │   └── ProtectedRoute.tsx    # Route-level permission protection
│   ├── admin/                    # Admin-specific components
│   │   ├── PermissionMatrix.tsx  # User-agent permission matrix
│   │   ├── UserPermissionsDialog.tsx # Individual user permission management
│   │   ├── BulkPermissionDialog.tsx  # Bulk permission operations
│   │   └── PermissionTemplates.tsx   # Permission template management
│   └── features/                 # Feature-specific components
├── lib/                          # Utilities and configurations
│   ├── api/                      # API client functions
│   │   ├── permissions.ts        # Permission API endpoints
│   │   ├── clients.ts            # Client API endpoints
│   │   └── users.ts              # User API endpoints
│   └── utils.ts                  # Utility functions
├── hooks/                        # Custom React hooks
│   ├── useUserPermissions.ts     # Permission management hook
│   ├── usePermissionUpdates.ts   # Real-time permission updates
│   └── use-toast.ts              # Toast notifications
├── store/                        # Client state management
│   ├── authStore.ts              # Authentication state
│   └── permissionStore.ts        # Permission state cache
└── types/                        # TypeScript type definitions
    ├── auth.ts                   # Authentication types
    ├── permissions.ts            # Permission system types
    └── index.ts                  # Shared types
```

### UX Integration Architecture

**How Frontend Architecture Supports User Experience:**

The frontend architecture is designed to seamlessly integrate with UX specifications and provide a cohesive user experience across all agents and user roles. Our technical components are built to support the complete user journey from authentication to task completion.

**UX-Technical Integration Pillars:**

1. **Accessibility-First Architecture**
   ```typescript
   // All components include ARIA attributes and semantic HTML
   export const DataTable: React.FC<DataTableProps> = ({ data, columns }) => {
     return (
       <div role="region" aria-label="Data table">
         <table role="table" aria-describedby="table-description">
           <caption id="table-description" className="sr-only">
             Client data with sorting and filtering capabilities
           </caption>
           {/* Table implementation with full keyboard navigation */}
         </table>
       </div>
     )
   }
   ```

2. **Progressive Enhancement**
   ```typescript
   // Components work without JavaScript, enhanced with interactivity
   export const FormWithProgressiveEnhancement = () => {
     const [isEnhanced, setIsEnhanced] = useState(false)
     
     useEffect(() => {
       // Enable enhanced features only after hydration
       setIsEnhanced(true)
     }, [])
     
     return (
       <form method="post" action="/api/submit">
         {/* Basic HTML form functionality */}
         <input type="text" name="clientName" required />
         
         {isEnhanced && (
           // Enhanced features: real-time validation, autocomplete
           <ClientNameValidator />
         )}
       </form>
     )
   }
   ```

3. **Performance-Optimized UX**
   ```typescript
   // Lazy loading with loading states for better perceived performance
   const LazyAgentComponent = lazy(() => 
     import('./AgentSpecificComponent').then(module => ({
       default: module.AgentSpecificComponent
     }))
   )
   
   export const AgentPage = () => {
     return (
       <Suspense fallback={<AgentLoadingSkeleton />}>
         <LazyAgentComponent />
       </Suspense>
     )
   }
   ```

**UX State Management Integration:**

```typescript
// UX-focused state management for optimal user experience
interface UXState {
  // User preferences and customization
  userPreferences: {
    theme: 'light' | 'dark' | 'system'
    density: 'compact' | 'comfortable' | 'spacious'
    language: 'pt-BR' | 'en'
    dashboardLayout: DashboardLayout
  }
  
  // Application state for UX flows
  currentWorkflow: WorkflowState | null
  userGuidance: {
    showOnboarding: boolean
    completedSteps: string[]
    availableHelp: HelpContent[]
  }
  
  // Performance and feedback
  loadingStates: Record<string, boolean>
  errorStates: Record<string, ErrorState>
  successFeedback: SuccessMessage[]
  
  // Accessibility features
  accessibility: {
    highContrast: boolean
    reducedMotion: boolean
    screenReaderOptimizations: boolean
    keyboardNavigationMode: boolean
  }
}
```

### Permission-Aware UI Patterns

**Technical Implementation of Permission-Based User Experience:**

Our permission system is designed to provide intuitive and predictable user experiences while maintaining security. The UI adapts dynamically to user permissions without disrupting workflow continuity.

**Permission-Based Component Patterns:**

```typescript
// Progressive Disclosure Pattern
export const PermissionAwareActions: React.FC<{ 
  entity: any, 
  entityType: string 
}> = ({ entity, entityType }) => {
  const { hasAgentPermission } = useUserPermissions()
  
  const actions = [
    {
      key: 'view',
      label: 'Visualizar',
      icon: EyeIcon,
      permission: 'read',
      priority: 'high'
    },
    {
      key: 'edit',
      label: 'Editar',
      icon: PencilIcon,
      permission: 'update',
      priority: 'medium'
    },
    {
      key: 'delete',
      label: 'Excluir',
      icon: TrashIcon,
      permission: 'delete',
      priority: 'low',
      requiresConfirmation: true
    }
  ]
  
  const availableActions = actions.filter(action => 
    hasAgentPermission(entityType, action.permission)
  )
  
  return (
    <ActionDropdown 
      actions={availableActions}
      entity={entity}
      onAction={handleAction}
    />
  )
}

// Graceful Degradation Pattern
export const PermissionAwareForm: React.FC<FormProps> = ({ initialData }) => {
  const { hasAgentPermission } = useUserPermissions()
  const canEdit = hasAgentPermission('client_management', 'update')
  
  return (
    <Form initialData={initialData}>
      {canEdit ? (
        // Full editing interface
        <EditableFormFields />
      ) : (
        // Read-only view with clear indication
        <ReadOnlyFormFields>
          <PermissionMessage type="insufficient">
            Você não tem permissão para editar estes dados.
            <ContactAdminLink />
          </PermissionMessage>
        </ReadOnlyFormFields>
      )}
    </Form>
  )
}

// Contextual Permission Feedback
export const PermissionAwareNavigation: React.FC = () => {
  const { hasAgentPermission, isLoading } = useUserPermissions()
  
  if (isLoading) {
    return <NavigationSkeleton />
  }
  
  return (
    <Navigation>
      {navigationItems.map(item => {
        const hasAccess = hasAgentPermission(item.agent, 'read')
        
        return (
          <NavigationItem
            key={item.key}
            {...item}
            disabled={!hasAccess}
            tooltip={!hasAccess ? 'Acesso restrito - contate o administrador' : undefined}
            visual={hasAccess ? 'default' : 'muted'}
          />
        )
      })}
    </Navigation>
  )
}
```

**Permission UX Patterns:**

1. **Progressive Disclosure**: Show available actions based on permissions
2. **Graceful Degradation**: Convert editing interfaces to read-only views
3. **Contextual Feedback**: Clear messaging about permission restrictions
4. **Predictable Behavior**: Consistent permission handling across components
5. **Administrative Transparency**: Clear paths to request additional permissions

### Component Integration with UX Patterns

**Technical Components Supporting User Experience Flows:**

```typescript
// Workflow State Management Component
export const WorkflowProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowState | null>(null)
  const [workflowHistory, setWorkflowHistory] = useState<WorkflowStep[]>([])
  
  const startWorkflow = useCallback((workflowType: WorkflowType, initialData?: any) => {
    const workflow: WorkflowState = {
      id: generateId(),
      type: workflowType,
      status: 'in_progress',
      currentStep: 0,
      steps: getWorkflowSteps(workflowType),
      data: initialData || {},
      startedAt: new Date()
    }
    
    setCurrentWorkflow(workflow)
    setWorkflowHistory(prev => [...prev, workflow.steps[0]])
  }, [])
  
  const advanceWorkflow = useCallback((stepData?: any) => {
    if (!currentWorkflow) return
    
    const nextStep = currentWorkflow.currentStep + 1
    const isComplete = nextStep >= currentWorkflow.steps.length
    
    const updatedWorkflow = {
      ...currentWorkflow,
      currentStep: nextStep,
      status: isComplete ? 'completed' : 'in_progress',
      data: { ...currentWorkflow.data, ...stepData }
    }
    
    setCurrentWorkflow(isComplete ? null : updatedWorkflow)
    
    if (!isComplete) {
      setWorkflowHistory(prev => [...prev, updatedWorkflow.steps[nextStep]])
    }
  }, [currentWorkflow])
  
  return (
    <WorkflowContext.Provider value={{
      currentWorkflow,
      workflowHistory,
      startWorkflow,
      advanceWorkflow
    }}>
      {children}
    </WorkflowContext.Provider>
  )
}

// User Guidance Integration
export const GuidedExperience: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth()
  const [showGuidance, setShowGuidance] = useState(false)
  const [currentTip, setCurrentTip] = useState<GuidanceTip | null>(null)
  
  useEffect(() => {
    // Show guidance for new users or when accessing new features
    const shouldShowGuidance = user?.isFirstLogin || hasNewFeatures()
    setShowGuidance(shouldShowGuidance)
  }, [user])
  
  return (
    <>
      {children}
      {showGuidance && (
        <GuidanceOverlay
          currentTip={currentTip}
          onDismiss={() => setShowGuidance(false)}
          onNext={setCurrentTip}
        />
      )}
    </>
  )
}

// Accessibility Integration Component
export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [a11yPreferences, setA11yPreferences] = useState<AccessibilityPreferences>({
    highContrast: false,
    reducedMotion: false,
    screenReaderOptimizations: false,
    keyboardNavigationMode: false
  })
  
  useEffect(() => {
    // Auto-detect user preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches
    
    setA11yPreferences(prev => ({
      ...prev,
      reducedMotion: prefersReducedMotion,
      highContrast: prefersHighContrast
    }))
  }, [])
  
  return (
    <AccessibilityContext.Provider value={{
      preferences: a11yPreferences,
      updatePreferences: setA11yPreferences
    }}>
      <div 
        className={clsx(
          'app-root',
          a11yPreferences.highContrast && 'high-contrast',
          a11yPreferences.reducedMotion && 'reduced-motion'
        )}
      >
        {children}
      </div>
    </AccessibilityContext.Provider>
  )
}
```

**Component-UX Integration Patterns:**
- **State-Driven UI**: Components automatically adapt to application state
- **Context-Aware Rendering**: Components understand their place in user workflows
- **Accessibility-First**: All components built with accessibility as foundation
- **Performance-Conscious**: UX patterns optimize for perceived performance
- **Feedback-Rich**: Components provide clear feedback for all user interactions

### State Management for UX

**Application State Supporting User Experience Flows:**

```typescript
// UX-Optimized State Architecture
interface ApplicationState {
  // Core application data
  entities: {
    clients: ClientStore
    users: UserStore
    documents: DocumentStore
    recordings: RecordingStore
  }
  
  // UX-specific state
  userExperience: {
    currentAgent: AgentType | null
    activeWorkflows: WorkflowState[]
    recentActions: UserAction[]
    savedFilters: SavedFilter[]
    dashboardCustomization: DashboardConfig
  }
  
  // Performance and feedback state
  ui: {
    loading: LoadingState
    errors: ErrorState
    notifications: NotificationState
    modals: ModalState
    tours: TourState
  }
  
  // Real-time updates
  realtime: {
    connectionStatus: ConnectionStatus
    pendingUpdates: PendingUpdate[]
    optimisticUpdates: OptimisticUpdate[]
  }
}

// UX Flow State Management
export const useUserExperienceFlow = () => {
  const [experienceState, setExperienceState] = useState<UXFlowState>({
    currentFlow: null,
    completedFlows: [],
    availableActions: [],
    contextualHelp: null
  })
  
  const startFlow = useCallback((flowType: UXFlowType, context?: any) => {
    const flow: UXFlow = {
      id: generateId(),
      type: flowType,
      startedAt: new Date(),
      context,
      steps: getFlowSteps(flowType, context),
      currentStepIndex: 0
    }
    
    setExperienceState(prev => ({
      ...prev,
      currentFlow: flow,
      availableActions: flow.steps[0].actions
    }))
  }, [])
  
  const completeFlowStep = useCallback((stepData: any) => {
    setExperienceState(prev => {
      if (!prev.currentFlow) return prev
      
      const nextStepIndex = prev.currentFlow.currentStepIndex + 1
      const isFlowComplete = nextStepIndex >= prev.currentFlow.steps.length
      
      if (isFlowComplete) {
        return {
          ...prev,
          currentFlow: null,
          completedFlows: [...prev.completedFlows, prev.currentFlow],
          availableActions: []
        }
      }
      
      const updatedFlow = {
        ...prev.currentFlow,
        currentStepIndex: nextStepIndex
      }
      
      return {
        ...prev,
        currentFlow: updatedFlow,
        availableActions: updatedFlow.steps[nextStepIndex].actions
      }
    })
  }, [])
  
  return {
    experienceState,
    startFlow,
    completeFlowStep
  }
}

// Performance-Optimized State Updates
export const useOptimisticUpdates = () => {
  const [optimisticState, setOptimisticState] = useState<OptimisticState>({
    pendingOperations: new Map(),
    appliedUpdates: new Map()
  })
  
  const applyOptimisticUpdate = useCallback((
    operationId: string,
    updateFn: (currentState: any) => any,
    rollbackFn: (currentState: any) => any
  ) => {
    // Apply update immediately for better UX
    setOptimisticState(prev => {
      const newState = new Map(prev.appliedUpdates)
      newState.set(operationId, { updateFn, rollbackFn, appliedAt: Date.now() })
      
      return {
        ...prev,
        appliedUpdates: newState
      }
    })
    
    // Track pending operation
    setOptimisticState(prev => {
      const newPending = new Map(prev.pendingOperations)
      newPending.set(operationId, { status: 'pending', startedAt: Date.now() })
      
      return {
        ...prev,
        pendingOperations: newPending
      }
    })
  }, [])
  
  const confirmOptimisticUpdate = useCallback((operationId: string) => {
    setOptimisticState(prev => {
      const newPending = new Map(prev.pendingOperations)
      const newApplied = new Map(prev.appliedUpdates)
      
      newPending.delete(operationId)
      newApplied.delete(operationId)
      
      return {
        ...prev,
        pendingOperations: newPending,
        appliedUpdates: newApplied
      }
    })
  }, [])
  
  return {
    optimisticState,
    applyOptimisticUpdate,
    confirmOptimisticUpdate
  }
}
```

**State-UX Integration Benefits:**
- **Immediate Feedback**: Optimistic updates provide instant user feedback
- **Context Preservation**: State maintains user context across navigation
- **Progressive Enhancement**: State enables enhanced features while maintaining basic functionality
- **Personalization**: User preferences and customizations persist across sessions
- **Error Recovery**: Comprehensive error states with recovery mechanisms

### Responsive Design Architecture

**Mobile-First Technical Implementation:**

Our responsive design architecture ensures optimal user experience across all device types, from mobile phones to desktop computers. The technical implementation follows a mobile-first approach with progressive enhancement.

**Responsive Breakpoint System:**

```typescript
// Tailwind CSS configuration for responsive breakpoints
const tailwindConfig = {
  theme: {
    screens: {
      'xs': '475px',    // Large phones
      'sm': '640px',    // Small tablets
      'md': '768px',    // Medium tablets
      'lg': '1024px',   // Small desktops
      'xl': '1280px',   // Large desktops
      '2xl': '1536px'   // Ultra-wide displays
    },
    extend: {
      // Custom breakpoints for specific use cases
      screens: {
        'mobile-only': { 'max': '639px' },
        'tablet-only': { 'min': '640px', 'max': '1023px' },
        'desktop-only': { 'min': '1024px' }
      }
    }
  }
}

// Responsive hook for conditional rendering
export const useResponsive = () => {
  const [screenSize, setScreenSize] = useState<ScreenSize>('mobile')
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      if (width < 640) setScreenSize('mobile')
      else if (width < 1024) setScreenSize('tablet')
      else setScreenSize('desktop')
    }
    
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  return {
    screenSize,
    isMobile: screenSize === 'mobile',
    isTablet: screenSize === 'tablet',
    isDesktop: screenSize === 'desktop'
  }
}
```

**Adaptive Component Architecture:**

```typescript
// Responsive navigation component
export const AdaptiveNavigation: React.FC = () => {
  const { isMobile, isTablet } = useResponsive()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  
  if (isMobile) {
    return (
      <MobileNavigation
        isOpen={isMobileMenuOpen}
        onToggle={setIsMobileMenuOpen}
      />
    )
  }
  
  if (isTablet) {
    return <TabletNavigation />
  }
  
  return <DesktopNavigation />
}

// Responsive data table with different layouts per screen size
export const ResponsiveDataTable: React.FC<TableProps> = ({ data, columns }) => {
  const { isMobile, isTablet } = useResponsive()
  
  if (isMobile) {
    // Card layout for mobile
    return (
      <div className="space-y-4">
        {data.map(item => (
          <DataCard key={item.id} data={item} />
        ))}
      </div>
    )
  }
  
  if (isTablet) {
    // Horizontal scroll table for tablets
    return (
      <div className="overflow-x-auto">
        <Table data={data} columns={columns} />
      </div>
    )
  }
  
  // Full table for desktop
  return <Table data={data} columns={columns} />
}

// Responsive form layouts
export const AdaptiveForm: React.FC<FormProps> = ({ fields, onSubmit }) => {
  const { isMobile } = useResponsive()
  
  return (
    <form onSubmit={onSubmit} className={clsx(
      'space-y-6',
      isMobile ? 'px-4' : 'max-w-2xl mx-auto'
    )}>
      <div className={clsx(
        'grid gap-6',
        isMobile ? 'grid-cols-1' : 'grid-cols-2'
      )}>
        {fields.map(field => (
          <FormField
            key={field.name}
            {...field}
            className={clsx(
              field.fullWidth && 'col-span-full',
              isMobile && 'col-span-1'
            )}
          />
        ))}
      </div>
    </form>
  )
}
```

**Touch-Friendly Interface Patterns:**

```typescript
// Touch-optimized action buttons
export const TouchFriendlyActions: React.FC<ActionsProps> = ({ actions }) => {
  const { isMobile } = useResponsive()
  
  if (isMobile) {
    return (
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t">
        <div className="flex space-x-3">
          {actions.map(action => (
            <Button
              key={action.key}
              {...action}
              size="lg" // Larger touch targets
              className="flex-1 min-h-[48px]" // WCAG minimum touch target
            />
          ))}
        </div>
      </div>
    )
  }
  
  return (
    <div className="flex space-x-2">
      {actions.map(action => (
        <Button key={action.key} {...action} />
      ))}
    </div>
  )
}

// Swipe gesture support for mobile
export const SwipeableCard: React.FC<CardProps> = ({ children, onSwipeLeft, onSwipeRight }) => {
  const [swipeStartX, setSwipeStartX] = useState<number | null>(null)
  const { isMobile } = useResponsive()
  
  const handleTouchStart = (e: TouchEvent) => {
    setSwipeStartX(e.touches[0].clientX)
  }
  
  const handleTouchEnd = (e: TouchEvent) => {
    if (!swipeStartX || !isMobile) return
    
    const swipeEndX = e.changedTouches[0].clientX
    const swipeDistance = swipeStartX - swipeEndX
    const minSwipeDistance = 100
    
    if (swipeDistance > minSwipeDistance) {
      onSwipeLeft?.()
    } else if (swipeDistance < -minSwipeDistance) {
      onSwipeRight?.()
    }
    
    setSwipeStartX(null)
  }
  
  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      className="relative"
    >
      {children}
    </div>
  )
}
```

**Progressive Enhancement for Mobile:**

```typescript
// Progressive enhancement component
export const ProgressivelyEnhanced: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isEnhanced, setIsEnhanced] = useState(false)
  const { isMobile } = useResponsive()
  
  useEffect(() => {
    // Enable enhanced features after component mount
    const timer = setTimeout(() => setIsEnhanced(true), 100)
    return () => clearTimeout(timer)
  }, [])
  
  return (
    <div className={clsx(
      'transition-all duration-300',
      isEnhanced && 'enhanced'
    )}>
      {children}
      
      {isEnhanced && isMobile && (
        // Enhanced mobile features
        <MobileEnhancements />
      )}
    </div>
  )
}

// Adaptive loading strategies
export const AdaptiveImage: React.FC<ImageProps> = ({ src, alt, ...props }) => {
  const { isMobile } = useResponsive()
  
  return (
    <Image
      src={src}
      alt={alt}
      {...props}
      // Smaller images for mobile to save bandwidth
      width={isMobile ? props.width / 2 : props.width}
      height={isMobile ? props.height / 2 : props.height}
      // Lazy loading with intersection observer
      loading="lazy"
      // Responsive image optimization
      sizes={isMobile ? 
        '(max-width: 640px) 100vw' :
        '(max-width: 1024px) 50vw, 33vw'
      }
    />
  )
}
```

**Performance Optimization for Mobile:**

```typescript
// Mobile-optimized data loading
export const useMobileOptimizedQuery = <T>(
  queryKey: string[],
  queryFn: () => Promise<T>,
  options?: QueryOptions
) => {
  const { isMobile } = useResponsive()
  
  return useQuery({
    queryKey,
    queryFn,
    ...options,
    // Reduce stale time on mobile to ensure fresh data
    staleTime: isMobile ? 2 * 60 * 1000 : 5 * 60 * 1000,
    // Shorter cache time on mobile due to memory constraints
    cacheTime: isMobile ? 5 * 60 * 1000 : 30 * 60 * 1000,
    // Enable background refetch on mobile when app becomes active
    refetchOnWindowFocus: isMobile
  })
}

// Viewport-based rendering for performance
export const ViewportAwareRenderer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isInViewport, setIsInViewport] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setIsInViewport(entry.isIntersecting),
      { threshold: 0.1 }
    )
    
    if (ref.current) {
      observer.observe(ref.current)
    }
    
    return () => observer.disconnect()
  }, [])
  
  return (
    <div ref={ref}>
      {isInViewport ? children : <ContentPlaceholder />}
    </div>
  )
}
```

**Responsive Design Patterns:**
- **Mobile-First CSS**: All styles start from mobile and enhance upward
- **Adaptive Components**: Different component implementations per screen size
- **Touch Optimization**: Minimum 48px touch targets, swipe gestures
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Performance Optimization**: Smaller assets and optimized queries for mobile
- **Accessibility**: Enhanced keyboard navigation and screen reader support

### State Management Architecture

**State Structure:**
```typescript
// Authentication Store (Zustand)
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  requires2FA: boolean
  tempToken: string | null
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  verify2FA: (code: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  setUser: (user: User) => void
}

// Permission Store (Zustand)
interface PermissionState {
  permissions: Record<string, AgentPermissions> | null
  isLoading: boolean
  lastUpdated: Date | null
  websocketConnected: boolean
  
  // Actions
  setPermissions: (permissions: Record<string, AgentPermissions>) => void
  updateAgentPermissions: (agent: string, permissions: AgentPermissions) => void
  clearPermissions: () => void
  setWebsocketStatus: (connected: boolean) => void
  
  // Computed
  hasAgentPermission: (agent: string, operation: string) => boolean
  getAgentPermissions: (agent: string) => AgentPermissions | null
}

// UI State Store (Zustand)
interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  currentBranding: BrandingConfig
  
  // Actions
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  updateBranding: (branding: BrandingConfig) => void
}

// Permission Types
interface AgentPermissions {
  create: boolean
  read: boolean
  update: boolean
  delete: boolean
}

interface UserPermissions {
  client_management?: AgentPermissions
  pdf_processing?: AgentPermissions
  reports_analysis?: AgentPermissions
  audio_recording?: AgentPermissions
}
```

### Routing Architecture

**Route Organization:**
- `/` - Public homepage
- `/login` - Authentication page
- `/dashboard` - Protected dashboard home
- `/dashboard/clients` - Client list with search/filters
- `/dashboard/clients/new` - New client registration
- `/dashboard/clients/[id]` - Client detail and edit
- `/dashboard/users` - User management (admin only)
- `/dashboard/system` - System configuration

### Frontend Services Layer

**API Client Setup:**
```typescript
class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1',
      timeout: 30000,
    })

    // Request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const { refreshToken, logout } = useAuthStore.getState()
          try {
            await refreshToken()
            return this.client.request(error.config)
          } catch (refreshError) {
            logout()
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }
}
```

### Permission System Frontend Architecture

**Permission Management Hooks:**
```typescript
// Custom hook for user permissions with caching and real-time updates
export const useUserPermissions = (userId?: string) => {
  const { user } = useAuth()
  const permissionStore = usePermissionStore()
  const targetUserId = userId || user?.user_id

  const { data: permissions, isLoading, error } = useQuery({
    queryKey: ['user-permissions', targetUserId],
    queryFn: () => permissionsAPI.getUserPermissions(targetUserId!),
    enabled: !!targetUserId && user?.role !== 'sysadmin',
    staleTime: 5 * 60 * 1000, // 5 minutes
    onSuccess: (data) => {
      permissionStore.setPermissions(data)
    }
  })

  const hasAgentPermission = useCallback((agent: string, operation: string): boolean => {
    // Sysadmin always has access
    if (user?.role === 'sysadmin') return true
    
    // Admin has access to client_management and reports_analysis
    if (user?.role === 'admin') {
      return ['client_management', 'reports_analysis'].includes(agent)
    }
    
    // Check specific permissions for regular users
    return permissions?.[agent]?.[operation] || false
  }, [user?.role, permissions])

  const updatePermissions = useMutation({
    mutationFn: (newPermissions: UserPermissions) => 
      permissionsAPI.updateUserPermissions(targetUserId!, newPermissions),
    onSuccess: () => {
      queryClient.invalidateQueries(['user-permissions', targetUserId])
      toast.success('Permissões atualizadas com sucesso')
    },
    onError: (error) => {
      toast.error('Erro ao atualizar permissões')
      console.error('Permission update error:', error)
    }
  })

  return {
    permissions,
    isLoading,
    error,
    hasAgentPermission,
    updatePermissions: updatePermissions.mutate,
    isUpdating: updatePermissions.isLoading
  }
}

// Hook for real-time permission updates via WebSocket
export const usePermissionUpdates = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const permissionStore = usePermissionStore()
  const [socket, setSocket] = useState<WebSocket | null>(null)

  useEffect(() => {
    if (!user?.user_id) return

    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/permissions`)
    
    ws.onopen = () => {
      permissionStore.setWebsocketStatus(true)
      console.log('Permission WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'permission_update') {
        // Invalidate permission queries for updated user
        queryClient.invalidateQueries(['user-permissions', data.user_id])
        queryClient.invalidateQueries(['permission-matrix'])
        
        // Update local permission store
        if (data.user_id === user.user_id) {
          permissionStore.setPermissions(data.permissions)
          toast.info('Suas permissões foram atualizadas')
        }
        
        // Show admin notification for other users
        if (user.role === 'admin' && data.user_id !== user.user_id) {
          toast.info(`Permissões atualizadas para usuário ${data.user_id}`)
        }
      }
    }

    ws.onclose = () => {
      permissionStore.setWebsocketStatus(false)
      console.log('Permission WebSocket disconnected')
    }

    ws.onerror = (error) => {
      console.error('Permission WebSocket error:', error)
      permissionStore.setWebsocketStatus(false)
    }

    setSocket(ws)
    
    return () => {
      ws.close()
    }
  }, [user?.user_id, queryClient, permissionStore])

  return {
    connected: permissionStore.websocketConnected,
    socket
  }
}
```

**Permission Guard Components:**
```typescript
// Permission-based conditional rendering component
interface PermissionGuardProps {
  agent: string
  operation: string
  children: React.ReactNode
  fallback?: React.ReactNode
  userId?: string
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  agent,
  operation,
  children,
  fallback = null,
  userId
}) => {
  const { hasAgentPermission } = useUserPermissions(userId)
  
  if (!hasAgentPermission(agent, operation)) {
    return <>{fallback}</>
  }
  
  return <>{children}</>
}

// Route-level permission protection
interface ProtectedRouteProps {
  children: React.ReactNode
  requiredAgent?: string
  requiredOperation?: string
  requiredRole?: UserRole
  fallback?: React.ReactNode
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredAgent,
  requiredOperation,
  requiredRole,
  fallback = <div>Acesso negado</div>
}) => {
  const { user } = useAuth()
  const { hasAgentPermission } = useUserPermissions()
  const router = useRouter()

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }

    // Check role requirement
    if (requiredRole && user.role !== requiredRole && user.role !== 'sysadmin') {
      router.push('/dashboard')
      return
    }

    // Check agent permission requirement
    if (requiredAgent && requiredOperation) {
      if (!hasAgentPermission(requiredAgent, requiredOperation)) {
        router.push('/dashboard')
        return
      }
    }
  }, [user, requiredRole, requiredAgent, requiredOperation, hasAgentPermission, router])

  // Show loading while checking permissions
  if (!user) {
    return <div>Carregando...</div>
  }

  // Check role access
  if (requiredRole && user.role !== requiredRole && user.role !== 'sysadmin') {
    return <>{fallback}</>
  }

  // Check agent permission access
  if (requiredAgent && requiredOperation && !hasAgentPermission(requiredAgent, requiredOperation)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
```

**Permission Management Components:**
```typescript
// User Permission Matrix Component
export const PermissionMatrix: React.FC = () => {
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: usersAPI.getUsers
  })

  const { data: permissionMatrix } = useQuery({
    queryKey: ['permission-matrix'],
    queryFn: permissionsAPI.getPermissionMatrix
  })

  const updatePermission = useMutation({
    mutationFn: ({ userId, agent, operation, value }: {
      userId: string
      agent: string
      operation: string
      value: boolean
    }) => permissionsAPI.updateSinglePermission(userId, agent, operation, value),
    onSuccess: () => {
      queryClient.invalidateQueries(['permission-matrix'])
      queryClient.invalidateQueries(['user-permissions'])
    }
  })

  const handlePermissionToggle = (userId: string, agent: string, operation: string) => {
    const currentValue = permissionMatrix?.[userId]?.[agent]?.[operation] || false
    updatePermission.mutate({
      userId,
      agent,
      operation,
      value: !currentValue
    })
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Usuário
            </th>
            {AGENTS.map(agent => (
              <th key={agent.name} className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                {agent.display_name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {users?.map(user => (
            <tr key={user.user_id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {user.full_name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {user.email}
                    </div>
                  </div>
                </div>
              </td>
              {AGENTS.map(agent => (
                <td key={agent.name} className="px-6 py-4 whitespace-nowrap text-center">
                  <PermissionCell
                    user={user}
                    agent={agent.name}
                    permissions={permissionMatrix?.[user.user_id]?.[agent.name] || {}}
                    onToggle={handlePermissionToggle}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Individual User Permission Dialog
export const UserPermissionsDialog: React.FC<{
  user: User
  isOpen: boolean
  onClose: () => void
}> = ({ user, isOpen, onClose }) => {
  const { permissions, updatePermissions, isUpdating } = useUserPermissions(user.user_id)
  const [localPermissions, setLocalPermissions] = useState<UserPermissions>(permissions || {})
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    if (permissions) {
      setLocalPermissions(permissions)
      setHasChanges(false)
    }
  }, [permissions])

  const handlePermissionToggle = (agent: string, operation: string) => {
    const newPermissions = {
      ...localPermissions,
      [agent]: {
        ...localPermissions[agent],
        [operation]: !localPermissions[agent]?.[operation]
      }
    }
    
    setLocalPermissions(newPermissions)
    setHasChanges(true)
  }

  const handleSave = async () => {
    updatePermissions(localPermissions)
    setHasChanges(false)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Gerenciar Permissões - {user.full_name}</DialogTitle>
          <DialogDescription>
            Configure as permissões do usuário para cada agente do sistema
          </DialogDescription>
        </DialogHeader>
        
        <Tabs defaultValue="client_management" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            {AGENTS.map(agent => (
              <TabsTrigger key={agent.name} value={agent.name}>
                {agent.short_name}
              </TabsTrigger>
            ))}
          </TabsList>
          
          {AGENTS.map(agent => (
            <TabsContent key={agent.name} value={agent.name}>
              <Card>
                <CardHeader>
                  <CardTitle>{agent.display_name}</CardTitle>
                  <CardDescription>{agent.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {OPERATIONS.map(operation => (
                      <div key={operation} className="flex items-center space-x-2">
                        <Checkbox
                          id={`${agent.name}-${operation}`}
                          checked={localPermissions[agent.name]?.[operation] || false}
                          onCheckedChange={() => handlePermissionToggle(agent.name, operation)}
                        />
                        <Label htmlFor={`${agent.name}-${operation}`}>
                          {OPERATION_LABELS[operation]}
                        </Label>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={!hasChanges || isUpdating}
          >
            {isUpdating ? 'Salvando...' : 'Salvar Alterações'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

**Permission-aware Navigation:**
```typescript
// Dynamic navigation menu with permission-based visibility
export const NavigationMenu: React.FC = () => {
  const { user } = useAuth()
  const { hasAgentPermission } = useUserPermissions()
  
  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
      show: true
    },
    {
      name: 'Clientes',
      href: '/dashboard/clients',
      icon: UsersIcon,
      show: hasAgentPermission('client_management', 'read')
    },
    {
      name: 'Documentos',
      href: '/dashboard/documents',
      icon: DocumentIcon,
      show: hasAgentPermission('pdf_processing', 'read')
    },
    {
      name: 'Relatórios',
      href: '/dashboard/reports',
      icon: ChartBarIcon,
      show: hasAgentPermission('reports_analysis', 'read')
    },
    {
      name: 'Gravações',
      href: '/dashboard/recordings',
      icon: MicrophoneIcon,
      show: hasAgentPermission('audio_recording', 'read')
    },
    {
      name: 'Usuários',
      href: '/dashboard/users',
      icon: UserGroupIcon,
      show: user?.role === 'admin' || user?.role === 'sysadmin'
    },
    {
      name: 'Permissões',
      href: '/dashboard/admin/permissions',
      icon: KeyIcon,
      show: user?.role === 'admin' || user?.role === 'sysadmin'
    }
  ]

  return (
    <nav className="space-y-1">
      {navigationItems
        .filter(item => item.show)
        .map(item => (
          <Link
            key={item.name}
            href={item.href}
            className="flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-50"
          >
            <item.icon className="mr-3 h-5 w-5" />
            {item.name}
          </Link>
        ))
      }
    </nav>
  )
}
```

### Cross-References to UX Architecture

**Integration with UX Documentation:**

This frontend architecture works in conjunction with several UX architecture documents to provide a complete user experience system:

#### UX Specification Integration
- **[UX Specification](./ux-specification.md)**: Defines user journeys, interaction patterns, and accessibility requirements that this architecture supports
- **Technical Implementation**: Our component architecture directly implements UX specification requirements through:
  - Workflow providers supporting multi-step user journeys
  - Permission-aware components providing contextual access control
  - Accessibility providers ensuring WCAG compliance
  - State management preserving user context across interactions

#### UI Design System Integration
- **[UI Design System](./ui-design-system.md)**: Provides visual design tokens, component specifications, and brand customization guidelines
- **Technical Implementation**: Our architecture integrates design system elements through:
  - shadcn/ui components as base implementation of design system patterns
  - CSS variable system enabling complete brand customization
  - Responsive design patterns ensuring consistent experience across devices
  - Theme provider managing dark/light modes and custom branding

#### Responsive Design Integration
- **[Responsive Design](./responsive-design.md)**: Defines breakpoint strategy, mobile-first approach, and adaptive interfaces
- **Technical Implementation**: Our responsive architecture includes:
  - Mobile-first Tailwind CSS configuration with custom breakpoints
  - Adaptive component rendering based on screen size
  - Progressive enhancement for mobile experiences
  - Touch-friendly interaction patterns for mobile devices

#### Permission System Cross-References
- **[Permission Integration Guide](./permission-integration-guide.md)**: Detailed implementation patterns for permission-aware UI
- **[Permission Quick Reference](./permission-quick-reference.md)**: Developer reference for permission system usage
- **[Developer Reference](./developer-reference.md)**: Comprehensive patterns and best practices

**Architecture Alignment:**
- **Component Architecture** → Implements UX patterns defined in specification
- **State Management** → Supports user experience flows and personalization
- **Permission System** → Provides seamless access control as specified in UX requirements
- **Performance Optimization** → Ensures responsive interactions meeting UX performance standards
- **Accessibility Features** → Technical implementation of accessibility requirements from UX specification

### Real-time Updates Architecture

**WebSocket Integration:**
- Automatic reconnection on connection loss
- Permission update broadcasting to affected users
- Optimistic UI updates with server validation
- Toast notifications for permission changes
- Cache invalidation for affected queries

**Performance Optimizations:**
- Permission caching with 5-minute stale time
- Optimistic updates for better UX
- Debounced permission matrix updates
- Lazy loading of permission dialogs
- Virtualized tables for large user lists
