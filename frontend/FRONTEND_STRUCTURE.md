# Frontend Structure Guide

This document outlines the reorganized frontend structure for better maintainability and developer experience.

## Directory Structure

```
src/
├── lib/                          # Core library code
│   ├── api/                      # API client and endpoints
│   │   ├── client.ts            # HTTP client configuration
│   │   └── index.ts             # API exports
│   ├── components/               # Reusable components
│   │   ├── ui/                  # Basic UI components
│   │   │   ├── ErrorAlert.svelte
│   │   │   ├── LoadingSpinner.svelte
│   │   │   └── index.ts
│   │   ├── forms/               # Form components
│   │   │   ├── Input.svelte
│   │   │   ├── Select.svelte
│   │   │   ├── Button.svelte
│   │   │   └── index.ts
│   │   ├── layout/              # Layout components
│   │   │   ├── Card.svelte
│   │   │   ├── Modal.svelte
│   │   │   └── index.ts
│   │   ├── charts/              # Chart components
│   │   │   ├── BaseChart.svelte
│   │   │   ├── LineChart.svelte
│   │   │   ├── BarChart.svelte
│   │   │   ├── PieChart.svelte
│   │   │   ├── DoughnutChart.svelte
│   │   │   └── index.ts
│   │   ├── filters/             # Filter components
│   │   │   ├── CategoryFilter.svelte
│   │   │   ├── DateRangeFilter.svelte
│   │   │   └── index.ts
│   │   ├── dashboard/           # Dashboard-specific components
│   │   │   ├── InteractiveKPICard.svelte
│   │   │   └── index.ts
│   │   └── index.ts             # All component exports
│   ├── stores/                  # Svelte stores
│   │   ├── leads.ts            # Lead management store
│   │   ├── ui.ts               # UI state management
│   │   └── index.ts
│   ├── types/                   # TypeScript type definitions
│   │   ├── enums.ts            # Enums (LeadStatus, etc.)
│   │   ├── entities.ts         # Core entity types
│   │   ├── api.ts              # API response types
│   │   ├── dashboard.ts        # Dashboard-specific types
│   │   └── index.ts
│   ├── utils/                   # Utility functions
│   │   ├── formatting/         # Formatting utilities
│   │   │   └── date.ts
│   │   ├── validation/         # Validation utilities
│   │   │   └── forms.ts
│   │   ├── chartSetup.ts       # Chart configuration
│   │   └── index.ts
│   ├── config.ts               # App configuration
│   └── index.ts                # Main lib exports
├── routes/                      # SvelteKit routes
│   ├── +layout.svelte          # Root layout
│   ├── +page.svelte            # Homepage
│   ├── dashboard/              # Dashboard routes
│   └── workflows/              # Workflow routes
├── app.css                     # Global styles
├── app.d.ts                    # App type definitions
└── app.html                    # HTML template
```

## Key Improvements

### 1. Better Component Organization
- **UI Components**: Basic reusable components (ErrorAlert, LoadingSpinner)
- **Form Components**: Form-specific components with consistent styling
- **Layout Components**: Layout helpers (Card, Modal)
- **Feature Components**: Domain-specific components (charts, filters, dashboard)

### 2. Modular Type System
- **Enums**: All enums in one place
- **Entities**: Core business entity types
- **API**: API-specific types and responses
- **Dashboard**: Dashboard and analytics types

### 3. Organized Utilities
- **Formatting**: Date, number, and text formatting
- **Validation**: Form and data validation
- **Chart Setup**: Chart.js configuration and formatting helpers (consolidated)

### 4. Centralized State Management
- **UI Store**: Loading states, errors, modals
- **Domain Stores**: Feature-specific state (leads, campaigns)

### 5. Clean Dependencies
- **Removed**: Unused authentication dependencies (lucia, argon2, postgresql adapters)
- **Consolidated**: Chart utilities into a single module
- **Minimal**: Only essential dependencies for the current feature set

## Usage Examples

### Importing Components
```typescript
// Import specific components
import { ErrorAlert, LoadingSpinner } from '$lib/components/ui';
import { Input, Button } from '$lib/components/forms';
import { Card, Modal } from '$lib/components/layout';

// Or import all components
import { ErrorAlert, Input, Card } from '$lib/components';
```

### Using Types
```typescript
// Import specific types
import type { Lead, LeadCreate } from '$lib/types/entities';
import type { LeadStatus } from '$lib/types/enums';
import type { ApiResponse } from '$lib/types/api';

// Or import all types
import type { Lead, LeadStatus, ApiResponse } from '$lib/types';
```

### Using Utilities
```typescript
// Import specific utilities
import { formatDate } from '$lib/utils/formatting/date';
import { validateEmail } from '$lib/utils/validation/forms';

// Or import all utilities
import { formatDate, validateEmail } from '$lib/utils';
```

### Using Stores
```typescript
import { isLoading, errorMessage } from '$lib/stores/ui';
import { leads } from '$lib/stores/leads';
```

## Component Guidelines

### Form Components
- All form components include consistent styling
- Support for validation states and error messages
- Accessible with proper labels and ARIA attributes

### UI Components
- Follow Tailwind CSS design system
- Include loading and error states where appropriate
- Responsive design by default

### Layout Components
- Flexible and composable
- Support for different sizes and variants
- Consistent spacing and styling

## Best Practices

1. **Import Organization**: Use the index files for cleaner imports
2. **Type Safety**: Always use TypeScript types for props and data
3. **Component Composition**: Prefer composition over large monolithic components
4. **Consistent Styling**: Use Tailwind classes consistently across components
5. **Error Handling**: Include proper error states and loading indicators

## Migration Notes

- Old `types.ts` has been split into organized modules
- Components have been reorganized by category
- All exports are available through index files for backward compatibility
- The main `$lib` import still works for all exports

## Recent Cleanup (Latest)

### Files Removed
- `test-imports.ts` - Temporary test file no longer needed
- `README.md` - Generic SvelteKit readme (redundant with this guide)
- `demo/+page.svelte` - Simple redirect route that wasn't essential
- `chartData.ts` - Functionality consolidated into chartSetup.ts

### Dependencies Cleaned
- Removed unused authentication packages (lucia, argon2, postgresql adapters)
- Removed database dependencies (pg, postgres, @types/pg, @types/node)
- Kept only essential chart and animation dependencies

## Future Enhancements

1. **Testing**: Add component tests using Vitest/Testing Library
2. **Storybook**: Add component documentation and examples
3. **Accessibility**: Enhance ARIA support and keyboard navigation
4. **Performance**: Add lazy loading for heavy components
5. **Theming**: Add dark mode and theme customization