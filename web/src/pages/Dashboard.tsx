import React from 'react';
import { Chart } from '../components/Chart';
import { useMarketData } from '../hooks/useMarketData';
import { HealthStatus } from '../components/HealthStatus';

export const Dashboard: React.FC = () => {
    const { data, isHealthy, currentPrice } = useMarketData();
    const latestData = data.length > 0 ? data[data.length - 1] : null;

    return (
        <main className="min-h-screen bg-surface flex flex-col font-body antialiased overflow-x-hidden">
            {/* Top Bar */}
            <header className="h-14 flex justify-between items-center px-6 bg-[#0f231e] py-2 border-b border-outline-variant/10">
                <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-3 mr-2">
                            <div className="w-7 h-7 bg-secondary rounded-sm flex items-center justify-center">
                                <span className="material-symbols-outlined text-on-secondary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>token</span>
                            </div>
                            <h1 className="font-headline font-black text-secondary tracking-widest text-base hidden md:block uppercase">KINETIC</h1>
                        </div>
                        <div className="flex items-center"><span className="font-headline font-black text-on-background text-lg tracking-tight uppercase">EUR / USD</span></div>
                        <HealthStatus isHealthy={isHealthy} />
                    </div>
                    <div className="flex space-x-6">
                        <div className="flex flex-col">
                            <span className="text-[9px] text-outline uppercase tracking-wider">Price</span>
                            <span className="text-xs font-medium font-label">{currentPrice?.toFixed(5) || '1.08424'}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[9px] text-outline uppercase tracking-wider">Change</span>
                            <span className="text-xs font-medium font-label text-secondary">+0.0024 (0.22%)</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <div className="flex items-center bg-surface-container px-3 py-1 rounded-md">
                        <span className="material-symbols-outlined text-outline text-base mr-2" data-icon="search">search</span>
                        <input className="bg-transparent border-none focus:ring-0 text-xs text-primary p-0 w-40" placeholder="Search instruments..." type="text"/>
                    </div>
                    <div className="flex items-center space-x-3">
                        <button className="text-outline hover:text-primary transition-colors">
                            <span className="material-symbols-outlined text-xl" data-icon="notifications">notifications</span>
                        </button>
                        <button className="text-outline hover:text-primary transition-colors">
                            <span className="material-symbols-outlined text-xl" data-icon="settings">settings</span>
                        </button>
                        <button className="bg-secondary text-on-secondary px-4 py-1.5 rounded-md font-headline font-bold text-[10px] uppercase tracking-widest transition-transform active:scale-95">
                            Trade Now
                        </button>
                    </div>
                </div>
            </header>

            {/* Dashboard Body */}
            <div className="p-6 flex-initial flex flex-col space-y-6">
                {/* Hero Grid: Chart & Data */}
                <div className="grid grid-cols-12 gap-6 items-start">
                    {/* Main Candlestick Chart Module */}
                    <div className="col-span-12 lg:col-span-9 flex flex-col space-y-6">
                        <div className="bg-surface-container rounded-lg overflow-hidden flex flex-col shadow-2xl">
                            <div className="px-5 py-3 flex justify-between items-center border-b border-outline-variant/10">
                                <div className="flex space-x-1">
                                    {/* Timeframe Selectors */}
                                    <button className="px-2 py-1 text-[10px] font-bold text-secondary bg-secondary/10 rounded transition-colors">1m</button>
                                    <button className="px-2 py-1 text-[10px] font-bold text-outline hover:bg-surface-container-high rounded transition-colors">5m</button>
                                    <button className="px-2 py-1 text-[10px] font-bold text-outline hover:bg-surface-container-high rounded transition-colors">15m</button>
                                    <button className="px-2 py-1 text-[10px] font-bold text-outline hover:bg-surface-container-high rounded transition-colors">1h</button>
                                    <button className="px-2 py-1 text-[10px] font-bold text-outline hover:bg-surface-container-high rounded transition-colors">4h</button>
                                    <button className="px-2 py-1 text-[10px] font-bold text-outline hover:bg-surface-container-high rounded transition-colors">D</button>
                                    <button className="px-2 py-1 text-[10px] font-bold text-outline hover:bg-surface-container-high rounded transition-colors">W</button>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <span className="material-symbols-outlined text-outline cursor-pointer hover:text-primary transition-colors text-lg" data-icon="photo_camera">photo_camera</span>
                                    <span className="material-symbols-outlined text-outline cursor-pointer hover:text-primary transition-colors text-lg" data-icon="fullscreen">fullscreen</span>
                                </div>
                            </div>
                            <div className="relative h-[420px] w-full p-4">
                                <Chart data={data} />
                                {!isHealthy && (
                                    <div className="absolute inset-0 bg-surface-container-highest/60 backdrop-blur-sm m-4 z-10 flex flex-col items-center justify-center rounded">
                                        <div className="bg-surface-container border border-tertiary/30 px-6 py-4 rounded-lg shadow-xl flex flex-col justify-center items-center gap-3">
                                            <span className="material-symbols-outlined text-tertiary text-3xl animate-pulse">cloud_off</span>
                                            <h2 className="text-tertiary font-headline font-bold uppercase tracking-widest text-lg">Connection Lost</h2>
                                            <p className="text-outline font-label text-xs max-w-[250px] text-center">Synchronizing with the neural engine. Retrying connection...</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="px-6 py-4 bg-surface-container-high grid grid-cols-5 gap-4">
                                <div className="flex flex-col">
                                    <span className="text-[9px] text-outline uppercase tracking-widest font-headline">Open</span>
                                    <span className="text-base font-label font-bold text-primary">{latestData?.open.toFixed(5) || '1.08182'}</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-[9px] text-outline uppercase tracking-widest font-headline">High</span>
                                    <span className="text-base font-label font-bold text-secondary">{latestData?.high.toFixed(5) || '1.08550'}</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-[9px] text-outline uppercase tracking-widest font-headline">Low</span>
                                    <span className="text-base font-label font-bold text-tertiary">{latestData?.low.toFixed(5) || '1.08110'}</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-[9px] text-outline uppercase tracking-widest font-headline">Close</span>
                                    <span className="text-base font-label font-bold text-primary">{latestData?.close.toFixed(5) || '1.08424'}</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-[9px] text-outline uppercase tracking-widest font-headline">Volume</span>
                                    <span className="text-base font-label font-bold text-primary">{latestData ? (latestData.volume / 1000).toFixed(1) + 'K' : '42.8K'}</span>
                                </div>
                            </div>
                        </div>

                        {/* Current Trade Entries Table */}
                        <div className="bg-surface-container rounded-lg overflow-hidden flex flex-col shadow-xl">
                            <div className="px-5 py-3 flex justify-between items-center border-b border-outline-variant/10 bg-surface-container">
                                <h3 className="font-headline text-[10px] font-black uppercase tracking-[0.2em] text-outline">Current Trade Entries</h3>
                                <div className="flex items-center space-x-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
                                    <span className="text-[9px] text-secondary font-bold uppercase tracking-wider">Live Positions</span>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left table-auto">
                                    <thead className="bg-surface-container-high z-10">
                                        <tr>
                                            <th className="px-5 py-3 text-[9px] font-bold text-outline uppercase tracking-wider">Entry ID</th>
                                            <th className="px-5 py-3 text-[9px] font-bold text-outline uppercase tracking-wider">Pair</th>
                                            <th className="px-5 py-3 text-[9px] font-bold text-outline uppercase tracking-wider">Entry Price</th>
                                            <th className="px-5 py-3 text-[9px] font-bold text-outline uppercase tracking-wider">Current Price</th>
                                            <th className="px-5 py-3 text-[9px] font-bold text-outline uppercase tracking-wider">Profit/Loss</th>
                                            <th className="px-5 py-3 text-[9px] font-bold text-outline uppercase tracking-wider text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-outline-variant/5">
                                        <tr className="hover:bg-surface-container-high/50 transition-colors group">
                                            <td className="px-5 py-3 text-xs font-label font-medium text-primary">#K7291-B</td>
                                            <td className="px-5 py-3 text-xs font-bold font-headline text-on-background">EUR / USD</td>
                                            <td className="px-5 py-3 text-xs font-label text-outline">1.08182</td>
                                            <td className="px-5 py-3 text-xs font-label text-primary">1.08424</td>
                                            <td className="px-5 py-3 text-xs font-bold font-label text-secondary">+24.2 PIPS</td>
                                            <td className="px-5 py-3 text-right">
                                                <button className="bg-tertiary/10 hover:bg-tertiary text-tertiary hover:text-on-tertiary px-3 py-1 rounded text-[9px] font-bold uppercase tracking-widest transition-all">Close Trade</button>
                                            </td>
                                        </tr>
                                        <tr className="hover:bg-surface-container-high/50 transition-colors group">
                                            <td className="px-5 py-3 text-xs font-label font-medium text-primary">#K7295-S</td>
                                            <td className="px-5 py-3 text-xs font-bold font-headline text-on-background">GBP / JPY</td>
                                            <td className="px-5 py-3 text-xs font-label text-outline">188.420</td>
                                            <td className="px-5 py-3 text-xs font-label text-primary">188.150</td>
                                            <td className="px-5 py-3 text-xs font-bold font-label text-secondary">+27.0 PIPS</td>
                                            <td className="px-5 py-3 text-right">
                                                <button className="bg-tertiary/10 hover:bg-tertiary text-tertiary hover:text-on-tertiary px-3 py-1 rounded text-[9px] font-bold uppercase tracking-widest transition-all">Close Trade</button>
                                            </td>
                                        </tr>
                                        <tr className="hover:bg-surface-container-high/50 transition-colors group">
                                            <td className="px-5 py-3 text-xs font-label font-medium text-primary">#K7301-B</td>
                                            <td className="px-5 py-3 text-xs font-bold font-headline text-on-background">BTC / USD</td>
                                            <td className="px-5 py-3 text-xs font-label text-outline">64,250.00</td>
                                            <td className="px-5 py-3 text-xs font-label text-primary">64,120.50</td>
                                            <td className="px-5 py-3 text-xs font-bold font-label text-tertiary">-129.50 USD</td>
                                            <td className="px-5 py-3 text-right">
                                                <button className="bg-tertiary/10 hover:bg-tertiary text-tertiary hover:text-on-tertiary px-3 py-1 rounded text-[9px] font-bold uppercase tracking-widest transition-all">Close Trade</button>
                                            </td>
                                        </tr>
                                        <tr className="hover:bg-surface-container-high/50 transition-colors group">
                                            <td className="px-5 py-3 text-xs font-label font-medium text-primary">#K7304-B</td>
                                            <td className="px-5 py-3 text-xs font-bold font-headline text-on-background">XAU / USD</td>
                                            <td className="px-5 py-3 text-xs font-label text-outline">2,024.15</td>
                                            <td className="px-5 py-3 text-xs font-label text-primary">2,026.88</td>
                                            <td className="px-5 py-3 text-xs font-bold font-label text-secondary">+2.73 USD</td>
                                            <td className="px-5 py-3 text-right">
                                                <button className="bg-tertiary/10 hover:bg-tertiary text-tertiary hover:text-on-tertiary px-3 py-1 rounded text-[9px] font-bold uppercase tracking-widest transition-all">Close Trade</button>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Side Module: Market Prediction & Execution */}
                    <div className="col-span-12 lg:col-span-3 flex flex-col space-y-6">
                        {/* Market Prediction */}
                        <div className="bg-surface-container rounded-lg p-5 shadow-xl border-l-2 border-secondary/30">
                            <h3 className="font-headline text-xs font-black uppercase tracking-[0.2em] mb-5 flex items-center">
                                Market Prediction
                                <div className="ml-auto flex space-x-1">
                                    <div className="w-1 h-1 rounded-full bg-secondary animate-pulse"></div>
                                    <div className="w-1 h-1 rounded-full bg-secondary/40"></div>
                                    <div className="w-1 h-1 rounded-full bg-secondary/20"></div>
                                </div>
                            </h3>
                            <div className="space-y-3">
                                {/* Buy Box */}
                                <div className="group bg-surface-container-low p-4 rounded border-l-4 border-secondary hover:bg-secondary/5 transition-all cursor-pointer">
                                    <div className="flex justify-between items-end">
                                        <div className="flex flex-col">
                                            <span className="text-[9px] text-outline uppercase tracking-widest mb-0.5">Buy Prediction</span>
                                            <span className="text-xl font-headline font-extrabold text-secondary">65%</span>
                                        </div>
                                        <span className="material-symbols-outlined text-secondary opacity-20 group-hover:opacity-100 transition-opacity text-lg" data-icon="trending_up">trending_up</span>
                                    </div>
                                    <div className="mt-2 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                                        <div className="h-full bg-secondary" style={{ width: "65%" }}></div>
                                    </div>
                                </div>
                                {/* Hold Box */}
                                <div className="group bg-surface-container-low p-4 rounded border-l-4 border-outline hover:bg-outline/5 transition-all cursor-pointer">
                                    <div className="flex justify-between items-end">
                                        <div className="flex flex-col">
                                            <span className="text-[9px] text-outline uppercase tracking-widest mb-0.5">Hold Neutral</span>
                                            <span className="text-xl font-headline font-extrabold text-outline">10%</span>
                                        </div>
                                        <span className="material-symbols-outlined text-outline opacity-20 group-hover:opacity-100 transition-opacity text-lg" data-icon="horizontal_rule">horizontal_rule</span>
                                    </div>
                                    <div className="mt-2 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                                        <div className="h-full bg-outline" style={{ width: "10%" }}></div>
                                    </div>
                                </div>
                                {/* Sell Box */}
                                <div className="group bg-surface-container-low p-4 rounded border-l-4 border-tertiary hover:bg-tertiary/5 transition-all cursor-pointer">
                                    <div className="flex justify-between items-end">
                                        <div className="flex flex-col">
                                            <span className="text-[9px] text-outline uppercase tracking-widest mb-0.5">Sell Prediction</span>
                                            <span className="text-xl font-headline font-extrabold text-tertiary">25%</span>
                                        </div>
                                        <span className="material-symbols-outlined text-tertiary opacity-20 group-hover:opacity-100 transition-opacity text-lg" data-icon="trending_down">trending_down</span>
                                    </div>
                                    <div className="mt-2 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                                        <div className="h-full bg-tertiary" style={{ width: "25%" }}></div>
                                    </div>
                                </div>
                            </div>
                            <div className="mt-5 pt-4 border-t border-outline-variant/10">
                                <p className="text-[9px] text-outline leading-relaxed italic">
                                    Institutional analysis suggests a strong bullish momentum sustained by recent ECB projections.
                                </p>
                            </div>
                        </div>

                        {/* Trade Controls Section (Aeon Ledger Style) */}
                        <div className="bg-surface-container rounded-lg p-5 shadow-xl border-l-2 border-primary/30">
                            <h3 className="font-headline text-[10px] font-black uppercase tracking-[0.2em] mb-5 text-outline">Trade Controls</h3>
                            <div className="space-y-4">
                                {/* Stop Loss Row */}
                                <div className="flex flex-col space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-[9px] text-outline uppercase tracking-widest font-bold">Stop Loss</span>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input className="sr-only peer custom-toggle" type="checkbox"/>
                                            <div className="w-7 h-3.5 bg-surface-container-highest rounded-full peer-checked:bg-secondary/20 transition-all"></div>
                                            <div className="absolute left-0.5 top-0.5 w-2.5 h-2.5 bg-outline rounded-full transition-all toggle-dot"></div>
                                        </label>
                                    </div>
                                    <div className="flex space-x-2">
                                        <input className="flex-1 bg-surface-container-low border border-outline-variant/20 rounded-sm px-2 py-1.5 text-xs font-label text-primary focus:ring-1 focus:ring-secondary focus:border-secondary outline-none transition-all" placeholder="0.0000" type="number"/>
                                        <div className="relative inline-block w-20">
                                            <select className="appearance-none w-full bg-surface-container-low border border-outline-variant/20 rounded-sm px-2 py-1.5 text-[10px] font-bold text-outline uppercase focus:ring-1 focus:ring-secondary outline-none cursor-pointer">
                                                <option>Price</option>
                                                <option>%</option>
                                            </select>
                                            <span className="material-symbols-outlined absolute right-1 top-1.5 text-xs pointer-events-none text-outline">expand_more</span>
                                        </div>
                                    </div>
                                </div>
                                {/* Take Profit Row */}
                                <div className="flex flex-col space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-[9px] text-outline uppercase tracking-widest font-bold">Take Profit</span>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input defaultChecked className="sr-only peer custom-toggle" type="checkbox"/>
                                            <div className="w-7 h-3.5 bg-surface-container-highest rounded-full peer-checked:bg-secondary/20 transition-all"></div>
                                            <div className="absolute left-0.5 top-0.5 w-2.5 h-2.5 bg-outline rounded-full transition-all toggle-dot"></div>
                                        </label>
                                    </div>
                                    <div className="flex space-x-2">
                                        <input className="flex-1 bg-surface-container-low border border-outline-variant/20 rounded-sm px-2 py-1.5 text-xs font-label text-primary focus:ring-1 focus:ring-secondary focus:border-secondary outline-none transition-all" placeholder="0.0000" type="number" defaultValue="1.09200"/>
                                        <div className="relative inline-block w-20">
                                            <select className="appearance-none w-full bg-surface-container-low border border-outline-variant/20 rounded-sm px-2 py-1.5 text-[10px] font-bold text-outline uppercase focus:ring-1 focus:ring-secondary outline-none cursor-pointer">
                                                <option>Price</option>
                                                <option>%</option>
                                            </select>
                                            <span className="material-symbols-outlined absolute right-1 top-1.5 text-xs pointer-events-none text-outline">expand_more</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Quick Execution */}
                        <div className="bg-surface-container rounded-lg p-5 flex flex-col">
                            <div className="space-y-4">
                                <h3 className="font-headline text-[10px] font-black uppercase tracking-[0.2em] text-outline">Quick Execution</h3>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="bg-surface-container-high p-3 rounded text-center border-b-2 border-transparent hover:border-secondary transition-all cursor-pointer">
                                        <span className="block text-[9px] text-outline uppercase mb-0.5">Buy</span>
                                        <span className="block text-xs font-bold font-label">1.08425</span>
                                    </div>
                                    <div className="bg-surface-container-high p-3 rounded text-center border-b-2 border-transparent hover:border-tertiary transition-all cursor-pointer">
                                        <span className="block text-[9px] text-outline uppercase mb-0.5">Sell</span>
                                        <span className="block text-xs font-bold font-label">1.08423</span>
                                    </div>
                                </div>
                            </div>
                            <div className="mt-6">
                                <div className="flex justify-between text-[9px] uppercase tracking-widest text-outline mb-1.5">
                                    <span>Risk Level</span>
                                    <span className="text-secondary">Low</span>
                                </div>
                                <div className="h-1 bg-surface-container-highest rounded-full flex overflow-hidden">
                                    <div className="h-full bg-secondary" style={{ width: "30%" }}></div>
                                    <div className="h-full bg-outline-variant" style={{ width: "70%" }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
};
