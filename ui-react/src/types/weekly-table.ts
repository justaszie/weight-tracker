import type { Goal } from '@/types/goal';

export type WeeklyDataUrlParams = {
    weeks_limit?: string;
    date_to?: string;
    date_from?: string;
    goal: Goal;
};

export type WeeklyDataEntry = {
  week_start: string;
  avg_weight: number;
  weight_change: number;
  weight_change_prc: number;
  net_calories: number;
  result: "positive" | "negative";
}