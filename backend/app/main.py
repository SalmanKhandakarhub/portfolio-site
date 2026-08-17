"""Contact endpoint for the portfolio site.

Run locally:
    uvicorn app.main:app --reload --port 8020
"""

import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .mailer import send_enquiry_emails
from .ratelimit import client_ip, close_redis, init_redis, too_many
from .schemas import ContactIn, ContactOut

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
log = logging.getLogger("contact")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(title="Contact API", docs_url=None, redoc_url=None, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,   # explicit list, never "*"
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/contact", response_model=ContactOut)
async def contact(payload: ContactIn, request: Request, background: BackgroundTasks):
    ip = client_ip(request)

    # 1. Honeypot. Answer 200 so the bot believes it succeeded and moves on;
    #    a 400 just tells it which field to stop filling in.
    if payload.company:
        log.info("honeypot triggered from %s", ip)
        return ContactOut(ok=True, message="Thanks — your message has been sent.")

    # 2. Rate limit.
    if await too_many(ip):
        log.info("rate limited %s", ip)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "ok": False,
                "message": "You've sent a few messages already. Email me directly instead.",
            },
        )

    # 3. Queue both emails and return immediately. The visitor is not made to
    #    wait on an SMTP handshake that can take several seconds.
    background.add_task(
        send_enquiry_emails,
        name=payload.name,
        email=payload.email,
        kind=payload.kind,
        message=payload.message,
        ip=ip,
    )

    log.info("enquiry accepted from %s <%s>", payload.name, payload.email)
    return ContactOut(
        ok=True,
        message="Thanks — your message has been sent. Check your inbox for a confirmation.",
    )
