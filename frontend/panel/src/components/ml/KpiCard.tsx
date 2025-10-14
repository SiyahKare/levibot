interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  status?: "green" | "amber" | "red" | "gray";
}

export default function KpiCard({
  title,
  value,
  subtitle,
  trend,
  status = "gray",
}: KpiCardProps) {
  const statusColors = {
    green: "border-green-500 bg-green-500/10",
    amber: "border-amber-500 bg-amber-500/10",
    red: "border-red-500 bg-red-500/10",
    gray: "border-zinc-700 bg-zinc-800/50",
  };

  const trendIcons = {
    up: "📈",
    down: "📉",
    neutral: "➡️",
  };

  return (
    <div
      className={`rounded-xl border-2 p-6 shadow-lg transition-all duration-300 ${statusColors[status]}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-400 uppercase tracking-wide">
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
        </div>
        {trend && (
          <div className="text-2xl opacity-70">{trendIcons[trend]}</div>
        )}
      </div>
    </div>
  );
}
