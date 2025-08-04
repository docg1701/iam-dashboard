# Multi-Agent IAM Dashboard - UI Design System

*Last Updated: August 4, 2025 - Version 2.0 (Integrated Architecture)*

> **Quick Navigation**: [Design System Approach](#design-system-approach) | [Component Library](#component-library--specifications) | [Branding System](#custom-branding-system-architecture) | [Animation Guide](#animation--micro-interactions)

---

## Overview

This UI Design System specification defines the visual design, component library, and branding architecture for the Multi-Agent IAM Dashboard. It establishes a comprehensive design system using **shadcn/ui** components with **Tailwind CSS** that supports complete brand flexibility through CSS variables.

**Integration with Architecture:**
- **UX Foundation**: [UX Specification](./ux-specification.md)
- **Technical Implementation**: [Frontend Architecture](./frontend-architecture.md)
- **Permission Components**: [Permission Integration Guide](./permission-integration-guide.md)
- **Responsive Behavior**: [Responsive Design](./responsive-design.md)

---

## Design System Approach

### Core Technology Stack
- **Component Library**: shadcn/ui with Radix UI primitives
- **Styling**: Tailwind CSS with CSS variables for theming
- **Icons**: Lucide React for consistent iconography
- **Typography**: Inter (default) with customizable font stack
- **Motion**: Framer Motion for smooth animations

### Design System Principles
1. **Consistency**: Unified visual language across all components
2. **Accessibility**: WCAG AA compliance built into every component
3. **Customization**: Complete brand flexibility through CSS variables
4. **Performance**: Optimized components with minimal bundle impact
5. **Developer Experience**: Clear API with comprehensive documentation

---

## Component Library & Specifications

### Core Component Architecture

#### Primary Components

**Button Components**
- **Primary Button**: Main call-to-action styling with hover states
- **Secondary Button**: Supporting actions with outline styling  
- **Danger Button**: Destructive actions with warning colors
- **Icon Button**: Compact actions with icon-only display
- **Loading Button**: Progress indicators for async operations
- **Permission Button**: Conditional button rendering based on user permissions with disabled states

**Form Components**
- **Text Input**: Standard text fields with validation states
- **Select Dropdown**: Single and multi-select options
- **Date Picker**: Standardized date input with calendar popup
- **Checkbox/Radio**: Selection controls with indeterminate states
- **File Upload**: Drag-and-drop with progress indicators

**Data Display Components**
- **Data Table**: Sortable, filterable tables with pagination and permission-based column visibility
- **Card Layout**: Information containers with consistent spacing and conditional content
- **Stats Widget**: Metric display with trend indicators and permission-filtered data
- **Progress Bar**: Visual progress indication for operations
- **Badge/Tag**: Status and category labels including permission status indicators
- **User Card**: User information display with integrated permission status and agent access summary

#### Component States & Variants

**Interactive States**
- Default, Hover, Active, Disabled, Loading
- Focus states with keyboard navigation support
- Error states with validation messaging
- Permission states: Authorized, Unauthorized, Pending verification
- Conditional visibility states: Hidden, Visible, Partially visible

**Size Variants**
- Small (mobile-optimized), Medium (default), Large (desktop)
- Consistent sizing scale across all components

**Brand Variants**
- All components adapt to custom color schemes via CSS variables
- Typography variants supporting custom font selections

### Permission System Components

The permission system introduces specialized components for managing and displaying user permissions across the multi-agent platform.

#### Permission Control Components

**PermissionGuard**
- **Purpose**: Conditional rendering based on user permissions
- **Props**: `agent: string`, `operation: string`, `children: ReactNode`, `fallback?: ReactNode`
- **Usage**: Wraps components that should only be visible to users with specific agent permissions
- **States**: Loading, Authorized, Unauthorized
- **Example**: Hide/show "Create Client" button based on client_management:create permission

**ProtectedRoute**
- **Purpose**: Route-level permission protection with automatic redirects
- **Props**: `agent: string`, `operation: string`, `children: ReactNode`, `redirectTo?: string`
- **Usage**: Protects entire page routes from unauthorized access
- **States**: Loading, Authorized (renders children), Unauthorized (redirects)
- **Integration**: Works with Next.js App Router for seamless navigation protection

**PermissionBadge**
- **Purpose**: Visual indicators for permission status and access levels
- **Props**: `agent: string`, `operation?: string`, `user?: User`, `variant: 'status' | 'access' | 'template'`
- **Variants**: Status (granted/denied), Access level (create/read/update/delete), Template applied
- **States**: Granted (green), Denied (red), Partial (yellow), Loading (gray)
- **Usage**: Display user permission status in tables and user profiles

#### Permission Management Components

**PermissionMatrix**
- **Purpose**: Comprehensive user-agent permission grid for administrators
- **Props**: `users: User[]`, `onPermissionChange: Function`, `bulkMode?: boolean`
- **Features**: Real-time updates, bulk selection, filtering, search
- **Performance**: Virtualized rendering for 500+ users
- **States**: Loading matrix, Interactive mode, Bulk edit mode, Saving changes
- **Responsive**: Horizontal scroll on mobile, collapsible agent columns

**UserPermissionsDialog**
- **Purpose**: Individual user permission configuration interface
- **Props**: `user: User`, `isOpen: boolean`, `onClose: Function`, `onSave: Function`
- **Features**: Agent permission toggles, template application, audit history
- **Validation**: Real-time permission conflict detection
- **States**: View mode, Edit mode, Saving, Template selection
- **Accessibility**: Full keyboard navigation, screen reader support

**BulkPermissionDialog**
- **Purpose**: Multi-user permission operations for administrative efficiency
- **Props**: `selectedUsers: string[]`, `isOpen: boolean`, `onApply: Function`
- **Features**: User selection grid, permission modification panel, preview changes
- **Operations**: Bulk grant, bulk revoke, template application, permission merging
- **Safety**: Change preview, confirmation dialogs, rollback capability
- **Performance**: Batch API calls, progress tracking, operation cancellation

**PermissionTemplates**
- **Purpose**: Template management interface for standardized permission sets
- **Props**: `templates: PermissionTemplate[]`, `onTemplateAction: Function`
- **Features**: Create template, edit template, apply to users, delete template
- **Categories**: System templates (read-only), Custom templates, Organizational templates
- **Usage tracking**: Template application count, last used date
- **Validation**: Permission conflict detection, template naming constraints

#### Permission Form Components

**AgentPermissionCheckbox**
- **Purpose**: Agent-specific permission checkboxes with operation granularity
- **Props**: `agent: string`, `operation: string`, `value: boolean`, `onChange: Function`, `disabled?: boolean`
- **Features**: Visual operation icons, permission descriptions, dependency warnings
- **States**: Checked, Unchecked, Indeterminate (inherited), Disabled
- **Validation**: Real-time dependency checking (e.g., delete requires read)
- **Accessibility**: Clear labels, keyboard shortcuts, screen reader descriptions

**PermissionSelector**
- **Purpose**: Dropdown for selecting permission levels with predefined options
- **Props**: `agent: string`, `value: string`, `onChange: Function`, `options: PermissionLevel[]`
- **Options**: None, Read-only, Standard, Full access, Custom
- **Features**: Quick permission level selection, custom option for granular control
- **Integration**: Updates individual permission checkboxes when level changes
- **Validation**: Prevents invalid permission combinations

**TemplateSelector**
- **Purpose**: Template selection component with preview and application
- **Props**: `templates: PermissionTemplate[]`, `onSelect: Function`, `allowCustom?: boolean`
- **Features**: Template categories, permission preview, usage statistics
- **Search**: Template name and description search
- **Preview**: Expandable permission details before application
- **Integration**: Seamless integration with user creation and bulk operations

#### Permission Data Display Components

**PermissionStatus**
- **Purpose**: Comprehensive user permission overview with visual summaries
- **Props**: `user: User`, `detailed?: boolean`, `showAgentCards?: boolean`
- **Displays**: Total permissions count, agent access summary, template applied
- **Variants**: Compact (single line), Standard (card layout), Detailed (expandable)
- **Features**: Permission search, agent filtering, export capabilities
- **Updates**: Real-time permission change notifications

**AgentAccessCard**
- **Purpose**: Agent-specific access summary with operation breakdowns
- **Props**: `agent: string`, `permissions: AgentPermissions`, `compact?: boolean`
- **Features**: Operation icons, access level indicator, last activity
- **States**: Full access (green), Partial access (yellow), No access (gray), Loading
- **Interactive**: Click to expand detailed permissions, edit permissions (if authorized)
- **Integration**: Links to agent-specific interfaces and audit logs

**PermissionAuditLog**
- **Purpose**: Permission change history with comprehensive tracking
- **Props**: `userId?: string`, `agentName?: string`, `limit?: number`, `interactive?: boolean`
- **Features**: Chronological change log, change reason, user attribution
- **Filtering**: Date range, change type, user, agent
- **Export**: CSV export for compliance reporting
- **Performance**: Paginated loading, virtual scrolling for large logs
- **Details**: Before/after permission comparison, change impact analysis

#### Component Integration Patterns

**Conditional Rendering Pattern**
```typescript
<PermissionGuard agent="client_management" operation="create">
  <Button onClick={createClient}>New Client</Button>
</PermissionGuard>
```

**Route Protection Pattern**  
```typescript
<ProtectedRoute agent="user_management" operation="read">
  <UserManagementPage />
</ProtectedRoute>
```

**Permission Status Display Pattern**
```typescript
<div className="user-card">
  <UserInfo user={user} />
  <PermissionStatus user={user} detailed />
  <PermissionBadge agent="client_management" user={user} />
</div>
```

**Bulk Operations Pattern**
```typescript
const [selectedUsers, setSelectedUsers] = useState<string[]>([])

<UserSelectionTable onSelectionChange={setSelectedUsers} />
<BulkPermissionDialog 
  selectedUsers={selectedUsers}
  onApply={handleBulkUpdate}
/>
```

#### Permission Component Accessibility

**Loading States**
- Skeleton placeholders for permission matrices
- Shimmer effects for permission status cards
- Progress indicators for bulk operations
- Spinner overlays for real-time updates

**Error States**
- Permission check failures with retry options
- Validation errors with clear guidance
- Network error handling with offline indicators
- Unauthorized access with helpful explanations

**Accessibility Standards**
- WCAG AA compliance for all permission components
- Screen reader support with descriptive ARIA labels
- Keyboard navigation for all interactive elements
- High contrast mode support for permission indicators
- Focus management for modal dialogs and complex interactions

**Responsive Behavior**
- Mobile-first permission management interfaces
- Collapsible permission matrices for tablet viewing
- Touch-friendly permission toggles and selection
- Adaptive layouts for various screen sizes
- Bottom sheet interfaces for mobile permission editing

---

## Custom Branding System Architecture

The platform implements **complete visual customization** through CSS variables, allowing each client implementation to reflect their unique brand identity.

### Core Color Palette Structure

| Color Role | CSS Variable | Default Value | Usage |
|------------|--------------|---------------|--------|
| Primary | `--primary` | `222.2 47.4% 11.2%` | Main brand color for buttons, links |
| Primary Foreground | `--primary-foreground` | `210 40% 98%` | Text on primary backgrounds |
| Secondary | `--secondary` | `210 40% 96.1%` | Supporting elements |
| Background | `--background` | `0 0% 100%` | Main page background |
| Foreground | `--foreground` | `222.2 47.4% 11.2%` | Primary text color |
| Muted | `--muted` | `210 40% 96.1%` | Subtle backgrounds |
| Border | `--border` | `214.3 31.8% 91.4%` | Component borders |
| Destructive | `--destructive` | `0 62.8% 30.6%` | Error/delete actions |
| Success | `--success` | `142.1 76.2% 36.3%` | Success states |
| Warning | `--warning` | `47.9 95.8% 53.1%` | Warning states |

### Typography Scale

| Scale | CSS Variable | Default | Usage |
|--------|--------------|---------|--------|
| Base Font | `--font-sans` | 'Inter', system-ui | Body text and interface |
| Monospace | `--font-mono` | 'JetBrains Mono' | Code and data display |
| Heading XL | `text-4xl` | 36px/40px | Page titles |
| Heading L | `text-3xl` | 30px/36px | Section headers |
| Heading M | `text-xl` | 20px/28px | Component titles |
| Body L | `text-lg` | 18px/28px | Important body text |
| Body M | `text-base` | 16px/24px | Standard body text |
| Body S | `text-sm` | 14px/20px | Supporting text |
| Caption | `text-xs` | 12px/16px | Labels and captions |

### Approved Font Families for Customization

**Professional Sans-Serif Options**
- Inter (default) - Modern, highly legible
- Source Sans Pro - Clean, professional
- Open Sans - Friendly, approachable
- Roboto - Material Design aesthetic
- Nunito Sans - Rounded, modern

**Professional Serif Options** (for branded headers)
- Source Serif Pro - Traditional elegance
- Playfair Display - Editorial sophistication
- Lora - Readable serif for digital

### Iconography Guidelines

**Icon System**: Lucide React icons for consistency
**Icon Sizes**: 16px (small), 20px (medium), 24px (large), 32px (extra large)
**Icon Style**: Outline style for consistency, filled variants for selected states
**Custom Icons**: SVG format, optimized for performance, consistent stroke width

### Spacing & Layout System

**Spatial Scale** (based on 4px grid)
- `spacing-1`: 4px - Tight spacing
- `spacing-2`: 8px - Component internal spacing  
- `spacing-3`: 12px - Related element spacing
- `spacing-4`: 16px - Standard component spacing
- `spacing-6`: 24px - Section spacing
- `spacing-8`: 32px - Large section spacing
- `spacing-12`: 48px - Page section spacing

**Layout Radius**
- `--radius`: 0.5rem (8px) - Default border radius (customizable)
- Component radius scales: 0.25rem, 0.5rem, 0.75rem, 1rem

### Branding Implementation Guide

**CSS Variable Structure**
```css
:root {
  /* Color System */
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --background: 0 0% 100%;
  --foreground: 222.2 47.4% 11.2%;
  
  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Layout */
  --radius: 0.5rem;
}

/* Dark Mode Support */
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
}
```

**Custom Branding Configuration**
```typescript
interface BrandingConfig {
  colors: {
    primary: string
    secondary: string
    background: string
    foreground: string
  }
  typography: {
    fontFamily: string
    headingFont?: string
  }
  layout: {
    borderRadius: string
  }
  logo: {
    url: string
    width: number
    height: number
  }
}
```

---

## Animation & Micro-interactions

### Animation Principles
1. **Purposeful**: Every animation serves a functional purpose
2. **Subtle**: Enhance rather than distract from the user experience
3. **Fast**: Animations complete within 300ms for responsiveness
4. **Accessible**: Respect user motion preferences and provide alternatives

### Core Animation Library

**Transition Classes** (Tailwind CSS)
```css
/* Standard transitions */
.transition-standard { transition: all 150ms ease-in-out; }
.transition-fast { transition: all 100ms ease-in-out; }
.transition-slow { transition: all 300ms ease-in-out; }

/* Specific property transitions */
.transition-colors { transition: color, background-color, border-color 150ms ease-in-out; }
.transition-transform { transition: transform 150ms ease-in-out; }
.transition-opacity { transition: opacity 150ms ease-in-out; }
```

**Motion Variants** (Framer Motion)
```typescript
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 }
}

export const slideUp = {
  initial: { y: 20, opacity: 0 },
  animate: { y: 0, opacity: 1 },
  exit: { y: -20, opacity: 0 },
  transition: { duration: 0.3, ease: "easeOut" }
}

export const scaleIn = {
  initial: { scale: 0.9, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  exit: { scale: 0.9, opacity: 0 },
  transition: { duration: 0.2, ease: "easeOut" }
}
```

### Micro-interaction Specifications

**Button Interactions**
- **Hover**: Scale 1.02, shadow increase, 100ms duration
- **Active**: Scale 0.98, reduced shadow, 50ms duration
- **Loading**: Spinner with fade-in, button text fade-out
- **Success**: Brief green flash with checkmark icon

**Form Interactions**
- **Focus**: Border color change, shadow appearance, 150ms
- **Validation**: Error shake animation (3px x-axis, 3 cycles)
- **Success**: Subtle green glow, checkmark icon animation
- **Character count**: Color transition as limit approaches

**Permission Component Animations**
- **Permission Grant**: Green checkmark with scale bounce
- **Permission Deny**: Red X with shake animation
- **Matrix Updates**: Ripple effect from changed cell
- **Bulk Operations**: Progressive reveal of affected items

**Navigation Animations**
- **Page Transitions**: Slide in from right, fade previous
- **Sidebar**: Slide in from left with backdrop fade
- **Mobile Menu**: Scale up from hamburger button
- **Tab Switching**: Horizontal slide with indicator movement

### Accessibility Considerations

**Reduced Motion Support**
```css
@media (prefers-reduced-motion: reduce) {
  .transition-standard { transition: none; }
  .animate-spin { animation: none; }
  .animate-bounce { animation: none; }
}
```

**High Contrast Mode**
```css
@media (prefers-contrast: high) {
  .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.8); }
  .border { border-width: 2px; }
}
```

---

## Cross-References

### Related Architecture Documents
- **[UX Specification](./ux-specification.md)** - User experience foundation and workflows
- **[Frontend Architecture](./frontend-architecture.md)** - Technical component implementation
- **[Permission Integration Guide](./permission-integration-guide.md)** - Permission component patterns
- **[Responsive Design](./responsive-design.md)** - Device adaptation and accessibility

### Related PRD Documents
- **[User Interface Design Goals](../prd/user-interface-design-goals.md)** - Business UX objectives
- **[Technical Assumptions](../prd/technical-assumptions.md)** - Technology stack decisions

---

*This UI Design System provides the visual foundation and component specifications for the Multi-Agent IAM Dashboard. For user experience patterns and workflows, see the [UX Specification](./ux-specification.md).*