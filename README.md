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
