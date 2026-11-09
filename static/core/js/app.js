(function() {
  'use strict';

  // Helper: Get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken') || (document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : '');

  // --------------------------------------------------------------------------
  // 1. MOBILE NAVIGATION DRAWER & KEYBOARD ACCESSIBILITY
  // --------------------------------------------------------------------------
  const mobileNavToggle = document.getElementById('mobileNavToggle');
  const mobileNavMenu = document.getElementById('mobileNavMenu');
  const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');

  function openMobileNav() {
    if (!mobileNavMenu || !mobileNavToggle) return;
    mobileNavToggle.setAttribute('aria-expanded', 'true');
    mobileNavMenu.setAttribute('aria-hidden', 'false');
    mobileNavMenu.classList.add('is-active');
    const firstLink = mobileNavMenu.querySelector('a');
    if (firstLink) firstLink.focus();
  }

  function closeMobileNav() {
    if (!mobileNavMenu || !mobileNavToggle) return;
    mobileNavToggle.setAttribute('aria-expanded', 'false');
    mobileNavMenu.setAttribute('aria-hidden', 'true');
    mobileNavMenu.classList.remove('is-active');
  }

  if (mobileNavToggle) {
    mobileNavToggle.addEventListener('click', function() {
      const isExpanded = mobileNavToggle.getAttribute('aria-expanded') === 'true';
      if (isExpanded) {
        closeMobileNav();
      } else {
        openMobileNav();
      }
    });
  }

  mobileNavLinks.forEach(function(link) {
    link.addEventListener('click', function() {
      closeMobileNav();
    });
  });

  // --------------------------------------------------------------------------
  // 2. MOTION PRIMITIVES: SLIDING PILL TAB INDICATOR (DESKTOP)
  // --------------------------------------------------------------------------
  const navIndicator = document.getElementById('navIndicator');
  const navLinks = document.querySelectorAll('#navLinksList a');

  function moveIndicatorTo(el) {
    if (!navIndicator || !el) return;
    const rect = el.getBoundingClientRect();
    const parent = el.closest('.nav-links-wrap');
    if (!parent) return;
    const parentRect = parent.getBoundingClientRect();
    
    navIndicator.style.left = (rect.left - parentRect.left) + 'px';
    navIndicator.style.top = (rect.top - parentRect.top) + 'px';
    navIndicator.style.width = rect.width + 'px';
    navIndicator.style.height = rect.height + 'px';
    navIndicator.style.opacity = '1';
  }

  navLinks.forEach(function(link) {
    link.addEventListener('mouseenter', function() {
      moveIndicatorTo(link);
    });
  });

  const navWrap = document.querySelector('.nav-links-wrap');
  if (navWrap && navIndicator) {
    navWrap.addEventListener('mouseleave', function() {
      navIndicator.style.opacity = '0';
    });
  }

  // --------------------------------------------------------------------------
  // 3. CULT UI AI PROMPT TYPEWRITER & LIVE GENERATION
  // --------------------------------------------------------------------------
  const typedEl = document.getElementById('typed');
  const siteBlks = document.querySelectorAll('.blk');
  const txt = 'Architecture for RepairTrace AI: 3D inspection & WhatsApp automation';
  let charIdx = 0;

  function showBlocks() {
    siteBlks.forEach(function(el, k) {
      setTimeout(function() {
        el.classList.add('on');
      }, k * 350);
    });
  }

  if (typedEl) {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      typedEl.textContent = txt;
      siteBlks.forEach(el => el.classList.add('on'));
    } else {
      (function typePrompt() {
        if (charIdx <= txt.length) {
          typedEl.textContent = txt.slice(0, charIdx++);
          setTimeout(typePrompt, 35);
        } else {
          setTimeout(showBlocks, 250);
        }
      })();
    }
  }

  // --------------------------------------------------------------------------
  // 4. CULT UI SEGMENTED PLAN SELECTOR & SYNC
  // --------------------------------------------------------------------------
  const planButtons = document.querySelectorAll('.select-plan-btn');
  const cultPlanPills = document.querySelectorAll('.cult-plan-pill');
  const hiddenPlanField = document.getElementById('clientSelectedPlan');

  function updateWhatsAppLinks(planName) {
    const waFloat = document.getElementById('whatsappFloatBtn');
    const waSuccess = document.getElementById('whatsappSuccessBtn');
    const cleanNumber = (waFloat && waFloat.getAttribute('data-clean-wa')) || (waSuccess && waSuccess.getAttribute('data-clean-wa')) || '';
    if (cleanNumber) {
      const msg = encodeURIComponent(`Hi, I'm interested in a website. Plan: ${planName}`);
      const href = `https://wa.me/${cleanNumber}?text=${msg}`;
      if (waFloat) waFloat.href = href;
      if (waSuccess) waSuccess.href = href;
    }
  }

  function selectPlan(planName) {
    if (hiddenPlanField) hiddenPlanField.value = planName;
    cultPlanPills.forEach(function(btn) {
      btn.classList.toggle('active', btn.getAttribute('data-plan-choice') === planName);
    });
    updateWhatsAppLinks(planName);
  }

  planButtons.forEach(function(btn) {
    btn.addEventListener('click', function() {
      const plan = btn.getAttribute('data-plan-target');
      if (plan) selectPlan(plan);
    });
  });

  cultPlanPills.forEach(function(btn) {
    btn.addEventListener('click', function() {
      const plan = btn.getAttribute('data-plan-choice');
      if (plan) selectPlan(plan);
    });
  });

  // --------------------------------------------------------------------------
  // 5. MOTION PRIMITIVES SPRING ACCORDION (FAQ - ACCESSIBLE)
  // --------------------------------------------------------------------------
  const faqItems = document.querySelectorAll('.faq-spring-item');

  faqItems.forEach(function(item) {
    const btn = item.querySelector('.faq-spring-btn');
    if (btn) {
      btn.addEventListener('click', function() {
        const isOpen = item.classList.contains('open');
        faqItems.forEach(function(i) {
          i.classList.remove('open');
          const b = i.querySelector('.faq-spring-btn');
          if (b) b.setAttribute('aria-expanded', 'false');
        });
        if (!isOpen) {
          item.classList.add('open');
          btn.setAttribute('aria-expanded', 'true');
        }
      });
    }
  });

  // --------------------------------------------------------------------------
  // 6. WORKING DJANGO QUOTE FORM (DATABASE PERSISTENCE)
  // --------------------------------------------------------------------------
  const quoteForm = document.getElementById('quoteForm');
  const formSuccess = document.getElementById('formSuccess');
  const successEmail = document.getElementById('successEmail');
  const resetFormBtn = document.getElementById('resetFormBtn');
  const submitBtn = document.getElementById('submitQuoteBtn');
  const directEmailBtn = document.getElementById('directEmailBtn');
  const formErrorEl = document.getElementById('formErrorMessage');
  const contactEmail = (quoteForm && quoteForm.getAttribute('data-contact-email')) || 'admin@sitewright.ai';

  function showFormError(msg) {
    if (formErrorEl) {
      formErrorEl.textContent = msg;
      formErrorEl.style.display = 'block';
    }
  }

  function clearFormError() {
    if (formErrorEl) {
      formErrorEl.textContent = '';
      formErrorEl.style.display = 'none';
    }
  }

  if (quoteForm) {
    quoteForm.addEventListener('submit', function(e) {
      e.preventDefault();
      clearFormError();

      const name = document.getElementById('clientName').value.trim();
      const email = document.getElementById('clientEmail').value.trim();
      const business = document.getElementById('clientBusiness') ? document.getElementById('clientBusiness').value.trim() : '';
      const phone = document.getElementById('clientPhone') ? document.getElementById('clientPhone').value.trim() : '';
      const plan = hiddenPlanField ? hiddenPlanField.value : 'Business';
      const brief = document.getElementById('clientBrief') ? document.getElementById('clientBrief').value.trim() : '';

      const contactRefUrl = document.getElementById('formContactRefUrl') ? document.getElementById('formContactRefUrl').value.trim() : '';
      const websiteTrap = document.getElementById('formWebsiteTrap') ? document.getElementById('formWebsiteTrap').value.trim() : '';

      if (!name) {
        showFormError('Please provide your name.');
        return;
      }

      if (!email && !phone) {
        showFormError('Please provide at least one contact method (email or phone).');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
      }

      const payload = {
        name: name,
        email: email,
        business_name: business,
        phone: phone,
        plan: plan,
        brief: brief,
        contact_ref_url: contactRefUrl,
        website_trap: websiteTrap || contactRefUrl
      };

      fetch('/api/quote/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(payload)
      })
      .then(res => {
        return res.json().then(data => ({ status: res.status, body: data }));
      })
      .then(result => {
        const data = result.body;
        if (result.status === 429) {
          showFormError(data.error || 'Too many submissions. Please wait a moment before trying again.');
          return;
        }

        if (data.success) {
          clearFormError();
          if (successEmail) successEmail.textContent = email || phone;
          updateWhatsAppLinks(plan);

          // Track Plausible event
          if (typeof window.plausible === 'function') {
            window.plausible('LeadQuoteSubmitted', { props: { plan: plan } });
          }

          if (directEmailBtn) {
            const subject = encodeURIComponent(`Website Idea: ${business || name} (${plan})`);
            const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\nBusiness: ${business}\nPhone: ${phone}\nPlan: ${plan}\n\nDetails:\n${brief}`);
            directEmailBtn.href = `mailto:${contactEmail}?subject=${subject}&body=${body}`;
          }

          quoteForm.style.display = 'none';
          if (formSuccess) formSuccess.style.display = 'block';
        } else {
          let errorMsg = data.error;
          if (!errorMsg && data.errors) {
            errorMsg = Object.values(data.errors).flat().join(' ');
          }
          showFormError('Submission error: ' + (errorMsg || 'Unknown error occurred.'));
        }
      })
      .catch(err => {
        console.error('Submission error:', err);
        showFormError('Could not send. Please try again or email us directly');
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Send My Website Idea';
        }
      });
    });
  }

  if (resetFormBtn && quoteForm && formSuccess) {
    resetFormBtn.addEventListener('click', function() {
      clearFormError();
      quoteForm.reset();
      selectPlan('Business');
      formSuccess.style.display = 'none';
      quoteForm.style.display = 'block';
    });
  }

  // --------------------------------------------------------------------------
  // 7. PORTFOLIO PROJECT DETAIL MODAL (ACCESSIBLE DIALOG & FOCUS TRAP)
  // --------------------------------------------------------------------------
  const projectModal = document.getElementById('projectModal');
  const projectModalCloseBtn = document.getElementById('projectModalCloseBtn');
  const projectModalCategory = document.getElementById('projectModalCategory');
  const projectModalBadge = document.getElementById('projectModalBadge');
  const projectModalTitle = document.getElementById('projectModalTitle');
  const projectModalResult = document.getElementById('projectModalResult');
  const projectModalDesc = document.getElementById('projectModalDesc');
  const projectModalProblem = document.getElementById('projectModalProblem');
  const projectModalSolution = document.getElementById('projectModalSolution');
  const projectModalTech = document.getElementById('projectModalTech');
  const projectModalLiveBtn = document.getElementById('projectModalLiveBtn');
  const projectModalGithubBtn = document.getElementById('projectModalGithubBtn');
  const projectModalCtaBtn = document.getElementById('projectModalCtaBtn');
  let lastActiveElement = null;

  function closeProjectModal() {
    if (!projectModal) return;
    projectModal.style.display = 'none';
    if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
      lastActiveElement.focus();
    }
  }

  function openProjectModal(triggerBtn) {
    if (!projectModal) return;
    lastActiveElement = triggerBtn || document.activeElement;

    const title = triggerBtn.getAttribute('data-title') || '';
    const category = triggerBtn.getAttribute('data-category') || '';
    const badge = triggerBtn.getAttribute('data-badge') || 'Open Source';
    const result = triggerBtn.getAttribute('data-result') || '';
    const desc = triggerBtn.getAttribute('data-desc') || '';
    const problem = triggerBtn.getAttribute('data-problem') || '';
    const solution = triggerBtn.getAttribute('data-solution') || '';
    const tech = triggerBtn.getAttribute('data-tech') || '';
    const url = triggerBtn.getAttribute('data-url') || '';
    const github = triggerBtn.getAttribute('data-github') || '';

    if (projectModalTitle) projectModalTitle.textContent = title;
    if (projectModalCategory) projectModalCategory.textContent = category;
    if (projectModalBadge) projectModalBadge.textContent = badge;
    if (projectModalResult) projectModalResult.textContent = result;
    if (projectModalDesc) projectModalDesc.textContent = desc;

    if (projectModalProblem) {
      projectModalProblem.textContent = problem;
      const wrap = document.getElementById('projectModalProblemWrap');
      if (wrap) wrap.style.display = problem ? 'block' : 'none';
    }
    if (projectModalSolution) {
      projectModalSolution.textContent = solution;
      const wrap = document.getElementById('projectModalSolutionWrap');
      if (wrap) wrap.style.display = solution ? 'block' : 'none';
    }
    if (projectModalTech) {
      projectModalTech.textContent = tech;
      const wrap = document.getElementById('projectModalTechWrap');
      if (wrap) wrap.style.display = tech ? 'block' : 'none';
    }

    if (projectModalLiveBtn) {
      if (url && url !== github) {
        projectModalLiveBtn.href = url;
        projectModalLiveBtn.style.display = 'inline-block';
      } else {
        projectModalLiveBtn.style.display = 'none';
      }
    }

    if (projectModalGithubBtn) {
      if (github) {
        projectModalGithubBtn.href = github;
        projectModalGithubBtn.style.display = 'inline-block';
      } else {
        projectModalGithubBtn.style.display = 'none';
      }
    }

    projectModal.style.display = 'flex';
    if (projectModalCloseBtn) {
      projectModalCloseBtn.focus();
    }
  }

  document.querySelectorAll('.open-project-modal-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      openProjectModal(btn);
    });
  });

  if (projectModalCloseBtn) {
    projectModalCloseBtn.addEventListener('click', closeProjectModal);
  }

  if (projectModal) {
    projectModal.addEventListener('click', function(e) {
      if (e.target === projectModal) {
        closeProjectModal();
      }
    });

    // Modal Focus Trap
    projectModal.addEventListener('keydown', function(e) {
      if (e.key !== 'Tab') return;
      const focusable = projectModal.querySelectorAll('button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          last.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    });
  }

  if (projectModalCtaBtn) {
    projectModalCtaBtn.addEventListener('click', closeProjectModal);
  }

  // Global Escape handler
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      if (mobileNavToggle && mobileNavToggle.getAttribute('aria-expanded') === 'true') {
        closeMobileNav();
        mobileNavToggle.focus();
      }
      if (projectModal && projectModal.style.display === 'flex') {
        closeProjectModal();
      }
    }
  });

  // --------------------------------------------------------------------------
  // 8. PLAUSIBLE ANALYTICS: WHATSAPP EVENT TRACKING
  // --------------------------------------------------------------------------
  document.querySelectorAll('#whatsappFloatBtn, #whatsappSuccessBtn, .wa-track-link').forEach(function(btn) {
    btn.addEventListener('click', function() {
      if (typeof window.plausible === 'function') {
        window.plausible('WhatsAppChatClick', { props: { location: btn.id || 'footer_or_link' } });
      }
    });
  });

})();