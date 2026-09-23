import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { MonthlySpending } from '../../types/dashboard';
import { formatCurrency } from '../../utils/formatters';

interface MonthlyTrendChartProps {
  data: MonthlySpending[];
}

export default function MonthlyTrendChart({ data }: MonthlyTrendChartProps) {
  if (data.length === 0) {
    return <p className="text-sm text-gray-500">No hay datos de tendencia mensual.</p>;
  }

  const chartData = data.map((d) => ({
    month: d.month,
    total_amount: d.total_amount,
    invoice_count: d.invoice_count,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          formatter={(value, name) => [
            name === 'total_amount' ? formatCurrency(Number(value)) : value,
            name === 'total_amount' ? 'Total' : 'Cantidad',
          ]}
        />
        <Line
          type="monotone"
          dataKey="total_amount"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
