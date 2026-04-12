import React, { useRef, useEffect } from 'react';
import { createChart } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import type { OHLCVData } from '../hooks/useMarketData';

interface ChartProps {
    data: OHLCVData[];
}

/**
 * Renders a lightweight candlestick chart with design system colors.
 */
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
                textColor: '#767575', // outline
                fontSize: 10,
                fontFamily: 'Inter, sans-serif',
            },
            grid: {
                vertLines: { color: 'rgba(72, 72, 72, 0.1)' }, // outline-variant at 10%
                horzLines: { color: 'rgba(72, 72, 72, 0.1)' },
            },
            crosshair: {
                vertLine: { color: '#c6c6c7', width: 1, style: 2 }, // primary
                horzLine: { color: '#c6c6c7', width: 1, style: 2 },
            },
            rightPriceScale: {
                borderColor: 'rgba(72, 72, 72, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(72, 72, 72, 0.1)',
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
        });

        chartRef.current = chart;

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#00fdc1', // secondary
            downColor: '#ff6e86', // tertiary
            borderVisible: false,
            wickUpColor: '#00fdc1',
            wickDownColor: '#ff6e86',
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

            formattedData.sort((a, b) => (a.time as number) - (b.time as number));

            // Filter unique times to avoid lightweight-charts errors
            const uniqueData = formattedData.filter((item, index, self) =>
                index === self.findIndex((t) => t.time === item.time)
            );

            seriesRef.current.setData(uniqueData);
        }
    }, [data]);

    return (
        <div ref={chartContainerRef} className="absolute inset-0 bg-[#0e0e0e]" />
    );
};
