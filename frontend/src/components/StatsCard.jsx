export default function StatsCard({ label, value, prefix = '', suffix = '', positive, negative }) {
  let colorClass = 'text-gray-900';
  if (positive === true) colorClass = 'text-positive';
  else if (positive === false) colorClass = 'text-negative';
  else if (negative === true) colorClass = 'text-negative';
  else if (negative === false) colorClass = 'text-positive';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 min-w-[140px] flex-1">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${colorClass}`}>
        {prefix}{value !== null && value !== undefined ? value : '—'}{suffix}
      </p>
    </div>
  );
}
