#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "fastapi",
#   "uvicorn",
#   "httpx",
#   "pyjwt"
# ]
# ///

import argparse
import httpx
import jwt
import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Rate limits from environment variables
# https://docs.notifications.service.gov.uk/rest-api.html#rate-limits
MINUTE_LIMIT = int(os.environ.get("MINUTE_LIMIT", 3_000))
# https://docs.notifications.service.gov.uk/rest-api.html#daily-limits
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", 250_000))

# API URL configuration
# https://docs.notifications.service.gov.uk/rest-api.html#base-url
BASE_URL = os.environ.get("BASE_URL", "https://api.notifications.service.gov.uk")
# https://docs.notifications.service.gov.uk/rest-api.html#send-an-email
EMAIL_ENDPOINT = "/v2/notifications/email"

app = FastAPI(title="Notifications API Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RateLimiter:
    def __init__(self):
        self._minute_windows = defaultdict(lambda: deque())
        self._daily_counters = defaultdict(int)
        self._current_day = datetime.now(timezone.utc).date()

    def check_rate_limit(self, issuer_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60

        while self._minute_windows[issuer_id] and self._minute_windows[issuer_id][0] < minute_ago:
            self._minute_windows[issuer_id].popleft()

        if len(self._minute_windows[issuer_id]) >= MINUTE_LIMIT:
            return False

        self._minute_windows[issuer_id].append(now)
        return True

    def check_daily_limit(self, issuer_id: str) -> bool:
        today = datetime.now(timezone.utc).date()
        if today != self._current_day:
            self._current_day = today
            self._daily_counters.clear()

        if self._daily_counters[issuer_id] >= DAILY_LIMIT:
            return False

        self._daily_counters[issuer_id] += 1
        return True


rate_limiter = RateLimiter()


def extract_api_key(auth_header: str) -> str:
    if auth_header.startswith("Bearer "):
        return auth_header.split("Bearer ")[1]
    return None


def get_issuer_from_jwt(token: str) -> str:
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload.get("iss")


@app.post(EMAIL_ENDPOINT, status_code=201)
async def send_email(request: Request):
    body = await request.json()

    auth_header = request.headers.get("Authorization", "")
    api_key = extract_api_key(auth_header)

    if api_key and "test-ratelimit" in body.get("email_address", ""):
        issuer_id = get_issuer_from_jwt(api_key)
        print(f"Mocking ... API Key: {api_key[:10]}... Issuer: {issuer_id}")

        if not rate_limiter.check_daily_limit(issuer_id):
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit exceeded: {DAILY_LIMIT} emails per day allowed"
            )

        if not rate_limiter.check_rate_limit(issuer_id):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {MINUTE_LIMIT} requests per minute allowed"
            )

        notification_id = str(uuid.uuid4())
        template_id = str(uuid.uuid4())
        reference = body.get("reference", "")
        subject = body.get("template_id") or "Test Email"
        email_body = body.get("personalisation", {}).get("body", "This is a test email for rate limiting")

        mock_response = {
            "id": notification_id,
            "reference": reference,
            "content": {
                "subject": subject,
                "body": email_body,
                "from_email": "test.notifications@example.gov.uk",
                "one_click_unsubscribe_url": "https://example.com/unsubscribe"
            },
            "uri": f"{BASE_URL}/v2/notifications/{notification_id}",
            "template": {
                "id": template_id,
                "version": 1,
                "uri": f"{BASE_URL}/v2/template/{template_id}"
            }
        }

        return mock_response

    # For all other requests, forward to the actual API
    headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}
    target_url = f"{BASE_URL}{EMAIL_ENDPOINT}"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            target_url,
            json=body,
            headers=headers,
            timeout=30.0
        )
        return response.json()


def main(args):
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notifications API Proxy with configurable URLs and rate limiting")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    args = parser.parse_args()
    main(args)
