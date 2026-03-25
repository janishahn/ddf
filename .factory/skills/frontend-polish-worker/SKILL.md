---
name: frontend-polish-worker
description: Implements UI polish refinements including layout adjustments, loading animations, micro-interactions, and viewport parity fixes.
---

# Frontend Polish Worker

NOTE: Startup and cleanup are handled by `worker-base`. This skill defines the WORK PROCEDURE.

## When to Use This Skill

Use this worker for:
- Desktop layout expansion (max-width adjustments, grid/flex refinements)
- Mobile viewport optimization (ensuring key elements visible without scrolling)
- Loading animation refinement (timing, easing, crossfade transitions)
- Micro-interaction additions (hover states, transitions, button feedback)
- Reroll button position stability across title lengths

## Required Skills

- `agent-browser` - For visual verification via screenshots at multiple viewport sizes

## Work Procedure

### 1. Understand the Feature

Read the feature description carefully. Identify:
- Which layout breakpoints need adjustment
- What timing values need refinement
- Which interactive elements need hover/focus states

### 2. Implement TDD (Write Tests First)

Even for UI polish, write testable assertions before implementation:

1. **For layout changes:** Create a component test that verifies computed styles or class names
2. **For timing changes:** Document the expected timing values in comments
3. **For visibility assertions:** Plan viewport sizes to test (390x844, 390x667, 1920x1080, 1440x900)

Run `npm run lint` and fix any issues before proceeding.

### 3. Implement the Changes

Make focused changes to:
- `frontend/src/App.tsx` - Layout structure, component composition
- `frontend/src/index.css` - Animations, transitions, responsive utilities
- `frontend/src/components/ui/*.tsx` - Component-level hover/focus states

**Key files:**
- `App.tsx` - Main layout, grid configurations, responsive classes
- `index.css` - CSS animations, custom properties, keyframes

### 4. Verify with agent-browser

Use agent-browser to capture screenshots at multiple viewport sizes:

```bash
# Desktop viewports
agent-browser set viewport 1920 1080 && agent-browser screenshot --full /tmp/desktop-1920.png
agent-browser set viewport 1440 900 && agent-browser screenshot --full /tmp/desktop-1440.png

# Mobile viewports
agent-browser set viewport 390 844 && agent-browser screenshot --full /tmp/mobile-844.png
agent-browser set viewport 390 667 && agent-browser screenshot --full /tmp/mobile-667.png
```

Verify:
- Key elements visible in each viewport
- Layout fills horizontal space appropriately
- Animations play smoothly
- Hover states are visible

### 5. Interactive Testing

Test the complete user flows:
1. Initial page load - verify skeleton → album appears
2. Click reroll - verify loading animations
3. Change age filter - verify toggle animation and new album load
4. Hover over album cover - verify scale effect
5. Hover over buttons - verify hover feedback
6. Resize browser - verify layout adaptation

### 6. Run Validators

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

### 7. Document Changes

In your handoff, include:
- Specific files modified
- CSS timing values changed
- Viewport sizes tested
- Screenshots captured
- Any issues discovered

## Example Handoff

```json
{
  "salientSummary": "Expanded desktop layout from max-w-5xl to max-w-7xl, refined mobile viewport to ensure key elements visible at 390x667, added hover states to toggle group items, smoothed album-enter animation from 420ms to 320ms.",
  "whatWasImplemented": "Modified App.tsx to change container max-width from max-w-5xl to max-w-7xl (1280px to 1400px). Reduced viewer-card min-height on mobile from calc(100svh - 16rem) to calc(100svh - 12rem) to ensure album + title + controls fit in 667px viewport. Added hover:bg-muted/50 transition-colors duration-150 to ToggleGroupItem. Refined album-enter keyframes timing in index.css from 420ms to 320ms with ease-out easing. Verified with screenshots at 1920x1080, 1440x900, 390x844, and 390x667 viewports.",
  "whatWasLeftUndone": "",
  "verification": {
    "commandsRun": [
      {"command": "cd frontend && npm run lint", "exitCode": 0, "observation": "No lint errors"},
      {"command": "cd frontend && npm run build", "exitCode": 0, "observation": "Build succeeded"}
    ],
    "interactiveChecks": [
      {"action": "Set viewport to 1920x1080, captured screenshot", "observed": "Content now extends beyond previous 1280px limit, fills more horizontal space"},
      {"action": "Set viewport to 390x667, captured screenshot", "observed": "Album cover, title, age filter, and reroll button all visible without scrolling"},
      {"action": "Hovered over age filter toggle item", "observed": "Background transitions to muted/50 over 150ms"},
      {"action": "Triggered reroll, observed album transition", "observed": "Album enters with fade+slide animation over~320ms, smooth and quick"}
    ]
  },
  "tests": {
    "added": []
  },
  "discoveredIssues": []
}
```

## When to Return to Orchestrator

- Feature depends on backend API changes that don't exist
- Existing CSS animations cannot be refined without breaking other components
- Viewport requirements conflict with each other (e.g., fitting everything on 667px height requires unacceptable compromises on larger viewports)
- User experience requirements need clarification beyond what's specified
