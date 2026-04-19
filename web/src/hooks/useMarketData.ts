import useSWR from 'swr';

export interface OHLCVData {
    time: string | number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

const fetcher = async (url: string) => {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result = await response.json();
    
    const rawRecords = Array.isArray(result) ? result : (result.data || []);
    return rawRecords.map((record: any) => ({
        time: record.timestamp || record.time,
        open: record.open,
        high: record.high,
        low: record.low,
        close: record.close,
        volume: record.volume
    }));
};

export const useMarketData = (pair: string = 'BTC/USD', intervalMinutes: number = 60) => {
    const url = `/api/v1/historic-data/live?pair=${encodeURIComponent(pair)}&interval=${intervalMinutes}`;
    
    const { data: mappedRecords, error } = useSWR<OHLCVData[]>(url, fetcher, {
        refreshInterval: 15000,
    });

    const isHealthy = !error;
    let currentPrice: number | null = null;
    
    if (mappedRecords && mappedRecords.length > 0) {
        currentPrice = mappedRecords[mappedRecords.length - 1].close;
    }

    return { 
        data: mappedRecords || [], 
        error: error || null, 
        isHealthy, 
        currentPrice 
    };
};
