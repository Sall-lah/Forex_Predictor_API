import React, { useRef, useCallback } from 'react';
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
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const prevDataRef = useRef<OHLCVData[]>([]);

    const chartContainerRef = useCallback((node: HTMLDivElement | null) => {
        if (node !== null) {
            const handleResize = () => {
                if (node && chartRef.current) {
                    chartRef.current.applyOptions({ width: node.clientWidth });
                }
            };

            const chart = createChart(node, {
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
                width: node.clientWidth,
                height: node.clientHeight,
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

            // Re-apply data if we already had it before initialization
            if (prevDataRef.current.length > 0) {
                applyDataToSeries(prevDataRef.current, candlestickSeries);
            }
            
            // cleanup is attached to node so we can't easily return it from useCallback,
            // but we can store it on the element or cleanup when node is null
        } else {
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
                seriesRef.current = null;
            }
        }
    }, []);

    const applyDataToSeries = (chartData: OHLCVData[], series: ISeriesApi<"Candlestick">) => {
        const formattedData: CandlestickData<Time>[] = chartData.map(item => {
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

        series.setData(uniqueData);
    };

    if (data !== prevDataRef.current) {
        prevDataRef.current = data;
        if (seriesRef.current && data.length > 0) {
            applyDataToSeries(data, seriesRef.current);
        }
    }

    return (
        <div ref={chartContainerRef} className="absolute inset-0 bg-[#0e0e0e]" />
    );
};
