import { TrendingUp, TrendingDown, Target, Activity, DollarSign, BarChart3, PieChart, ChevronRight } from 'lucide-react';

const ICON_MAP = {
  'Total P&L': { icon: DollarSign, gradient: 'from-[#059669] to-[#10B981]' },
  'Win Rate': { icon: Target, gradient: 'from-[#2563EB] to-[#3B82F6]' },
  'Profit Factor': { icon: BarChart3, gradient: 'from-[#7C3AED] to-[#8B5CF6]' },
  'Trades': { icon: Activity, gradient: 'from-[#F59E0B] to-[#F97316]' },
  'Avg Win': { icon: TrendingUp, gradient: 'from-[#059669] to-[#10B981]' },
  'Avg Loss': { icon: TrendingDown, gradient: 'from-[#DC2626] to-[#EF4444]' },
  'W / L': { icon: PieChart, gradient: 'from-[#6366F1] to-[#818CF8]' },
};

export default function StatCards({ summary, onCardClick }) {
  if (!summary) return null;

  const {
    total_pnl = 0,
    win_rate = 0,
    profit_factor = 0,
    avg_win = 0,
    avg_loss = 0,
    trade_count = { total: 0, winning: 0, losing: 0 },
  } = summary;

  const total = trade_count?.total ?? 0;
  const wins = trade_count?.winning ?? 0;
  const losses = trade_count?.losing ?? 0;

  const cards = [
    { label: 'Total P&L', value: total_pnl != null ? `$${Number(total_pnl).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : null, positive: total_pnl > 0, negative: total_pnl < 0, subtitle: total > 0 ? `Across ${total} trades` : null },
    { label: 'Win Rate', value: win_rate != null ? `${win_rate.toFixed(1)}%` : null, positive: win_rate >= 50, subtitle: `${wins}W / ${losses}L` },
    { label: 'Profit Factor', value: profit_factor != null ? profit_factor.toFixed(2) : null, positive: profit_factor >= 1.5, subtitle: profit_factor > 0 ? 'Wins vs losses ratio' : null },
    { label: 'Trades', value: total, subtitle: `${wins} winning · ${losses} losing` },
    { label: 'Avg Win', value: avg_win != null ? `$${Number(avg_win).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : null, positive: true, subtitle: `Best: $${(summary.best_trade?.pnl || 0).toLocaleString()}` },
    { label: 'Avg Loss', value: avg_loss != null ? `$${Number(avg_loss).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : null, negative: true, subtitle: `Worst: $${Math.abs(summary.worst_trade?.pnl || 0).toLocaleString()}` },
    { label: 'W / L', value: `${wins}W / ${losses}L`, subtitle: `Streak: ${summary.max_consecutive_wins || 0}W / ${summary.max_consecutive_losses || 0}L` },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-4">
      {cards.map((card) => {
        const iconDef = ICON_MAP[card.label] || { icon: Activity, gradient: 'from-[#64748B] to-[#94A3B8]' };
        const Icon = iconDef.icon;
        const valColor = card.positive ? 'text-[#059669]' : card.negative ? 'text-[#DC2626]' : 'text-[#0F172A]';

        return (
          <button
            key={card.label}
            onClick={() => onCardClick?.(card.label)}
            className="stat-card text-left w-full cursor-pointer group"
          >
            <div className="flex items-start justify-between mb-3">
              <p className="stat-label">{card.label}</p>
              <div className={`stat-icon bg-gradient-to-br ${iconDef.gradient} shadow-sm group-hover:scale-110 transition-transform duration-200`}>
                <Icon size={15} className="text-white" />
              </div>
            </div>
            <p className={`stat-value ${valColor}`}>
              {card.value ?? '\u2014'}
            </p>
            {card.subtitle && (
              <p className="text-[11px] text-[#64748B] mt-1.5 flex items-center gap-1">
                {card.subtitle}
                <ChevronRight size={11} className="text-[#CBD5E1] group-hover:text-[#64748B] group-hover:translate-x-0.5 transition-all" />
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}
