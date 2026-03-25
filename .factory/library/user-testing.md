# User Testing

Testing surface, required testing skills/tools, and resource cost classification.

## Validation Surface

**Browser-based UI testing** via agent-browser:
- Desktop viewport: 1920x1080, 1440x900, 1366x768
- Tablet viewport: 768x1024
- Mobile viewport: 390x844 (standard smartphone), 390x667 (short smartphone)

## Required Testing Skills/Tools

- `agent-browser` - Required for all UI visual verification
- Screenshots with `--annotate` for element labeling
- Multiple viewport testing via `agent-browser set viewport`

## Resource Cost Classification

**Agent-browser instances:** ~300MB RAM per instance

On this machine:
- Max concurrent validators: **3-5**
- Testing is lightweight (viewport screenshots, no heavy rendering)
- Each validator can run sequential viewport tests

## Testing Approach

1. Start backend and frontend services
2. Open browser to `http://localhost:3000`
3. Set viewport to target size
4. Capture screenshot
5. Verify visual elements present
6. Interact with controls (reroll, age filter)
7. Capture screenshots during loading states
8. Verify console has no errors

## Manual Verification Checklist

For each viewport size, verify:
- [ ] Album cover visible
- [ ] Title text visible and readable
- [ ] Year/runtime metadata visible
- [ ] Age filter toggle visible
- [ ] Reroll button visible
- [ ] No horizontal scroll on desktop
- [ ] Minimal vertical scroll on mobile (390x667)
- [ ] Hover effects functional

## Flow Validator Guidance: Browser

### Isolation Rules
- All tests read from shared backend and frontend services
- No shared mutable state between tests
- Each validator works independently with its own browser session
- Use `--session` flag with agent-browser for session isolation

### Resource Boundaries
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Viewport sizes: Use exact dimensions as specified in assertions
- Sessions: Use session ID format `<session-prefix>__<group-id>` (e.g., `layout1234__desktop`)

### Concurrency Limits
- Max 3-5 concurrent browser sessions
- Each session uses ~300MB RAM
- Parallel validators safe to run simultaneously

### Required Evidence per Assertion
- Desktop assertions: Screenshot at 1920x1080 or 1440x900 or 1024x768
- Mobile assertions: Screenshot at 390x844 or 390x667
- Console check: `console-errors` in report
- Visual inspection notes required for each assertion

### Special Considerations
- VAL-STABLE assertions require comparing screenshots across multiple albums
- Use reroll action to get different albums for stability testing
- Capture initial load state before any interactions
