import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface InvoiceTypeBreakdownProps {
  data: Record<string, number>;
}

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function InvoiceTypeBreakdown({ data }: InvoiceTypeBreakdownProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name: `Tipo ${name}`,
    value,
  }));

  if (chartData.length === 0 || chartData.every((d) => d.value === 0)) {
    return <p className="text-sm text-gray-500">No hay facturas clasificadas por tipo.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => [value, 'Facturas']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
