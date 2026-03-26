/**
 * tactile.js - Advanced Tactile Feedback for Agenda SDB
 * Uses Anime.js to provide premium spring physics on touch interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  
  // Select all premium interactive elements
  const selectors = [
    '.btn', 
    '.casa-card', 
    '.obra-card-premium', 
    '.nav-link', 
    '.dropdown-item',
    '.modal-close',
    '.modal-close-hero',
    '.btn-add-obra'
  ];

  const animatePress = (el) => {
    anime.remove(el); // Stop any ongoing animation
    anime({
      targets: el,
      scale: 0.94,
      duration: 120,
      easing: 'easeOutQuad'
    });
  };

  const animateRelease = (el) => {
    anime.remove(el);
    anime({
      targets: el,
      scale: 1,
      duration: 600,
      type: 'spring',
      stiffness: 300,
      damping: 12, // Damping 12 gives a nice subtle overshoot/jiggle
      mass: 0.8
    });
  };

  // Delegate events to the body for better performance and to handle dynamic content
  document.body.addEventListener('touchstart', (e) => {
    const target = e.target.closest(selectors.join(','));
    if (target) {
      animatePress(target);
    }
  }, { passive: true });

  document.body.addEventListener('touchend', (e) => {
    const target = e.target.closest(selectors.join(','));
    if (target) {
      animateRelease(target);
    }
  }, { passive: true });

  document.body.addEventListener('touchcancel', (e) => {
    const target = e.target.closest(selectors.join(','));
    if (target) {
      animateRelease(target);
    }
  }, { passive: true });

  // Optional: Add mouse feedback for desktop if explicitly desired, 
  // but the user asked for "celular" (mobile). 
  // Keeping it touch-only for now to respect user preferences.
});
