/**
 * DocHub - Antigravity Dynamic Experience Engine
 * Handles interactive particle background, cursor parallax, scroll reveal,
 * video controls, and guest assessment persistence.
 */

(function() {
  'use strict';

  // 1. Particle Ambient Canvas (Google Antigravity Inspired)
  function initParticleCanvas() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    let mouse = { x: -1000, y: -1000, radius: 140 };

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      createParticles();
    }

    function createParticles() {
      particles = [];
      const particleCount = Math.min(Math.floor((width * height) / 18000), 80);
      for (let i = 0; i < particleCount; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.4,
          vy: (Math.random() - 0.5) * 0.4,
          radius: Math.random() * 2 + 0.8,
          alpha: Math.random() * 0.5 + 0.15,
          color: Math.random() > 0.4 ? 'rgba(124, 58, 237,' : 'rgba(99, 102, 241,'
        });
      }
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(124, 58, 237, ${0.12 * (1 - dist / 110)})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      // Draw and update particles
      for (let p of particles) {
        // Move
        p.x += p.vx;
        p.y += p.vy;

        // Wrap boundaries
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Mouse interaction
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {
          const force = (1 - dist / mouse.radius) * 1.5;
          p.x -= (dx / dist) * force;
          p.y -= (dy / dist) * force;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `${p.color} ${p.alpha})`;
        ctx.fill();
      }

      requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });
    window.addEventListener('mouseleave', () => {
      mouse.x = -1000;
      mouse.y = -1000;
    });

    resize();
    draw();
  }

  // 2. Navbar Scroll Behavior
  function initNavbar() {
    const nav = document.querySelector('.ag-nav');
    if (!nav) return;

    window.addEventListener('scroll', () => {
      if (window.scrollY > 30) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  // 3. Guest Session Progress Storage (from design2.txt)
  window.DocHubGuest = {
    saveProgress: function(assessmentId, currentStep, results) {
      try {
        const payload = {
          assessmentId: assessmentId,
          currentStep: currentStep,
          results: results,
          timestamp: new Date().toISOString()
        };
        localStorage.setItem(`dochub_guest_assessment_${assessmentId}`, JSON.stringify(payload));
        localStorage.setItem('dochub_last_guest_assessment', JSON.stringify(payload));
      } catch (e) {
        console.warn('localStorage error:', e);
      }
    },
    
    getProgress: function(assessmentId) {
      try {
        const raw = localStorage.getItem(`dochub_guest_assessment_${assessmentId}`);
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },
    
    clearProgress: function(assessmentId) {
      try {
        localStorage.removeItem(`dochub_guest_assessment_${assessmentId}`);
      } catch (e) {}
    }
  };

  // 4. Initialize on DOM ready
  document.addEventListener('DOMContentLoaded', () => {
    initParticleCanvas();
    initNavbar();
  });
})();
