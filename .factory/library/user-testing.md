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
