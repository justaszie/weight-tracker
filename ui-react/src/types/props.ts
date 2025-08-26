import type { Goal } from "@/types/goal";
import type { DatesFilterValues, WeeksFilterValues } from "@/types/filter";
import type { WeightEntry } from "@/types/weight-entry";
import type { ToastMessageCategory, ShowToastFn } from "@/types/toast";
import type { DataSourceName } from "./utils";

export type MainProps = {
  goalSelected: Goal;
  handleDataSyncComplete: () => void;
  dataSyncComplete: boolean;
  onDataSyncRequest: (data_source?: DataSourceName) => void;
  showToast: ShowToastFn;
};

export type SummaryProps = {
  latestEntry?: WeightEntry | null;
  goalSelected: Goal;
  weeksFilterValues?: WeeksFilterValues;
  datesFilterValues?: DatesFilterValues;
  dataSyncComplete: boolean;
  showToast: ShowToastFn;
};

export type GetDataCTAProps = {
  ctaText: string;
  srcIcon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  dataSource: DataSourceName;
  onDataSyncRequest: (data_source?: DataSourceName) => void;
};

export type WeeklyDataTableProps = {
  goalSelected: Goal;
  weeksFilterValues?: WeeksFilterValues;
  datesFilterValues?: DatesFilterValues;
  dataSyncComplete: boolean;
  showToast: ShowToastFn;
};

export type FiltersProps = {
  weeksFilterValues?: WeeksFilterValues;
  datesFilterValues?: DatesFilterValues;
  handleDatesFilterChange: (newValues: DatesFilterValues) => void;
  handleWeeksFilterChange: (newValues: WeeksFilterValues) => void;
  showToast: ShowToastFn;
  resetFilterValues: () => void;
};

export type WeeksFilterProps = {
  selectedValues?: WeeksFilterValues;
  handleValueChange: (newValues: WeeksFilterValues) => void;
  showToast: ShowToastFn;
};

export type DatesFilterProps = {
  selectedValues?: DatesFilterValues;
  handleValueChange: (newValues: DatesFilterValues) => void;
  showToast: ShowToastFn;
};

export type ToastProps = {
  category: ToastMessageCategory;
  message: string;
};

export type HeaderProps = {
  handleGoalChange: (goal: Goal) => void;
  goalSelected: Goal;
};
