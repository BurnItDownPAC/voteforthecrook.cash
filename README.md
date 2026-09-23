# Vote For The Crook - Stripe Merch Store

This is a static storefront that uses Stripe Payment Links for checkout.

## 1) Add product images

Place your product images at:

- `assets/tshirt.png`
- `assets/hat.png`
- `assets/mug.png`

Recommended: around 1200px wide, JPG or PNG.

## 2) Create Stripe Payment Link

In Stripe Dashboard:

1. Go to **Payments > Payment Links**
2. Click **Create payment link**
3. Create/select each product in Stripe
4. Set price, shipping options, and tax settings
5. Copy each generated Payment Link URL

## 3) Paste your Stripe links

Open `index.html` and replace these:

- `https://buy.stripe.com/REPLACE_TSHIRT_PAYMENT_LINK`
- `https://buy.stripe.com/REPLACE_HAT_PAYMENT_LINK`
- `https://buy.stripe.com/REPLACE_MUG_PAYMENT_LINK`

with your real Stripe URLs.

## 4) Customize product details

In `index.html`, update:

- Product names and prices
- Product details text
- Shipping and returns policy copy

## 5) Run locally

Open `index.html` in your browser, or use a simple static server.

Landing page:

- `landing.html` is a focused campaign page with a single main CTA.
- Keep `index.html` as the full store page.
- If you want landing as homepage, rename `landing.html` to `index.html` and move the current store page to `shop.html`.

## 6) Deploy on Vercel

Dashboard method:

1. Go to https://vercel.com/new
2. Import your Git repo (or push this folder to GitHub first)
3. Vercel auto-detects it as a static site
4. Click Deploy

CLI method:

1. Install CLI: `npm i -g vercel`
2. From this folder, run: `vercel`
3. Follow the prompts once
4. For production deploys, run: `vercel --prod`

No build step is required for this project.

## 7) Connect custom domain (voteforthecrook.cash)

Do this after your first Vercel deploy succeeds.

In Vercel:

1. Open your project
2. Go to Settings > Domains
3. Add:
	- voteforthecrook.cash
	- www.voteforthecrook.cash

In Cloudflare DNS (zone: voteforthecrook.cash):

1. Remove conflicting records for @ or www (old A/AAAA/CNAME pointing elsewhere)
2. Add A record:
	- Type: A
	- Name: @
	- IPv4 address: 76.76.21.21
	- Proxy status: DNS only (gray cloud)
3. Add CNAME record:
	- Type: CNAME
	- Name: www
	- Target: cname.vercel-dns.com
	- Proxy status: DNS only (gray cloud)

Then back in Vercel:

1. Wait for verification (usually a few minutes)
2. Set voteforthecrook.cash as Primary
3. Enable redirect from www to apex (or vice versa, your choice)

Notes:

- If Cloudflare proxy is orange-cloud during setup, SSL verification can fail. Keep DNS only until Vercel shows domain as Valid.
- If you still see Invalid Configuration in Vercel, check for leftover AAAA records at @.

## 8) Other cheap hosts

Good low-cost hosts for static sites:

- Cloudflare Pages (often free tier is enough)
- Vercel (free tier)
- GitHub Pages (free)

You only pay Stripe transaction fees when people buy.

## 9) Vercel production hardening

This project includes `vercel.json` with:

- Redirect from `www.voteforthecrook.cash` to `voteforthecrook.cash`
- Security headers (HSTS, CSP, frame protection, MIME sniff protection)

After deploy, verify:

1. `https://www.voteforthecrook.cash` redirects to `https://voteforthecrook.cash`
2. Page source includes canonical URL `https://voteforthecrook.cash/`
3. Social preview tags are present (Open Graph and Twitter)

Optional checks:

- Run `curl -I https://voteforthecrook.cash` and confirm headers like `content-security-policy` and `strict-transport-security`.

## 10) 24/7 domain watcher (runs in GitHub, not on your laptop)

This repo now includes a scheduled workflow:

- `.github/workflows/domain-watch.yml`

What it does:

1. Runs every 30 minutes in GitHub Actions.
2. Checks WHOIS status for `cleofields.com`.
3. Creates/updates an issue named `Domain Watch: cleofields.com`.
4. Posts a comment when status changes.
5. Posts an alert comment when status reaches `pendingDelete` or `available`.

How to use:

1. Push this repository to GitHub.
2. Open the **Actions** tab and enable workflows if prompted.
3. Run **Domain Watch** once manually from **Run workflow** to initialize tracking.
4. Watch the issue `Domain Watch: cleofields.com` for updates.

To monitor a different domain:

- Use **Run workflow** and set the `domain` input.
