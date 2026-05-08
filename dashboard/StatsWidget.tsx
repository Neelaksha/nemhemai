// dashboard/StatsWidget.tsx
import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import './dashboard.css';

interface StatsWidgetProps {
  label: string;
  value: string;
  trend: string;
  trendType: 'up' | 'down';
}

export const StatsWidget: React.FC<StatsWidgetProps> = ({ label, value, trend, trendType }) => {
  return (
    <div className="dashboard-card">
      <div className="card-title">
        {label}
      </div>
      <div className="card-value">{value}</div>
      <div className={`card-trend ${trendType === 'up' ? 'trend-up' : 'trend-down'}`}>
        {trendType === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {trend}
        <span className="text-zinc-500 ml-1">vs last month</span>
      </div>
    </div>
  );
};
