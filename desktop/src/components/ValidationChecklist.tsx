import { CheckCircle2, XCircle } from 'lucide-react';

interface ValidationChecklistProps {
    playerName: string;
    metrics: any;
    ev: number;
}

interface CheckItem {
    label: string;
    passed: boolean;
    value: string;
    tooltip: string;
}

export default function ValidationChecklist({ playerName, metrics, ev }: ValidationChecklistProps) {
    // Evaluate each metric
    const checks: CheckItem[] = [
        {
            label: 'Form',
            passed: metrics.form > 70,
            value: `${metrics.form.toFixed(1)}%`,
            tooltip: 'Recent performance trend. ✅ if > 70%'
        },
        {
            label: 'Surface Win Rate',
            passed: metrics.surfaceWinRate > 60,
            value: `${metrics.surfaceWinRate.toFixed(1)}%`,
            tooltip: 'Win rate on this surface. ✅ if > 60%'
        },
        {
            label: 'Regularity',
            passed: metrics.regularity < 0.3,
            value: `CV: ${metrics.regularity.toFixed(2)}`,
            tooltip: 'Consistency (lower is better). ✅ if < 0.3'
        },
        {
            label: 'Set Trend',
            passed: metrics.setTrend > 0,
            value: metrics.setTrend > 0 ? 'Positive' : 'Negative',
            tooltip: 'Recent set performance trend. ✅ if positive'
        },
        {
            label: 'Value (EV)',
            passed: ev > 0,
            value: `${(ev * 100).toFixed(1)}%`,
            tooltip: 'Expected value. ✅ if > 0%'
        }
    ];

    const passedCount = checks.filter(c => c.passed).length;
    const totalCount = checks.length;
    const passRate = (passedCount / totalCount) * 100;

    // Determine overall rating
    let ratingColor = 'red';
    let ratingText = 'Weak';
    if (passRate >= 80) {
        ratingColor = 'emerald';
        ratingText = 'Strong';
    } else if (passRate >= 60) {
        ratingColor = 'yellow';
        ratingText = 'Moderate';
    }

    return (
        <div className={`p-5 rounded-xl border-2 ${ratingColor === 'emerald' ? 'bg-emerald-500/5 border-emerald-500/30' :
            ratingColor === 'yellow' ? 'bg-yellow-500/5 border-yellow-500/30' :
                'bg-red-500/5 border-red-500/30'
            }`}>
            {/* Header */}
            <div className="mb-4">
                <h4 className="font-bold text-white text-lg mb-1">{playerName}</h4>
                <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${ratingColor === 'emerald' ? 'text-emerald-400' :
                        ratingColor === 'yellow' ? 'text-yellow-400' :
                            'text-red-400'
                        }`}>
                        {ratingText} ({passedCount}/{totalCount})
                    </span>
                </div>
            </div>

            {/* Checks */}
            <div className="space-y-2">
                {checks.map((check, idx) => (
                    <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800"
                        title={check.tooltip}
                    >
                        <div className="flex items-center gap-2">
                            {check.passed ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : (
                                <XCircle className="w-4 h-4 text-red-400" />
                            )}
                            <span className="text-sm text-slate-300">{check.label}</span>
                        </div>
                        <span className={`text-sm font-medium ${check.passed ? 'text-emerald-400' : 'text-red-400'
                            }`}>
                            {check.value}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
