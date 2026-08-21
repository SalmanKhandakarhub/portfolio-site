/* ============================================================
   Salman — portfolio scripts
   Loaded by every page. Every section guards against missing
   elements, so one file safely serves all five pages.

     1. Nav              5. Work filter
     2. Scroll reveals   6. Contact form
     3. Request trace    7. Pointer layer
     4. FAQ              8. Footer year
   ============================================================ */

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ============================================================
   1. NAV — sticky border + mobile menu
   ============================================================ */
const nav = document.getElementById('nav');
if (nav) {
  addEventListener('scroll', () => nav.classList.toggle('is-stuck', scrollY > 20), { passive: true });
}

const toggle = document.getElementById('navToggle');
const panel = document.getElementById('navPanel');
if (toggle && panel) {
  toggle.addEventListener('click', () => {
    const open = panel.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  /* close after tapping a link */
  panel.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    panel.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }));
}

/* ============================================================
   2. SCROLL REVEALS
   ============================================================ */
const io = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('in'), i * 70);
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

/* ============================================================
   3. REQUEST TRACE — home page only
   ============================================================ */
const traceEl = document.getElementById('trace');
if (traceEl) {
  const rows = [...traceEl.querySelectorAll('.row')];
  const totalEl = document.getElementById('traceTotal');
  const textEl = document.getElementById('traceText');

  const timings = [4, 6, 3, 41, 2, 210, 18];   /* per-stage latency, ms */
  const peak = Math.max(...timings);
  let pinned = false;

  const paint = (i, ms) => {
    const r = rows[i];
    r.classList.add('is-lit');
    r.querySelector('.row__fill').style.width = Math.max(6, (ms / peak) * 100) + '%';
    r.querySelector('.row__ms').textContent = ms + 'ms';
  };

  const reset = () => {
    rows.forEach(r => {
      r.classList.remove('is-lit');
      r.querySelector('.row__fill').style.width = '0%';
      r.querySelector('.row__ms').textContent = '0ms';
    });
    totalEl.textContent = '—';
  };

  const run = () => {
    reset();
    let total = 0;
    rows.forEach((_, i) => setTimeout(() => {
      total += timings[i];
      paint(i, timings[i]);
      totalEl.textContent = total + 'ms';
    }, 260 + i * 260));
    setTimeout(run, 260 + rows.length * 260 + 3400);
  };

  if (reduced) {
    let t = 0;
    timings.forEach((ms, i) => { t += ms; paint(i, ms); });
    totalEl.textContent = t + 'ms';
  } else {
    const tio = new IntersectionObserver(e => {
      if (e[0].isIntersecting) { run(); tio.disconnect(); }
    }, { threshold: 0.3 });
    tio.observe(traceEl);
  }

  /* each stage explains itself on hover, and pins on click */
  const fallback = textEl.textContent;
  rows.forEach(r => {
    const show = () => { if (!pinned) textEl.textContent = r.dataset.detail; };
    const hide = () => { if (!pinned) textEl.textContent = fallback; };
    r.addEventListener('mouseenter', show);
    r.addEventListener('mouseleave', hide);
    r.addEventListener('focus', show);
    r.addEventListener('blur', hide);
    r.addEventListener('click', () => {
      const already = r.classList.contains('is-active');
      rows.forEach(x => x.classList.remove('is-active'));
      if (already) { pinned = false; textEl.textContent = fallback; }
      else { r.classList.add('is-active'); pinned = true; textEl.textContent = r.dataset.detail; }
    });
  });
}

/* marquee — duplicated so the loop has no seam */
const strip = document.getElementById('strip');
if (strip) {
  const items = ['FastAPI', 'Django', 'Flask', 'Python', 'Golang', 'AWS Cloud', 'PostgreSQL', 'Redis', 'Celery', 'AWS EC2', 'Docker', 'nginx', 'SQLAlchemy',
    'Pydantic', 'WebSockets', 'RAG', 'pgvector', 'Claude API', 'systemd', 'Poetry', 'MongoDB', 'Jitsi', 'AWS S3', 'AWS Lambda', 'Redis pub/sub',
    'Scikit-learn', 'TensorFlow', 'PyTorch', 'NumPy', 'Pandas', 'Matplotlib', 'TensorFlow', 'PyTorch'];
  strip.innerHTML = [...items, ...items].map(t => `<span>${t}</span>`).join('');
}

/* ============================================================
   4. FAQ — accordion
   ============================================================ */
document.querySelectorAll('.faq__q').forEach(q => {
  const a = q.nextElementSibling;
  q.addEventListener('click', () => {
    const open = q.getAttribute('aria-expanded') === 'true';
    q.setAttribute('aria-expanded', String(!open));
    a.style.maxHeight = open ? '0px' : a.scrollHeight + 'px';
  });
});

/* ============================================================
   5. WORK FILTER
   ============================================================ */
const filters = document.querySelectorAll('.filter');
if (filters.length) {
  const projects = [...document.querySelectorAll('.proj')];
  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      filters.forEach(b => b.classList.remove('is-on'));
      btn.classList.add('is-on');
      const want = btn.dataset.filter;
      let shown = 0;
      projects.forEach(p => {
        const match = want === 'all' || p.dataset.cat.includes(want);
        p.classList.toggle('is-hidden', !match);
        if (match) { p.querySelector('.proj__idx').textContent = String(++shown).padStart(2, '0'); }
      });
      const empty = document.getElementById('workEmpty');
      if (empty) empty.hidden = shown > 0;
    });
  });
}

