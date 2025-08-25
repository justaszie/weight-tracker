import type { Goal } from "@/types/goal";
import type { FiltersSelection } from "@/types/filter";
import type { WeightEntry } from "@/types/weight_entry";
import type { MessageCategory } from "@/types/toast";

export type MainProps = {
  goalSelected: Goal;
  handleDataSyncComplete: () => void;
  dataSyncComplete: boolean;
  onDataSyncRequest: (data_source?: string) => void;
};

export type DatesFilterProps = {
  selectedValues: { dateTo?: string; dateFrom?: string };
  handleSelectionChange: (newSelection: FiltersSelection) => void;
};

export type FiltersProps = {
  filtersSelection: FiltersSelection;
  handleFiltersSelectionChange: (newSelection: FiltersSelection) => void;
};

export type GetDataCTAProps = {
  ctaText: string;
  srcIcon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  dataSource: string;
  onDataSyncRequest: (data_source?: string) => void;
};

export type HeaderProps = {
  handleGoalChange: (goal: Goal) => void;
  goalSelected: Goal;
};

export type SummaryProps = {
  latestEntry?: WeightEntry | null;
  goalSelected: Goal;
  filterValues: FiltersSelection;
  dataSyncComplete: boolean;
};

export type ToastProps = {
  category: MessageCategory;
  message: string;
};

export type WeeklyDataTableProps = {
  filterValues: FiltersSelection;
  goalSelected: Goal;
  dataSyncComplete: boolean;
};

export type WeeksFilterProps = {
  selectedValues: { weeksLimit?: number };
  handleSelectionChange: (newSelection: FiltersSelection) => void;
};
