"""Request and response models. Validation happens here so the route body
stays about behaviour, not about checking strings."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Kind = Literal[
    "Backend API or architecture",
    "AI / LLM feature",
    "Real-time chat or video",
    "Fixing an existing system",
    "Something else",
]


class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    kind: Kind
    message: str = Field(min_length=20, max_length=5000)

    # Honeypot. Real visitors never see this field, so anything in it is a bot.
    # Named 'company' because that is what scrapers expect to find.
    company: str = ""

    @field_validator("name", "message")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("cannot be blank")
        return v

    @field_validator("message")
    @classmethod
    def reject_link_spam(cls, v: str) -> str:
        # Genuine enquiries rarely contain five or more links.
        if v.lower().count("http") >= 5:
            raise ValueError("too many links")
        return v


class ContactOut(BaseModel):
    ok: bool
    message: str
