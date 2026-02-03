'use client'

import { useState } from 'react'

interface CheckoutButtonsProps {
    monthlyPriceId: string
    yearlyPriceId: string
}

export default function CheckoutButtons({ monthlyPriceId, yearlyPriceId }: CheckoutButtonsProps) {
    const [loading, setLoading] = useState<string | null>(null)

    const handleCheckout = async (priceId: string) => {
        try {
            setLoading(priceId)
            const response = await fetch('/api/stripe/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ priceId }),
            })

            if (!response.ok) {
                const err = await response.json()
                throw new Error(err.error || 'Failed to checkout')
            }

            const data = await response.json()
            if (data.url) {
                window.location.href = data.url
            } else {
                throw new Error('No checkout URL returned')
            }
        } catch (error: any) {
            console.error('Checkout error:', error)
            alert(`Error: ${error.message || 'Unknown error'}. Please check console for details.`)
        } finally {
            setLoading(null)
        }
    }

    return (
        <div className="space-y-3">
            <button
                onClick={() => handleCheckout(monthlyPriceId)}
                disabled={loading === monthlyPriceId}
                className="w-full block text-center py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold uppercase tracking-wide transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-wait"
            >
                {loading === monthlyPriceId ? 'Loading...' : 'Unlock Monthly ($29)'}
            </button>
            <button
                onClick={() => handleCheckout(yearlyPriceId)}
                disabled={loading === yearlyPriceId}
                className="w-full block text-center py-3 rounded-lg border border-emerald-600/30 text-emerald-400 hover:bg-emerald-600/10 font-bold uppercase tracking-wide transition-all text-xs disabled:opacity-50 disabled:cursor-wait"
            >
                {loading === yearlyPriceId ? 'Loading...' : 'Unlock Yearly ($290) - Save 17%'}
            </button>
        </div>
    )
}
