import type { Variants } from 'motion/react'

/**
 * Shared entrance choreography for the speaking/report lists inside PhaseCard and RoundCard.
 *
 * Parent/child variants rather than an index-derived `delay` on each item. staggerChildren only
 * orchestrates the children present when the parent itself mounts -- replaying a past decision,
 * or expanding a collapsed phase -- which is exactly when several reports appear at once and a
 * sequence reads better than a flash. A report that streams in later inherits `show` from the
 * parent's context and animates immediately, instead of picking up a delay from its list index
 * and hesitating on screen.
 */
export const listVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 6 },
  show: { opacity: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } },
  // The speaking placeholder is replaced by the report card at the same list position, so this
  // exit is half of a crossfade rather than a card leaving the page. No y offset: sliding out
  // while its replacement slides in reads as two events instead of one substitution.
  exit: { opacity: 0, transition: { duration: 0.12 } },
}
