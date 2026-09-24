import Stripe from 'stripe';

// Signature verification does not make an API request, but the Stripe client
// requires a key at construction time. Checkout itself continues to use hosted
// Payment Links, so no Stripe API key is exposed to the storefront.
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_webhook_only');

function json(body, status = 200) {
  return Response.json(body, {
    status,
    headers: {
      'Cache-Control': 'no-store'
    }
  });
}

export function GET() {
  return json({
    ok: true,
    endpoint: 'Stripe webhook',
    configured: Boolean(process.env.STRIPE_WEBHOOK_SECRET)
  });
}

export async function POST(request) {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET?.trim();
  const signature = request.headers.get('stripe-signature');

  if (!webhookSecret) {
    console.error('Stripe webhook is missing STRIPE_WEBHOOK_SECRET.');
    return json({ error: 'Webhook is not configured.' }, 500);
  }

  if (!signature) {
    return json({ error: 'Missing Stripe signature.' }, 400);
  }

  const rawBody = await request.text();
  let event;

  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    console.error('Stripe webhook signature verification failed.');
    return json({ error: 'Invalid Stripe signature.' }, 400);
  }

  switch (event.type) {
    case 'checkout.session.completed':
    case 'checkout.session.async_payment_succeeded': {
      const session = event.data.object;
      console.info('Stripe checkout paid', {
        eventId: event.id,
        checkoutSessionId: session.id,
        paymentStatus: session.payment_status,
        amountTotal: session.amount_total,
        currency: session.currency,
        paymentLinkId: session.payment_link
      });
      break;
    }
    case 'checkout.session.async_payment_failed': {
      const session = event.data.object;
      console.warn('Stripe checkout payment failed', {
        eventId: event.id,
        checkoutSessionId: session.id,
        paymentLinkId: session.payment_link
      });
      break;
    }
    default:
      console.info('Stripe webhook received', {
        eventId: event.id,
        type: event.type
      });
  }

  return json({ received: true });
}
