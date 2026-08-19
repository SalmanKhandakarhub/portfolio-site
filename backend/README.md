# Contact API

A small FastAPI service behind the portfolio contact form. One endpoint, two emails.

When someone submits the form:

1. The payload is validated and checked against a honeypot and a per-IP rate limit.
2. **You** get a notification email with their details, and `Reply-To` set to their address — so hitting reply in your mail client answers them directly.
3. **They** get an acknowledgement email confirming it arrived, with a copy of what they sent.
4. The browser gets a response immediately. Both emails go out in a background task, because a slow SMTP handshake should never become a slow form.

---

## Technologies

| Piece | Choice | Why |
|---|---|---|
| Framework | FastAPI | Async, typed, and you already know it |
| Validation | Pydantic v2 | `EmailStr`, length bounds, and a `Literal` for the topic field — a bad payload never reaches your logic |
| Email | `aiosmtplib` | Async SMTP, so sending doesn't block the event loop |
| Templates | Jinja2 | Autoescaped — visitor input can't inject HTML into your inbox |
| Rate limiting | Redis | Shared across workers (see the note below) |
| Config | pydantic-settings | Everything from `.env`, nothing hardcoded |

---

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env       # then fill it in
uvicorn app.main:app --reload --port 8020
```

Check it's alive:

```bash
curl localhost:8020/api/health
```

Send a test enquiry:

```bash
curl -X POST localhost:8020/api/contact \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test User","email":"your-other@address.com",
       "kind":"Backend API or architecture",
       "message":"Testing the contact form end to end, at least twenty characters."}'
```

Both emails should arrive within a few seconds. If they don't, check the logs — every failure is logged with `exc_info`, so you get the actual exception rather than an empty string.

### Gmail specifically

Turn on 2-factor authentication, then generate an **App Password** and use that as `SMTP_PASSWORD`. Your normal Google password will be rejected.

`FROM_EMAIL` must be the Gmail account itself, or an alias verified in Gmail's settings. Setting it to an address Gmail isn't authorised to send as is the fastest way to land in spam.

---

## Deliverability — read this before going live

The notification to yourself will always arrive; it's the acknowledgement to strangers that's fragile. Automated mail from a Gmail account to someone who has never emailed you is exactly what spam filters are built to catch.

**Gmail SMTP is fine for low volume** — a handful of enquiries a week. Beyond that, or if confirmations start landing in spam, move to a transactional provider. You're already on AWS, so **SES** is the natural fit, and it's SMTP too: change four values in `.env` and nothing in the code.

Whichever you use, set up **SPF** and **DKIM** DNS records for your domain. Without them, confirmation emails are a coin flip.

---

## Deploying alongside your existing stack

This follows the same pattern as your other services.

**systemd** — `/etc/systemd/system/contact-api.service`:

```ini
[Unit]
Description=Portfolio contact API
After=network.target

[Service]
User=deploy
WorkingDirectory=/opt/project/portfolio/backend
EnvironmentFile=/opt/project/portfolio/backend/.env
ExecStart=/opt/project/portfolio/backend/.venv/bin/uvicorn app.main:app \
          --host 127.0.0.1 --port 8020 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now contact-api
```

Use the absolute path to the venv's `uvicorn`. systemd doesn't inherit your shell's `PATH`.

**nginx** — serve the static site and proxy the one API path, so the frontend can use a relative `/api/contact` and CORS never comes into it:

```nginx
server {
    server_name salman.dev;
    root /opt/project/portfolio;
    index index.html;

    location / {
        try_files $uri $uri.html $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8020;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The `X-Forwarded-For` header is what the rate limiter reads. Without it every request looks like it came from `127.0.0.1` and one visitor can lock out everyone else.

---

## Design notes

**Why Redis for rate limiting.** With multiple Uvicorn workers, a counter in a Python dict lives in one process. A limit of 3 quietly becomes 3 × workers, and which one you hit depends on which worker took the request. Redis gives one shared counter regardless of worker count.

**Why it fails open.** If Redis is unreachable the limiter stops limiting rather than blocking everything. A cache outage taking down your contact form is a worse outcome than a few spam messages.

**Why the honeypot returns 200.** Telling a bot it failed teaches it which field to leave alone next time. Returning success makes it move on believing the job is done.

**Why background tasks.** SMTP can take several seconds. Queueing the send and returning immediately means the visitor sees confirmation instantly. The trade-off: if sending fails afterwards, they've already been told it worked — which is why the notification failure is logged at `error` level. Set up an alert on that line.

**Why validation is duplicated.** The client-side checks exist for fast feedback. They're trivially bypassed with `curl`, so the server validates everything again from scratch.

---

## Possible next steps

- Store enquiries in Postgres as well as emailing them, so nothing is lost if SMTP fails
- Add a Slack or Telegram webhook for instant notification on your phone
- Swap `BackgroundTasks` for Celery if you want retries on failed sends
