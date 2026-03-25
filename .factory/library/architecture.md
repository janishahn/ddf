# Architecture

Architectural decisions, patterns discovered, and component structure.

## What belongs here

Component hierarchy, state management patterns, CSS architecture, key design decisions.

---

## Frontend Stack

- **Framework:** React 19 with TypeScript
- **Build:** Vite 7 with Tailwind CSS v4
- **UI Library:** shadcn/ui components (Radix UI primitives)
- **Styling:** Tailwind CSS with CSS custom properties for theming
- **Icons:** Lucide React
- **Toasts:** Sonner

## Component Structure

```
frontend/src/
├── App.tsx          # Main application component
├── main.tsx        # React entry point
├── api.ts          # API client functions
├── index.css       # Global styles, CSS animations
├── lib/utils.ts    # Utility functions (cn helper)
└── components/ui/  # shadcn/ui components
    ├── accordion.tsx
    ├── button.tsx
    ├── card.tsx
    ├── skeleton.tsx
    ├── toggle-group.tsx
    └── tooltip.tsx
```

## State Management

- **Local state:** React `useState` hooks
- **Async state:** Manual fetch with AbortController for cancellation
- **No global state library** - all state is component-local

## Key Patterns

### Layout Classes

- `max-w-5xl` - Current max-width (polish target: expand)
- `md:` - Mobile-to-desktop breakpoint (768px)
- `min-h-[calc(100svh-16rem)]` - Mobile viewer card height
- `min-h-[96px]` - Fixed footer height

### Animation Classes

- `album-enter` - Fade + slide-in on mount (420ms)
- `cover-sheen` - Diagonal shimmer (1.6s)
- `reroll-pulse` - Scale pulse during reroll (420ms)
- `shimmer` - Skeleton horizontal shimmer (1.4s infinite)

## CSS Custom Properties

Defined in `index.css`:

- `--radius`, `--radius-inset`, `--radius-tight` - Border radii
- `--font-body` (Lexend), `--font-display` (Fraunces)
- Color palette using HSL values
