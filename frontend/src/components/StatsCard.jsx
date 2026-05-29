export default function StatsCard({ label, value, positive, negative }) {
  const valueColor = positive ? 'text-[#22c55e]' : negative ? 'text-[#ef4444]' : 'text-[#111827]';

  return (
    <div className="stat-card">
      <p className="stat-label">{label}</p>
      <p className={`stat-value ${value != null ? valueColor : ''}`}>
        {value ?? '\u2014'}
      </p>
    </div>
  );
}
