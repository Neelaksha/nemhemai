// dashboard/Dashboard.tsx
import React from 'react';
import { StatsWidget } from './StatsWidget';
import { LineChartWidget } from './LineChartWidget';
import { BarChartWidget } from './BarChartWidget';
import { PieChartWidget } from './PieChartWidget';
import { summaryStats, timeSeriesData, salesByRegion, categoryData } from './mockData';
import { Calendar, Download, Filter, RefreshCw } from 'lucide-react';
import './dashboard.css';

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Business Overview</h1>
          <p className="text-zinc-400 mt-1">Real-time performance metrics and insights</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-md text-sm font-medium hover:bg-zinc-800 transition-colors">
            <Calendar size={16} />
            Jan 1, 2024 - Jul 31, 2024
          </button>
          <button className="p-2 bg-zinc-900 border border-zinc-800 rounded-md hover:bg-zinc-800 transition-colors">
            <Filter size={16} />
          </button>
          <button className="p-2 bg-zinc-900 border border-zinc-800 rounded-md hover:bg-zinc-800 transition-colors">
            <RefreshCw size={16} />
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-md text-sm font-semibold hover:bg-blue-500 transition-colors text-white shadow-lg shadow-blue-900/20">
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-row">
        {summaryStats.map((stat, i) => (
          <StatsWidget 
            key={i} 
            label={stat.label} 
            value={stat.value} 
            trend={stat.trend} 
            trendType={stat.trendType as 'up' | 'down'} 
          />
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LineChartWidget data={timeSeriesData} title="Revenue Growth" />
        </div>
        <div className="lg:col-span-1">
          <PieChartWidget data={categoryData} title="Traffic Source" />
        </div>
        <div className="lg:col-span-1">
          <BarChartWidget data={salesByRegion} title="Sales by Region" />
        </div>
        <div className="lg:col-span-2">
          <div className="dashboard-card h-full">
            <div className="card-title">Key Performance Indicators</div>
            <div className="space-y-4 mt-4">
              {[
                { name: 'Customer Satisfaction', value: 94, color: 'bg-emerald-500' },
                { name: 'Server Uptime', value: 99.9, color: 'bg-blue-500' },
                { name: 'Lead Conversion', value: 12.4, color: 'bg-amber-500' },
              ].map((kpi, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">{kpi.name}</span>
                    <span className="font-medium">{kpi.value}%</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2">
                    <div 
                      className={`${kpi.color} h-2 rounded-full transition-all duration-1000`} 
                      style={{ width: `${kpi.value}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
