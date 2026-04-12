import React from 'react';

interface HealthStatusProps {
    isHealthy: boolean;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({ isHealthy }) => {
    if (isHealthy) {
        return (
            <span className="bg-secondary/10 text-secondary text-[9px] px-1.5 py-0.5 rounded-full font-bold">
                LIVE
            </span>
        );
    }

    return (
        <div className="relative group">
            <span className="bg-tertiary/10 text-tertiary text-[9px] px-1.5 py-0.5 rounded-full font-bold cursor-help border border-tertiary/20">
                DISCONNECTED
            </span>
            <div className="absolute left-0 mt-2 w-48 p-2 bg-surface-container-high border border-outline-variant/20 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
                <p className="text-[10px] text-on-background font-label">
                    Backend or Kraken connection lost. Reconnecting...
                </p>
            </div>
        </div>
    );
};
