import type { WeeklyDataEntry } from '@/types/weekly-table';

export type SummaryUrlParams = {
  weeks_limit?: string;
  date_to?: string;
  date_from?: string;
};

export type SummaryMetrics = {
  total_change: number;
  avg_change: number;
  avg_change_prc: number;
  avg_net_calories: number;
};

export type SummaryData = {
  metrics?: SummaryMetrics | null;
  latest_week?: WeeklyDataEntry | null;
};
