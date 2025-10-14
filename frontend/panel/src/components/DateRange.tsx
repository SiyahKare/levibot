/**
 * Date Range Picker Component
 * Allows selection of date ranges for analytics
 */
import { useMemo } from "react";
import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";

type Props = {
  fromIso?: string;
  toIso?: string;
  onChange: (range: { fromIso?: string; toIso?: string }) => void;
};

export function DateRange({ fromIso, toIso, onChange }: Props) {
  const selected = useMemo(
    () => ({
      from: fromIso ? new Date(fromIso) : undefined,
      to: toIso ? new Date(toIso) : undefined,
    }),
    [fromIso, toIso]
  );

  const toISO = (d?: Date): string | undefined => {
    if (!d) return undefined;
    // Adjust for timezone to get local date at midnight
    const adjusted = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return adjusted.toISOString().replace(/\.\d{3}Z$/, "Z");
  };

  return (
    <div className="flex flex-col gap-3">
      <DayPicker
        mode="range"
        selected={selected as any}
        onSelect={(range: any) => {
          const from = range?.from ? new Date(range.from) : undefined;
          const to = range?.to ? new Date(range.to) : undefined;
          onChange({ fromIso: toISO(from), toIso: toISO(to) });
        }}
        numberOfMonths={2}
        className="rdp-custom"
      />
      <div className="text-xs text-zinc-500 dark:text-zinc-400 px-2">
        <div className="flex items-center gap-2">
          <span className="font-medium">From:</span>
          <span className="font-mono">{fromIso || "—"}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-medium">To:</span>
          <span className="font-mono">{toIso || "—"}</span>
        </div>
      </div>
    </div>
  );
}
