import type { Goal } from "@/types/goal";
import type { User } from "@/types/user";
import type { DatesFilterValues, WeeksFilterValues } from "@/types/filter";
import type { WeightEntry } from "@/types/weight-entry";
import type { ToastMessageCategory, ShowToastFn } from "@/types/toast";
import type { DataSourceName } from "./utils";
import type { Session } from "@supabase/supabase-js";

export type MainProps = {
  goalSelected: Goal;
  session: Session;
  handleDataSyncComplete: () => void;
  dataSyncComplete: boolean;
  onCTAClick: (data_source?: DataSourceName) => void;
  showToast: ShowToastFn;
};

export type LoginProps = {
  showToast: ShowToastFn;
}

export type SummaryProps = {
  latestEntry?: WeightEntry | null;
  goalSelected: Goal;
  weeksFilterValues?: WeeksFilterValues;
  datesFilterValues?: DatesFilterValues;
  dataSyncComplete: boolean;
  session: Session;
  showToast: ShowToastFn;
};

export type GetDataCTAProps = {
  ctaText: string;
  srcIcon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  dataSource?: DataSourceName;
  onCTAClick: (data_source?: DataSourceName) => void;
};

export type ManageDataCTAProps = {
  ctaText: string;
  onCTAClick: () => void;
};

export type WeeklyDataTableProps = {
  goalSelected: Goal;
  weeksFilterValues?: WeeksFilterValues;
  datesFilterValues?: DatesFilterValues;
  dataSyncComplete: boolean;
  session: Session;
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
  user: User;
};

export type NoDataViewProps = {
  onCTAClick: (data_source?: DataSourceName) => void;
}

export type GetDataSelectionProps = {
  onCTAClick: (data_source?: DataSourceName) => void;
}

export type AddDataModalProps = {
  closeModal: () => void;
  latestWeight: string;
}