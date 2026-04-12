import { useState, useEffect } from 'react';

export interface OHLCVData {
    time: string | number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export const useMarketData = (pair: string = 'BTC/USD') => {
    const [data, setData] = useState<OHLCVData[]>([]);
    const [error, setError] = useState<Error | null>(null);
    const [isHealthy, setIsHealthy] = useState<boolean>(true);
    const [currentPrice, setCurrentPrice] = useState<number | null>(null);

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            try {
                // Vite proxy should route this to backend
                const response = await fetch('/api/v1/historic-data/live?pair=' + encodeURIComponent(pair));
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const result = await response.json();
                
                if (!isMounted) return;

                // Standardizing response payload assumption
                const rawRecords = Array.isArray(result) ? result : (result.data || []);
                const mappedRecords = rawRecords.map((record: any) => ({
                    time: record.timestamp || record.time,
                    open: record.open,
                    high: record.high,
                    low: record.low,
                    close: record.close,
                    volume: record.volume
                }));
                
                setData(mappedRecords);
                
                if (mappedRecords.length > 0) {
                    const latest = mappedRecords[mappedRecords.length - 1];
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
    }, [pair]);

    return { data, error, isHealthy, currentPrice };
};
