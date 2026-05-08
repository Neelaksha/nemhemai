// dashboard/mockData.ts

export const timeSeriesData = [
  { name: 'Jan', value: 4000, secondary: 2400 },
  { name: 'Feb', value: 3000, secondary: 1398 },
  { name: 'Mar', value: 2000, secondary: 9800 },
  { name: 'Apr', value: 2780, secondary: 3908 },
  { name: 'May', value: 1890, secondary: 4800 },
  { name: 'Jun', value: 2390, secondary: 3800 },
  { name: 'Jul', value: 3490, secondary: 4300 },
];

export const categoryData = [
  { name: 'Direct', value: 400, color: '#3b82f6' },
  { name: 'Social', value: 300, color: '#10b981' },
  { name: 'Referral', value: 300, color: '#f59e0b' },
  { name: 'Other', value: 200, color: '#8b5cf6' },
];

export const salesByRegion = [
  { region: 'North', sales: 4500 },
  { region: 'South', sales: 3200 },
  { region: 'East', sales: 2800 },
  { region: 'West', sales: 5100 },
  { region: 'Central', sales: 1900 },
];

export const summaryStats = [
  { label: 'Total Revenue', value: '$124,592', trend: '+12.5%', trendType: 'up' },
  { label: 'Active Users', value: '14,208', trend: '+5.2%', trendType: 'up' },
  { label: 'Churn Rate', value: '2.4%', trend: '-0.8%', trendType: 'up' }, // up trend is good for churn down
  { label: 'Avg Order Value', value: '$84.20', trend: '-2.1%', trendType: 'down' },
];
