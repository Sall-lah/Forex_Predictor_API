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
        <span className="bg-tertiary/10 text-tertiary text-[9px] px-1.5 py-0.5 rounded-full font-bold cursor-help border border-tertiary/20" title="Backend or Kraken connection lost. Reconnecting and serving cached data.">
            DISCONNECTED
        </span>
    );
};
