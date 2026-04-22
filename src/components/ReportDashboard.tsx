import React from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  BarChart, Bar, Cell, AreaChart, Area
} from 'recharts';
import { 
  TrendingUp, Users, ShoppingCart, DollarSign, 
  ArrowUpRight, ArrowDownRight, Activity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface DashboardData {
  title: string;
  metrics: {
    total_revenue: number;
    total_orders: number;
    avg_order_value: number;
  };
  chart_data: Array<{
    period: string;
    revenue: number;
    [key: string]: any;
  }>;
  insights?: string;
}

const StatCard = ({ title, value, icon: Icon, trend, trendValue }: any) => (
  <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <h3 className="text-2xl font-bold text-white mt-1">{value}</h3>
          {trend && (
            <div className={`flex items-center mt-2 text-xs ${trend === 'up' ? 'text-emerald-400' : 'text-rose-400'}`}>
              {trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
              {trendValue} vs last period
            </div>
          )}
        </div>
        <div className="p-3 bg-emerald-500/10 rounded-xl">
          <Icon className="h-6 w-6 text-emerald-400" />
        </div>
      </div>
    </CardContent>
  </Card>
);

export const ReportDashboard: React.FC<{ data: DashboardData }> = ({ data }) => {
  const { metrics, chart_data, title, insights } = data;

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Activity className="h-5 w-5 text-emerald-400" />
          {title}
        </h2>
        <div className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
          Live Data
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard 
          title="Total Revenue" 
          value={`$${metrics.total_revenue.toLocaleString()}`} 
          icon={DollarSign}
          trend="up"
          trendValue="12.5%"
        />
        <StatCard 
          title="Total Orders" 
          value={metrics.total_orders.toString()} 
          icon={ShoppingCart}
          trend="up"
          trendValue="8%"
        />
        <StatCard 
          title="Avg Order Value" 
          value={`$${metrics.avg_order_value.toFixed(2)}`} 
          icon={TrendingUp}
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue Trend Chart */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-slate-300">Revenue Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chart_data}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="period" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                  itemStyle={{ color: '#10b981' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorRev)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Order Volume Chart */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-slate-300">Daily Volume</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="period" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <Tooltip 
                  cursor={{fill: '#1e293b'}}
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                />
                <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Insights Section */}
      {insights && (
        <Card className="bg-emerald-500/5 border-emerald-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              AI Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">
              {insights}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