/* ============================================================
   6. CONTACT FORM
   ------------------------------------------------------------
   Posts to the FastAPI endpoint in backend/. Set API_URL to
   wherever that is deployed. If backend and site share a domain,
   a relative '/api/contact' is enough and avoids CORS entirely.
   ============================================================ */
const send = document.getElementById('send');
if (send) {
  /* EDIT:API — relative path if same domain, full URL if not */
  // const API_URL = "https://portfolio-site-zma0.onrender.com/api/contact";
  const API_URL = 'http://127.0.0.1:8020/api/contact';
  
  const statusEl = document.getElementById('status');
  const fields = ['name', 'email', 'kind', 'msg'].map(id => document.getElementById(id));
  const honeypot = document.getElementById('company');
  const original = send.textContent;

  const setStatus = (kind, text) => {
    statusEl.className = 'form__status ' + kind;
    statusEl.textContent = text;
  };

  const submit = async () => {
    const [nameEl, emailEl, kindEl, msgEl] = fields;
    const name = nameEl.value.trim();
    const email = emailEl.value.trim();
    const msg = msgEl.value.trim();

    /* client-side checks are for fast feedback only —
       the server validates everything again, because this can be bypassed */
    if (!name || !email || !msg) {
      return setStatus('err', 'Add your name, email, and a few project details first.');
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return setStatus('err', 'That email address looks incomplete — check it and try again.');
    }
    if (msg.length < 20) {
      return setStatus('err', 'Tell me a little more — 20 characters at minimum.');
    }

    send.disabled = true;
    send.textContent = 'Sending…';
    setStatus('', '');

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          email,
          kind: kindEl.value,
          message: msg,
          company: honeypot ? honeypot.value : ''   /* honeypot: bots fill this */
        })
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok && data.ok) {
        setStatus('ok', data.message || 'Thanks — your message has been sent.');
        send.textContent = 'Sent ✓';
        fields.forEach(f => { if (f.tagName !== 'SELECT') f.value = ''; });
        return;   /* leave the button in its sent state */
      }

      if (res.status === 429) {
        setStatus('err', data.message || 'Too many messages. Email me directly instead.');
      } else if (res.status === 422) {
        setStatus('err', 'Something in the form was rejected — check your email address and message length.');
      } else {
        throw new Error('unexpected status ' + res.status);
      }
    } catch (err) {
      /* network down, CORS misconfigured, or the API is not running.
         Never leave the visitor with no way to reach you. */
      console.error('Contact form failed:', err);
      setStatus('err', "Couldn't send that — please email me directly instead.");
    } finally {
      if (send.textContent !== 'Sent ✓') {
        send.disabled = false;
        send.textContent = original;
      }
    }
  };

  send.addEventListener('click', submit);

  /* Ctrl/Cmd + Enter submits from the textarea */
  document.getElementById('msg').addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit();
  });
}

/* ============================================================
   7. POINTER LAYER
   Skipped on touch screens and when reduced motion is on.
   ============================================================ */
if (matchMedia('(hover:hover) and (pointer:fine)').matches && !reduced) {

  /* 7a. crosshair cursor */
  const ring = Object.assign(document.createElement('div'), { className: 'cur-ring' });
  const dot = Object.assign(document.createElement('div'), { className: 'cur-dot' });
  document.body.append(ring, dot);
  document.body.classList.add('cursor-on');

  let mx = innerWidth / 2, my = innerHeight / 2;
  let rx = mx, ry = my;

  addEventListener('mousemove', (e) => {
    mx = e.clientX; my = e.clientY;
    dot.style.transform = `translate3d(${mx}px, ${my}px, 0)`;
  }, { passive: true });

  (function follow() {
    rx += (mx - rx) * 0.16;
    ry += (my - ry) * 0.16;
    ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
    requestAnimationFrame(follow);
  })();

  const HOT = 'a, button, .row, .card, .proj, .chip';
  const TEXT = 'input, textarea, select';
  addEventListener('mouseover', (e) => {
    document.body.classList.toggle('cur-hot', !!e.target.closest(HOT));
    document.body.classList.toggle('cur-text', !!e.target.closest(TEXT));
  }, { passive: true });

  addEventListener('mouseleave', () => document.body.classList.remove('cursor-on'));
  addEventListener('mouseenter', () => document.body.classList.add('cursor-on'));

  /* 7b. spotlight follows the pointer inside each surface */
  document.querySelectorAll('.card, .proj, .trace').forEach(el => {
    el.addEventListener('mousemove', (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      el.style.setProperty('--my', (e.clientY - r.top) + 'px');
    }, { passive: true });
  });

  /* 7c. magnetic buttons */
  document.querySelectorAll('.cta-row .btn, #send').forEach(btn => {
    const PULL = 6;
    btn.addEventListener('mousemove', (e) => {
      const r = btn.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width / 2);
      const dy = e.clientY - (r.top + r.height / 2);
      btn.style.transform =
        `translate(${(dx / r.width) * PULL * 2}px, ${(dy / r.height) * PULL * 2 - 2}px)`;
    }, { passive: true });
    btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
  });
}

/* ============================================================
   8. FOOTER YEAR
   ============================================================ */
document.querySelectorAll('.year').forEach(el => el.textContent = new Date().getFullYear());
