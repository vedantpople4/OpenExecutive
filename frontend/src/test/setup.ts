import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import { MotionGlobalConfig } from 'motion/react'

// Component tests opt into jsdom per-file (`// @vitest-environment jsdom`), and jsdom has no
// real rAF or WAAPI. Without this, a Motion animation never advances to completion, so
// AnimatePresence keeps exiting nodes mounted forever -- assertions about what is *gone* hang
// or fail. Skipping animations makes every Motion component settle on its final values
// synchronously, which is what the tests actually assert about.
MotionGlobalConfig.skipAnimations = true

// Vitest doesn't expose `afterEach` as a global here (tests import it explicitly instead of
// relying on `test.globals`), so @testing-library/react's automatic cleanup detection never
// fires — without this, DOM from one test in a file bleeds into the next.
afterEach(() => {
  cleanup()
})
