# Vote For The Crook

Static storefront deployed on Vercel with Stripe-hosted checkout.

## Run locally

Install dependencies and start Vercel's local development server:

```sh
npm install
vercel dev
```

The local webhook route needs `STRIPE_WEBHOOK_SECRET` in `.env.local` if you want to test signed Stripe events locally. Never commit that file or the secret.

## Storefront

- `index.html` — homepage
- `tee.html` — tee details, size selector, and per-size checkout links
- `mug.html` — mug details and checkout link
- `thank-you.html` — post-payment confirmation page
- `api/stripe-webhook.js` — verifies and receives Stripe checkout events

## Stripe status

The storefront currently uses Stripe **sandbox** Payment Links. Sandbox payments cannot charge real cards.

Configured checkout behavior:

- Tee sizes S–3XL and mug are separate Stripe products
- Adjustable quantity from 1–10
- U.S. shipping addresses only
- $5.95 standard U.S. shipping
- Successful payments redirect to `/thank-you.html`
- The production webhook receives completed and asynchronous checkout results

The webhook signing secret is stored as the encrypted Vercel Production environment variable `STRIPE_WEBHOOK_SECRET`. Do not place it in HTML or commit it to Git.

The webhook currently validates and logs payment events. It does not yet submit orders to a printer, write to an order database, or send custom fulfillment email.

## Go live

Test-mode Stripe objects do not become live-mode objects automatically. Before accepting real payments:

1. Complete Stripe account activation and business verification.
2. Recreate the products, prices, shipping rate, Payment Links, and webhook in live mode.
3. Replace the sandbox checkout URLs in `tee.html` and `mug.html` with live URLs.
4. Replace the Vercel webhook secret with the live endpoint's signing secret.
5. Decide where sales tax must be collected before enabling Stripe Tax.
6. Make a small real purchase and confirm checkout, webhook delivery, refund, and fulfillment.

## Deploy

Deploy the current directory to production:

```sh
vercel --prod
```

The custom production domain is `https://voteforthecrook.cash`.

`vercel.json` contains the `www` redirect and security headers.

## Domain watcher

`.github/workflows/domain-watch.yml` checks the configured domain on a schedule and reports changes through a GitHub issue. It is separate from the storefront and checkout.

The default is `cleofields.com`, scheduled every 30 minutes (GitHub may delay scheduled runs). Both the workflow and local watcher use `scripts/domain_status.py` to query Verisign's registry RDAP service directly for .com/.net domains. Registrar referrals and free-text WHOIS messages are not used.

- A verified registry domain record means registered, including redemption/hold/pending-delete states.
- Only an HTTP 404 with an RDAP `errorCode` of 404 means no registry record (`available`). Confirm registration with a registrar before buying.
- Network errors, rate limits, redirects, and malformed responses fail the check without changing the last verified status or sending availability alerts.
- Alerts are posted when the state changes, not on every run. Email still depends on GitHub issue subscriptions and notification settings; no separate email sender is configured.
- Older WHOIS-based availability alerts may have been false positives and should not be used as current status.

Check once: `python3 scripts/domain_status.py cleofields.com`

Run regression tests: `python3 -B -m unittest discover -s scripts -p 'test_domain_status.py' -v`

Monitor locally: `bash scripts/watch-domain.sh cleofields.com 300`
