import type { Goal } from "@/types/goal";
import type { FiltersSelection } from "@/types/filter";
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
  filterValues: FiltersSelection;
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
  filterValues: FiltersSelection;
  goalSelected: Goal;
  dataSyncComplete: boolean;
  showToast: ShowToastFn;
};

export type FiltersProps = {
  filtersSelection: FiltersSelection;
  handleFiltersSelectionChange: (newSelection: FiltersSelection) => void;
  showToast: ShowToastFn;
};

export type WeeksFilterProps = {
  selectedValues: { weeksLimit?: number };
  handleSelectionChange: (newSelection: FiltersSelection) => void;
  showToast: ShowToastFn;
};

export type DatesFilterProps = {
  selectedValues: { dateTo?: string; dateFrom?: string };
  handleSelectionChange: (newSelection: FiltersSelection) => void;
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
