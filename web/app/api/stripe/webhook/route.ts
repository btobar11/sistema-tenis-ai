
import Stripe from 'stripe'
import { headers } from 'next/headers'
import { createAdminClient } from '@/utils/supabase/admin'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: Request) {
    const body = await req.text()
    const sig = (await headers()).get('stripe-signature')!

    let event
    try {
        event = stripe.webhooks.constructEvent(
            body,
            sig,
            process.env.STRIPE_WEBHOOK_SECRET!
        )
    } catch (err: any) {
        console.error(`Webhook Error: ${err.message} `)
        return new Response(`Webhook Error: ${err.message} `, { status: 400 })
    }

    const supabase = createAdminClient()

    if (event.type === 'checkout.session.completed') {
        const session = event.data.object as Stripe.Checkout.Session
        // User implied client_reference_id is user.id, but code uses metadata.user_id
        // We support both for robustness
        const userId = session.metadata?.user_id || session.client_reference_id
        const customerId = session.customer as string
        const plan = session.metadata?.plan || 'pro' // Default to pro if missing

        if (userId) {
            await supabase
                .from('profiles')
                .update({
                    subscription_status: 'active',
                    plan: plan,
                    stripe_customer_id: customerId,
                    updated_at: new Date().toISOString()
                })
                .eq('id', userId)
        }
    }

    if (event.type === 'customer.subscription.deleted') {
        const sub = event.data.object as Stripe.Subscription
        const customerId = sub.customer as string

        await supabase
            .from('profiles')
            .update({
                subscription_status: 'canceled',
                plan: 'free',
                updated_at: new Date().toISOString()
            })
            .eq('stripe_customer_id', customerId)
    }

    return new Response('ok')
}
