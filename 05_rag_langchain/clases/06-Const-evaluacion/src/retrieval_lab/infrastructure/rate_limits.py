from __future__ import annotations

import os
import random
import re
import threading
import time
from collections import deque
from email.utils import parsedate_to_datetime
from retrieval_lab.infrastructure.concurrency import check_cancelled


class RequestLimiter:
    def __init__(self, provider=None):
        prefix = f"{provider.upper()}_EMBEDDING" if provider else ""
        self.rpm = int(os.getenv(f"{prefix}_RPM") or 0)
        self.tpm = int(os.getenv(f"{prefix}_TPM") or 0)
        if self.rpm < 0 or self.tpm < 0:
            raise ValueError("Las cuotas de peticiones y tokens no pueden ser negativas.")
        self.lock = threading.Lock()
        self.requests = deque()
        self.token_total = 0
        self.request_total = 0
        self.cooldown = 0.0
        self.next_request = 0.0

    def acquire(self, tokens=0, requests=1):
        while True:
            check_cancelled()
            with self.lock:
                if (self.tpm and tokens > self.tpm) or (self.rpm and requests > self.rpm):
                    raise ValueError("Un lote excede la cuota configurada; reduzca su tamaño.")
                now = time.monotonic()
                while self.requests and self.requests[0][0] <= now - 60:
                    _, old_tokens, old_requests = self.requests.popleft()
                    self.token_total -= old_tokens
                    self.request_total -= old_requests
                delay = max(0.0, self.cooldown - now, self.next_request - now)
                full = ((self.rpm and self.request_total + requests > self.rpm) or
                        (self.tpm and self.token_total + tokens > self.tpm))
                if full:
                    delay = max(delay, self.requests[0][0] + 60 - now)
                if delay <= 0:
                    self.requests.append((now, tokens, requests))
                    self.token_total += tokens
                    self.request_total += requests
                    self.next_request = now + max(60 * requests / self.rpm if self.rpm else 0,
                                                  60 * tokens / self.tpm if self.tpm else 0)
                    return
            time.sleep(min(delay, 1.0))

    def defer(self, seconds):
        with self.lock:
            self.cooldown = max(self.cooldown, time.monotonic() + seconds)

    def learn(self, violations):
        with self.lock:
            for violation in violations:
                quota = violation.get("quotaId", "").lower()
                if "perminute" not in quota:
                    continue
                try:
                    limit = max(1, int(float(violation["quotaValue"]) * .9))
                except (KeyError, TypeError, ValueError):
                    continue
                field = "tpm" if "token" in quota else "rpm" if "embedcontent" in quota or "request" in quota else None
                if field:
                    current = getattr(self, field)
                    setattr(self, field, min(current, limit) if current else limit)


def error_details(error):
    body = getattr(error, "details", None) or getattr(error, "body", None) or {}
    if isinstance(body, dict):
        body = body.get("error", body)
    return body if isinstance(body, dict) else {}


def error_status(error):
    for source in (error, getattr(error, "response", None)):
        for name in ("status_code", "code", "status"):
            try:
                status = int(getattr(source, name, None))
            except (TypeError, ValueError):
                continue
            if 100 <= status <= 599:
                return status
    return 429 if getattr(error, "status", None) == "RESOURCE_EXHAUSTED" else None


def quota_details(error):
    body = error_details(error)
    details = body.get("details", [])
    violations, delays = [], []
    for detail in details if isinstance(details, list) else []:
        if not isinstance(detail, dict):
            continue
        violations.extend(detail.get("violations", []))
        value = detail.get("retryDelay")
        try:
            delay = (float(value.get("seconds", 0)) + float(value.get("nanos", 0)) / 1e9
                     if isinstance(value, dict) else float(str(value).removesuffix("s")))
            delays.append(delay)
        except (TypeError, ValueError):
            pass
    headers = getattr(getattr(error, "response", None), "headers", {}) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    if value:
        try:
            delays.append(float(value))
        except (TypeError, ValueError):
            try:
                delays.append(parsedate_to_datetime(value).timestamp() - time.time())
            except (TypeError, ValueError, OverflowError):
                pass
    match = re.search(r"retry in\s+([\d.]+)s", body.get("message", ""), re.IGNORECASE)
    if match:
        delays.append(float(match.group(1)))
    terminal = body.get("code") in ("insufficient_quota", "billing_hard_limit_reached") or any(
        "perday" in v.get("quotaId", "").lower() or str(v.get("quotaValue")) == "0"
        for v in violations)
    return violations, max([0.0, *delays]), terminal


def transient_retry(function, limiter=None, tokens=0, requests=1):
    import httpx
    from openai import APIConnectionError, APITimeoutError

    started = time.monotonic()
    for attempt in range(20):
        if limiter is not None:
            limiter.acquire(tokens, requests)
        try:
            return function()
        except Exception as error:
            status = error_status(error)
            retryable = status in (408, 429, 500, 502, 503, 504) or isinstance(
                error, (TimeoutError, ConnectionError, httpx.TransportError, APIConnectionError, APITimeoutError))
            violations, requested_delay, terminal = quota_details(error)
            if not retryable or terminal or attempt >= (19 if status == 429 else 5):
                raise
            delay = random.uniform(1, min(40, 2 ** (attempt + 1)))
            delay = max(delay, requested_delay + .5 if requested_delay else 0)
            if time.monotonic() - started + delay > 900:
                raise
            if limiter is not None:
                if status == 429:
                    limiter.learn(violations)
                limiter.defer(delay)
            else:
                time.sleep(delay)
