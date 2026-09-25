#!/usr/bin/env python3
"""Check .com/.net registration at Verisign; never follow registrar referrals."""

import argparse
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class CheckError(Exception):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def registry_url(domain):
    domain = domain.lower().rstrip(".")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(com|net)", domain):
        raise CheckError("Only valid second-level .com and .net domains are supported.")
    return domain, f"https://rdap.verisign.com/{domain.rsplit('.', 1)[1]}/v1/domain/{domain}"


def classify(domain, code, payload):
    if not isinstance(payload, dict):
        raise CheckError("Registry did not return an RDAP object.")
    # Availability requires an explicit registry RDAP 404, not arbitrary text,
    # a registrar's response, a redirect, or a transport/service error.
    if code == 404 and payload.get("errorCode") == 404:
        if any(key in payload for key in ("ldhName", "handle", "status")):
            raise CheckError("Conflicting registration and error data.")
        return "available", []
    if code != 200 or "errorCode" in payload:
        raise CheckError(f"Registry lookup failed (HTTP {code}).")
    if (payload.get("objectClassName") != "domain"
            or str(payload.get("ldhName", "")).lower() != domain):
        raise CheckError("Registry returned an unexpected domain record.")
    statuses = payload.get("status", [])
    if not isinstance(statuses, list) or not all(isinstance(s, str) for s in statuses):
        raise CheckError("Invalid registry status data.")
    normalized = {s.replace(" ", "").lower() for s in statuses}
    # Redemption can coexist with pending-delete in some registry responses.
    for key, state in (("redemptionperiod", "redemptionPeriod"),
                       ("pendingdelete", "pendingDelete"),
                       ("clienthold", "clientHold")):
        if key in normalized:
            return state, sorted(statuses)
    return "registered", sorted(statuses)


def check_domain(domain):
    domain, url = registry_url(domain)
    request = Request(url, headers={"Accept": "application/rdap+json",
                                    "User-Agent": "DomainWatch/2.0"})
    try:
        try:
            response = build_opener(NoRedirects()).open(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            code = response.code
            content_type = response.headers.get_content_type()
            if content_type not in ("application/rdap+json", "application/json"):
                raise CheckError(f"Registry returned non-JSON data (HTTP {code}).")
            payload = json.load(response)
    except (URLError, OSError, ValueError) as error:
        raise CheckError(f"Registry lookup could not be verified: {error}") from error
    state, statuses = classify(domain, code, payload)
    return {"domain": domain, "state": state, "statuses": statuses, "source": url}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain")
    args = parser.parse_args()
    try:
        print(json.dumps(check_domain(args.domain)))
    except CheckError as error:
        print(f"Domain check failed; no availability conclusion: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
