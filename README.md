# Portfolio — Salman

A five-page portfolio site for a backend and AI engineer. No build step, no framework, no dependencies to install: open `index.html` in a browser and it runs.

---

## Technologies used

| Layer | Technology | Why it's here |
|---|---|---|
| Markup | **HTML5** | Semantic elements (`header`, `nav`, `main`, `section`, `article`, `footer`) so screen readers and search engines can read the structure |
| Styling | **CSS3** | Written by hand — no Tailwind, no Bootstrap. Nothing to compile and nothing to update |
| — Layout | **CSS Grid & Flexbox** | Grid for page structure and card layouts, Flexbox for rows and alignment |
| — Theming | **CSS Custom Properties** | Every colour, font, and spacing value is a variable in `:root`. Change the whole palette in one place |
| — Responsive | **Media queries** | Three breakpoints: 980px, 720px, 420px |
| — Motion | **CSS transitions & keyframes** | Hover states, reveals, the marquee, and the pulsing status dot |
| Behaviour | **Vanilla JavaScript (ES6+)** | One 250-line file. No React, no jQuery, no bundler |
| — Reveals | **IntersectionObserver API** | Elements animate in when scrolled into view; far cheaper than scroll listeners |
| — Pointer | **requestAnimationFrame** | Drives the trailing cursor at 60fps without blocking the main thread |
| — Layout reads | **getBoundingClientRect** | Positions the spotlight and magnetic-button effects relative to each element |
| Typography | **Google Fonts** | Bricolage Grotesque (display), Public Sans (body), JetBrains Mono (data and labels) |
| Metadata | **Open Graph tags** | Controls the preview card when a page is shared on LinkedIn, Slack, or WhatsApp |
| Hosting | **Any static host** | Netlify, Vercel, GitHub Pages, Cloudflare Pages, or plain nginx |

**Browser support:** every modern browser — Chrome, Edge, Firefox, Safari, and their mobile versions. No polyfills needed.

---

## Structure

```
portfolio/
├── index.html          Home — hero, live request trace, service and work teasers
├── services.html       Detailed services, what each includes, four-step process
├── work.html           Full project list with category filtering
├── about.html          Bio, principles, dated timeline, full stack
├── contact.html        Contact form, direct links, FAQ accordion
├── assets/
│   ├── css/style.css   All styling for all five pages
│   └── js/main.js      All behaviour for all five pages
├── backend/            FastAPI contact API — see backend/README.md
│   ├── app/
│   │   ├── main.py         The /api/contact endpoint
│   │   ├── config.py       Settings from .env
│   │   ├── schemas.py      Pydantic validation
│   │   ├── mailer.py       Sends both emails
│   │   ├── ratelimit.py    Redis per-IP limiting
│   │   └── templates/      HTML email bodies
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

CSS and JS are shared across every page. Edit one file and all five update — which is the whole reason they aren't inlined.

---

## Features

- **Live request trace (home page).** Animates a request through middleware, database, Redis, LLM, and response, accumulating latency in real time. Each stage is hoverable and clickable and explains what happens at that layer. This is the centrepiece — it replaces a bullet list of skills with something that demonstrates systems thinking.
- **Crosshair cursor.** An amber dot tracks the pointer exactly; a ring trails behind with easing and opens into a crosshair over anything clickable.
- **Spotlight surfaces.** A soft glow follows the pointer inside cards, project rows, and the trace panel.
- **Magnetic buttons.** Primary buttons lean toward the cursor by up to 6px.
- **Work filter.** Filters projects by category and renumbers the visible ones.
- **FAQ accordion.** Height-animated, driven by `aria-expanded`.
- **Mobile menu.** Slide-down panel below 720px.
- **Working contact form.** Posts to the FastAPI backend, which emails you the enquiry and sends the visitor an automatic acknowledgement. Honeypot field and per-IP rate limiting included.

---

## Accessibility

Built to a floor, not as an afterthought:

- Skip-to-content link for keyboard users
- Visible focus outlines on every interactive element
- `aria-current="page"` marks the active nav item
- `aria-expanded` on the menu toggle and FAQ buttons
- `role="status"` on form feedback so it's announced
- All pointer effects disabled under `prefers-reduced-motion: reduce`
- All pointer effects skipped on touch devices via `(hover:hover) and (pointer:fine)`
- Text meets WCAG AA contrast against the dark background

---

## Before you publish

Search the files for these markers:

| Marker | Where | What to change |
|---|---|---|
| `EDIT:EMAIL` | `contact.html` | Your real address in the contact links |
| `EDIT:API` | `main.js` section 6 | Where the contact backend lives |
| `EDIT:LINKS` | `contact.html` | GitHub and LinkedIn URLs |
| `EDIT:WORK` | `work.html` | Your own projects. Keep the metric chips — the numbers do the persuading |
| `.env` values | `backend/.env` | SMTP credentials and your inbox address |
| Timeline dates | `about.html` | Your actual roles and dates |
| `salman.dev` | all pages | Brand text in the nav, if you want something else |

Also update the `<title>` and `<meta name="description">` on each page — they're what appears in search results.

### Making the contact form send

The form posts to a FastAPI service in `backend/` that emails you the enquiry **and** emails the visitor a confirmation. Setup, deployment, and deliverability notes are in [`backend/README.md`](backend/README.md).

Quick version:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in SMTP details
uvicorn app.main:app --port 8020
```

Then set `API_URL` in section 6 of `assets/js/main.js`. If nginx serves the site and proxies `/api/` to the backend, the default relative `/api/contact` is all you need and CORS never applies.

If you'd rather not run a backend at all, [Formspree](https://formspree.io) accepts the same JSON shape — but it can't send the acknowledgement email.

---

## Deploying

**Netlify (fastest):** drag the folder onto [app.netlify.com/drop](https://app.netlify.com/drop). Live in under a minute with HTTPS.

**GitHub Pages (free, your own repo):**

```bash
git init
git add .
git commit -m "Portfolio site"
git remote add origin https://github.com/YOURNAME/YOURNAME.github.io.git
git push -u origin main
```

Then enable Pages in the repository settings. Site appears at `https://YOURNAME.github.io`.

**Your own server:** copy the folder to the host and point an nginx `root` at it. No process to run — it's static files.

---

## Customising

**Change the colour scheme** — edit the seven values at the top of `style.css`:

```css
:root{
  --ink:   #08181C;   /* page background        */
  --ink-2: #0E262B;   /* cards and raised areas */
  --ink-3: #143238;   /* borders and tracks     */
  --bone:  #E8E6DD;   /* body text              */
  --muted: #7E9499;   /* secondary text         */
  --amber: #F0A03C;   /* primary accent         */
  --mint:  #5FD6C8;   /* secondary accent       */
}
```

**Remove the mouse effects** — delete the `POINTER LAYER` block in `style.css` and section 7 in `main.js`. Both are clearly marked and nothing else depends on them.

**Adjust the trace timings** — the `timings` array in section 3 of `main.js` sets each stage's latency in milliseconds. The largest value scales the bars.

**Add a project** — copy an `<article class="proj">` block in `work.html` and set `data-cat` to one or more of `backend`, `ai`, `realtime`, `infra`.
