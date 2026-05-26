import StatsCard from './StatsCard';

export default function StatCards({ summary }) {
  if (!summary) return null;

  const {
    total_pnl = 0,
    win_rate = 0,
    profit_factor = 0,
    avg_win = 0,
    avg_loss = 0,
    trade_count = { total: 0, winning: 0, losing: 0, breakeven: 0 },
  } = summary;

  const total_trades = trade_count?.total ?? 0;
  const total_wins = trade_count?.winning ?? 0;
  const total_losses = trade_count?.losing ?? 0;

  const cards = [
    {
      label: 'Total P&L',
      value: total_pnl != null ? `$${Number(total_pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : null,
      positive: total_pnl > 0,
      negative: total_pnl < 0,
    },
    {
      label: 'Win Rate',
      value: win_rate != null ? `${win_rate.toFixed(1)}%` : null,
      positive: win_rate >= 0.5,
      negative: win_rate < 0.5,
    },
    {
      label: 'Profit Factor',
      value: profit_factor != null ? profit_factor.toFixed(2) : null,
      positive: profit_factor >= 1.5,
      negative: profit_factor < 1,
    },
    {
      label: 'Total Trades',
      value: total_trades,
    },
    {
      label: 'Avg Win',
      value: avg_win != null ? `$${Number(avg_win).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : null,
      positive: true,
    },
    {
      label: 'Avg Loss',
      value: avg_loss != null ? `$${Number(avg_loss).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : null,
      negative: true,
    },
    {
      label: 'Wins / Losses',
      value: `${total_wins || 0}W / ${total_losses || 0}L`,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-4">
      {cards.map((card) => (
        <StatsCard
          key={card.label}
          label={card.label}
          value={card.value}
          positive={card.positive}
          negative={card.negative}
        />
      ))}
    </div>
  );
}
