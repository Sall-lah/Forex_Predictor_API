import React, { useRef, useEffect } from 'react';

export const Chart: React.FC = () => {
    const chartContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // lightweight-charts will be initialized here later
    }, []);

    return (
        <div ref={chartContainerRef} className="absolute inset-0 m-4 bg-[#0e0e0e] rounded overflow-hidden" />
    );
};
