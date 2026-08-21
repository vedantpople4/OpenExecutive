import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Vitest doesn't expose `afterEach` as a global here (tests import it explicitly instead of
// relying on `test.globals`), so @testing-library/react's automatic cleanup detection never
// fires — without this, DOM from one test in a file bleeds into the next.
afterEach(() => {
  cleanup()
})
