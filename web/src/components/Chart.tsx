import React, { useRef, useEffect } from 'react';
import { createChart } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import type { OHLCVData } from '../hooks/useMarketData';

interface ChartProps {
    data: OHLCVData[];
}

export const Chart: React.FC<ChartProps> = ({ data }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { color: 'transparent' },
                textColor: '#d1d5db',
            },
            grid: {
                vertLines: { color: '#1f2937' },
                horzLines: { color: '#1f2937' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
        });

        chartRef.current = chart;

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        seriesRef.current = candlestickSeries;

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, []);

    useEffect(() => {
        if (seriesRef.current && data.length > 0) {
            const formattedData: CandlestickData<Time>[] = data.map(item => {
                // Ensure time is in seconds for lightweight-charts
                let timeValue: Time;
                if (typeof item.time === 'string') {
                    timeValue = Math.floor(new Date(item.time).getTime() / 1000) as Time;
                } else if (item.time > 10000000000) {
                    timeValue = Math.floor(item.time / 1000) as Time;
                } else {
                    timeValue = item.time as Time;
                }

                return {
                    time: timeValue,
                    open: item.open,
                    high: item.high,
                    low: item.low,
                    close: item.close,
                };
            });
            
            // Sort by time
            formattedData.sort((a, b) => (a.time as number) - (b.time as number));
            
            seriesRef.current.setData(formattedData);
        }
    }, [data]);

    return (
        <div ref={chartContainerRef} className="absolute inset-0 m-4 bg-[#0e0e0e] rounded overflow-hidden" />
    );
};
