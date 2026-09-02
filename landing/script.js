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
