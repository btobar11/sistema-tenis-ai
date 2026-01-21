import React, { useState } from 'react';
import { Info } from 'lucide-react';

interface TooltipProps {
    content: string;
    children?: React.ReactNode;
}

export default function Tooltip({ content, children }: TooltipProps) {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div className="relative inline-block">
            <div
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                className="cursor-help inline-flex items-center"
            >
                {children || <Info className="w-4 h-4 text-slate-500 hover:text-emerald-400 transition-colors" />}
            </div>

            {isVisible && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 px-3 py-2 text-xs text-white bg-slate-800 rounded-lg shadow-xl border border-slate-700 pointer-events-none">
                    <div className="relative">
                        {content}
                        {/* Arrow */}
                        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
                            <div className="border-4 border-transparent border-t-slate-800"></div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
