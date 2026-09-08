// Solidifies the nav once the page scrolls past the hero's top edge — it
// starts transparent over the hero, then picks up a background + border so
// it stays legible over whatever content is underneath it.
const nav = document.getElementById('nav');

function updateNavState() {
  nav.classList.toggle('nav--scrolled', window.scrollY > 24);
}

updateNavState();
window.addEventListener('scroll', updateNavState, { passive: true });

// Close the mobile menu after a link inside it is tapped, so navigating
// doesn't leave the panel open underneath the new scroll position.
const navToggle = document.getElementById('nav-toggle');
document.querySelectorAll('.nav__mobile-panel a').forEach((link) => {
  link.addEventListener('click', () => {
    navToggle.checked = false;
  });
});

// Rotates the hero's "X is thinking" preview through the board so it reads
// as a live process rather than one fixed agent. Purely decorative — no
// aria-live, so it doesn't interrupt screen reader users with a chat every
// ~3 seconds for a widget that isn't reporting anything real.
// Fades + slides each `.reveal` element in as it scrolls into view. The
// hidden starting state only exists under the `.js` class the head script
// adds pre-paint, so this never fights a no-JS or reduced-motion visitor —
// see the `.js .reveal` rule in styles.css for why.
const revealEls = document.querySelectorAll('.reveal');
if (revealEls.length && 'IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );
  revealEls.forEach((el) => revealObserver.observe(el));
} else {
  revealEls.forEach((el) => el.classList.add('is-visible'));
}

const speakingText = document.getElementById('speaking-preview-text');
if (speakingText) {
  const agents = ['CFO', 'CTO', 'CEO', 'CMO'];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let i = 0;

  setInterval(() => {
    i = (i + 1) % agents.length;
    const next = `${agents[i]} IS THINKING…`;
    if (reduceMotion) {
      speakingText.textContent = next;
    } else {
      speakingText.classList.add('is-fading');
      setTimeout(() => {
        speakingText.textContent = next;
        speakingText.classList.remove('is-fading');
      }, 350);
    }
  }, 2800);
}
