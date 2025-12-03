import { useEffect, useState } from "react";

import type { MainProps } from "@/types/props";
import type { WeightEntry } from "@/types/weight-entry";
import type { DatesFilterValues, WeeksFilterValues } from "@/types/filter";
import type { DataViewMode } from "@/types/utils";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

import Filters from "./Filters";
import Summary from "./Summary";
import WeeklyDataTable from "./WeeklyDataTable";
import DailyDataTable from "./DailyDataTable";
import NoDataView from "./NoDataView";
import GetDataSelection from "./GetDataSelection";
import ManageDataCTA from "./ManageDataCTA";
import AddDataModal from "./AddDataModal";

const DEFAULT_WEEKS_LIMIT = 4;
const DEFAULT_DATA_VIEW_MODE: DataViewMode = "weekly";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

export default function Main(props: MainProps) {
  const [latestEntry, setLatestEntry] = useState<WeightEntry | null>(null);
  const [weeksFilterValues, setWeeksFilterValues] = useState<WeeksFilterValues>(
    {
      weeksLimit: DEFAULT_WEEKS_LIMIT,
    }
  );
  const [datesFilterValues, setDatesFilterValues] = useState<DatesFilterValues>(
    {}
  );
  const [isLoading, setIsLoading] = useState(true);
  const [showAddDataModal, setshowAddDataModal] = useState(false);
  const [dataViewMode, setDataViewMode] = useState<DataViewMode>(
    DEFAULT_DATA_VIEW_MODE
  );

  useEffect(() => {
    setIsLoading(true);
    const fetchLatestEntry = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/${API_PREFIX}/latest-entry`,
          {
            headers: {
              Authorization: `Bearer ${props.session.access_token}`,
            },
          }
        );
        if (!response.ok) {
          const body = await response.json();
          const errorMessage =
            "error_message" in body
              ? body["error_message"]
              : "Error getting latest entry";
          throw new Error(errorMessage);
        }
        const data: WeightEntry = await response.json();
        setLatestEntry(data);
      } catch (err: unknown) {
        if (err instanceof Error) {
          props.showToast("error", err.message);
        }
      }
      setIsLoading(false);
    };

    fetchLatestEntry();
  }, [props.dataUpdated]);

  function handleWeeksFilterChange(newValues: WeeksFilterValues) {
    setWeeksFilterValues(newValues);
  }

  function handleDatesFilterChange(newValues: DatesFilterValues) {
    setDatesFilterValues(newValues);
  }

  function resetFilterValues() {
    setWeeksFilterValues({});
    setDatesFilterValues({});
  }

  function toggleAddDataModal() {
    setshowAddDataModal(!showAddDataModal);
  }

  function handleDataViewModeChange(
    event: React.MouseEvent<HTMLAnchorElement>
  ) {
    event.preventDefault();
    const viewMode: DataViewMode = event.currentTarget.dataset
      .viewMode as DataViewMode;
    if (["daily", "weekly"].includes(viewMode)) {
      setDataViewMode(viewMode);
    }
  }

  return (
    <>
      <main>
        <div className="main-content">
          <div className="data-controls">
            <div className="filters">
              <Filters
                weeksFilterValues={weeksFilterValues}
                datesFilterValues={datesFilterValues}
                handleWeeksFilterChange={handleWeeksFilterChange}
                handleDatesFilterChange={handleDatesFilterChange}
                showToast={props.showToast}
                resetFilterValues={resetFilterValues}
              />
            </div>
            <div className="get-data">
              <GetDataSelection onCTAClick={props.onGetDataCTAClick} />
              <ManageDataCTA
                ctaText="+ Add Weight"
                onCTAClick={toggleAddDataModal}
              />
              <div>
                {isLoading ? (
                  <Spinner className="spinner" />
                ) : (
                  latestEntry !== null && (
                    <p>
                      {`Latest entry on ${latestEntry.entry_date} (${latestEntry.weight}kg)`}
                    </p>
                  )
                )}
              </div>
            </div>
          </div>
          {isLoading ? (
            <Spinner className="spinner" />
          ) : latestEntry == null ? (
            <NoDataView
              onGetDataCTAClick={props.onGetDataCTAClick}
              onAddDataCTAClick={toggleAddDataModal}
            />
          ) : (
            <>
              <Summary
                latestEntry={latestEntry}
                goalSelected={props.goalSelected}
                weeksFilterValues={weeksFilterValues}
                datesFilterValues={datesFilterValues}
                dataUpdated={props.dataUpdated}
                session={props.session}
                showToast={props.showToast}
              />
              {/* DATA VIEW SELECTION */}
              <div className="data-views">
                <a
                  data-view-mode="weekly"
                  onClick={handleDataViewModeChange}
                  className={`data-views__option ${
                    dataViewMode === "weekly"
                      ? "data-views__option--active"
                      : ""
                  }`}
                >
                  Weekly View
                </a>
                <a
                  data-view-mode="daily"
                  onClick={handleDataViewModeChange}
                  className={`data-views__option ${
                    dataViewMode === "daily" ? "data-views__option--active" : ""
                  }`}
                >
                  Daily View
                </a>
              </div>
              {/* DATA TABLES (Daily / Weekly) */}
              {dataViewMode === "daily" ? (
                <DailyDataTable
                  weeksFilterValues={weeksFilterValues}
                  datesFilterValues={datesFilterValues}
                  dataUpdated={props.dataUpdated}
                  session={props.session}
                  showToast={props.showToast}
                  handleDataUpdate={props.handleDataUpdate}
                />
              ) : (
                <WeeklyDataTable
                  goalSelected={props.goalSelected}
                  weeksFilterValues={weeksFilterValues}
                  datesFilterValues={datesFilterValues}
                  dataUpdated={props.dataUpdated}
                  session={props.session}
                  showToast={props.showToast}
                />
              )}
            </>
          )}
        </div>
      </main>
      {showAddDataModal && (
        <AddDataModal
          closeModal={toggleAddDataModal}
          latestWeight={latestEntry ? String(latestEntry.weight) : ""}
          session={props.session}
          showToast={props.showToast}
          handleDataUpdate={props.handleDataUpdate}
        />
      )}
    </>
  );
}
