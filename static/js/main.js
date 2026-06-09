/**
 * LaptopAI – main.js
 * Handles: form validation, scroll effects, loading state, animations
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll effect ───────────────────────────────────────
  const nav = document.getElementById('mainNav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 50);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ── Form validation & loading state ───────────────────────────
  const form = document.getElementById('recommendForm');
  if (form) {
    form.addEventListener('submit', (e) => {
      let valid = true;

      // Budget check
      const budgetInput = document.getElementById('budget');
      if (budgetInput) {
        const val = parseFloat(budgetInput.value);
        if (!budgetInput.value || isNaN(val) || val < 100) {
          budgetInput.classList.add('is-invalid');
          valid = false;
        } else {
          budgetInput.classList.remove('is-invalid');
          budgetInput.classList.add('is-valid');
        }
      }

      // RAM check
      const ramChecked = form.querySelector('input[name="ram"]:checked');
      if (!ramChecked) {
        document.getElementById('ram-options')?.classList.add('border-danger');
        valid = false;
      }

      // Storage check
      const storageChecked = form.querySelector('input[name="storage"]:checked');
      if (!storageChecked) {
        document.getElementById('storage-options')?.classList.add('border-danger');
        valid = false;
      }

      // Category check
      const catChecked = form.querySelector('input[name="category"]:checked');
      if (!catChecked) valid = false;

      if (!valid) {
        e.preventDefault();
        // Scroll to first error
        const firstInvalid = form.querySelector('.is-invalid, .border-danger');
        firstInvalid?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }

      // Show loading state
      const btn     = document.getElementById('submitBtn');
      const btnText = btn?.querySelector('.btn-text');
      const btnLoad = btn?.querySelector('.btn-loading');
      if (btn && btnText && btnLoad) {
        btnText.classList.add('d-none');
        btnLoad.classList.remove('d-none');
        btn.disabled = true;
      }
    });

    // Live budget formatting hint
    const budgetInput = document.getElementById('budget');
    if (budgetInput) {
      budgetInput.addEventListener('input', () => {
        const val = parseFloat(budgetInput.value);
        const hint = budgetInput.closest('.mb-4')?.querySelector('.form-hint');
        if (hint && !isNaN(val) && val > 0) {
          hint.textContent = `Budget yang dipilih: $${val.toLocaleString('en-US')}`;
          hint.style.color = 'var(--accent)';
        } else if (hint) {
          hint.textContent = 'Rentang: $100 – $10,000';
          hint.style.color = '';
        }
      });
    }
  }

  // ── Card stagger animation ─────────────────────────────────────
  const cards = document.querySelectorAll('.laptop-card');
  cards.forEach((card, i) => {
    card.style.animationDelay = `${i * 0.12}s`;
  });

  // ── Step cards hover parallax (desktop only) ──────────────────
  if (window.innerWidth > 992) {
    document.querySelectorAll('.step-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect  = card.getBoundingClientRect();
        const x     = (e.clientX - rect.left) / rect.width  - 0.5;
        const y     = (e.clientY - rect.top)  / rect.height - 0.5;
        card.style.transform = `translateY(-4px) rotateX(${-y*4}deg) rotateY(${x*4}deg)`;
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });
  }

  // ── Auto-dismiss flash alerts ──────────────────────────────────
  document.querySelectorAll('.flash-alert').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });

  // ── Smooth scroll for anchor links ────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── History table: highlight row on expand ────────────────────
  document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-bs-target');
      const target   = document.querySelector(targetId);
      if (!target) return;
      target.addEventListener('show.bs.collapse', () => {
        const row = btn.closest('tr');
        if (row) row.classList.add('table-active');
      }, { once: true });
      target.addEventListener('hide.bs.collapse', () => {
        const row = btn.closest('tr');
        if (row) row.classList.remove('table-active');
      }, { once: true });
    });
  });

});
