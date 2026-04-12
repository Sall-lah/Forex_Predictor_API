import { useState, useEffect } from 'react';

export interface OHLCVData {
    time: string | number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export const useMarketData = () => {
    const [data, setData] = useState<OHLCVData[]>([]);
    const [error, setError] = useState<Error | null>(null);
    const [isHealthy, setIsHealthy] = useState<boolean>(true);
    const [currentPrice, setCurrentPrice] = useState<number | null>(null);

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            try {
                // Vite proxy should route this to backend
                const response = await fetch('/api/v1/historic-data/live');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const result = await response.json();
                
                if (!isMounted) return;

                // Standardizing response payload assumption
                const records = Array.isArray(result) ? result : (result.data || []);
                
                setData(records);
                
                if (records.length > 0) {
                    const latest = records[records.length - 1];
                    setCurrentPrice(latest.close);
                }
                
                setIsHealthy(true);
                setError(null);
            } catch (err) {
                console.error("Market data fetch failed:", err);
                if (isMounted) {
                    setIsHealthy(false);
                    setError(err instanceof Error ? err : new Error('Unknown error'));
                }
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 2000); // 2 second polling

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    return { data, error, isHealthy, currentPrice };
};
