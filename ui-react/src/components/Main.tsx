import { useEffect, useState } from "react";

import type { MainProps } from "@/types/props";
import type { WeightEntry } from "@/types/weight-entry";
import type { DatesFilterValues, WeeksFilterValues } from "@/types/filter";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

import Filters from "./Filters";
import Summary from "./Summary";
import WeeklyDataTable from "./WeeklyDataTable";
import NoDataView from "./NoDataView";
import GetDataSelection from "./GetDataSelection";
import ManageDataCTA from "./ManageDataCTA";
import AddDataModal from "./AddDataModal";

const DEFAULT_WEEKS_LIMIT = 4;

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

  useEffect(() => {
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
  }, [props.dataSyncComplete]);

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
              <GetDataSelection onCTAClick={props.onCTAClick} />
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
                      Latest entry: {latestEntry.entry_date ?? "No Data Yet"}
                    </p>
                  )
                )}
              </div>
            </div>
          </div>
          {isLoading ? (
            <Spinner className="spinner" />
          ) : latestEntry == null ? (
            <NoDataView onCTAClick={props.onCTAClick} />
          ) : (
            <>
              <Summary
                latestEntry={latestEntry}
                goalSelected={props.goalSelected}
                weeksFilterValues={weeksFilterValues}
                datesFilterValues={datesFilterValues}
                dataSyncComplete={props.dataSyncComplete}
                session={props.session}
                showToast={props.showToast}
              />

              <WeeklyDataTable
                goalSelected={props.goalSelected}
                weeksFilterValues={weeksFilterValues}
                datesFilterValues={datesFilterValues}
                dataSyncComplete={props.dataSyncComplete}
                session={props.session}
                showToast={props.showToast}
              />
            </>
          )}
        </div>
      </main>
      {showAddDataModal && (
        <AddDataModal
          closeModal={toggleAddDataModal}
          latestWeight={latestEntry ? String(latestEntry.weight) : ""}
        />
      )}
    </>
  );
}
