import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';
import type { TopSupplier } from '../../types/dashboard';
import { formatCurrency } from '../../utils/formatters';

interface TopSuppliersListProps {
  suppliers: TopSupplier[];
}

export default function TopSuppliersList({ suppliers }: TopSuppliersListProps) {
  if (suppliers.length === 0) {
    return <p className="text-sm text-gray-500">No hay datos de proveedores.</p>;
  }

  const chartData = suppliers.map((s) => ({
    name: s.fantasy_name || s.legal_name || 'Sin nombre',
    amount: s.total_amount,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
        <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Total']} />
        <Bar dataKey="amount" fill="#3b82f6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
