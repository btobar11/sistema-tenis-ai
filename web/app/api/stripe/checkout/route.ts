import Stripe from 'stripe'
import { createClient } from '@/utils/supabase/server'
import { NextResponse } from 'next/server'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()

        console.log('[Checkout API] Auth Check:', {
            userId: user?.id,
            email: user?.email,
            hasUser: !!user,
            authError: authError?.message
        })

        if (authError || !user) {
            console.warn('[Checkout API] Unauthorized request:', authError?.message)
            return NextResponse.json({ error: `Unauthorized: ${authError?.message || 'No active session'}` }, { status: 401 })
        }

        const { priceId } = await req.json()

        // Create or retrieve Stripe Customer
        let customerId
        const { data: profile } = await supabase
            .from('profiles')
            .select('stripe_customer_id')
            .eq('id', user.id)
            .single()

        if (profile?.stripe_customer_id) {
            customerId = profile.stripe_customer_id
        } else {
            console.log('[Checkout API] Creating new Stripe customer for:', user.email)
            const customer = await stripe.customers.create({
                email: user.email!,
                metadata: { supabase_id: user.id }
            })
            customerId = customer.id
            // Save customer ID to profile (optional optimization)
        }

        const session = await stripe.checkout.sessions.create({
            mode: 'subscription',
            payment_method_types: ['card'],
            customer: customerId,
            ...(customerId ? {} : { customer_email: user.email! }),
            line_items: [{ price: priceId, quantity: 1 }],
            success_url: `${process.env.NEXT_PUBLIC_SITE_URL}/daily-edge`,
            cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL}/pricing`,
            metadata: {
                user_id: user.id,
            },
        })

        return NextResponse.json({ url: session.url })

    } catch (error: any) {
        console.error('[Checkout API] CRITICAL ERROR:', error)
        return NextResponse.json({ error: `Server Error: ${error.message}` }, { status: 500 })
    }
}
