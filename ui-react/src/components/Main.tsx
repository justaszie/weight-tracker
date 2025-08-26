import { useEffect, useState } from "react";

import type { MainProps } from "@/types/props";
import type { WeightEntry } from "@/types/weight-entry";
import type { DatesFilterValues, WeeksFilterValues } from "@/types/filter";
import type { DataSourceCTA } from "@/types/utils";

import Filters from "./Filters";
import GetDataCTA from "./GetDataCTA";
import Summary from "./Summary";
import WeeklyDataTable from "./WeeklyDataTable";

import { ReactComponent as GoogleIcon } from "@/assets/GoogleIcon.svg";
import { ReactComponent as MFPIcon } from "@/assets/MFPIcon.svg";

const DEFAULT_WEEKS_LIMIT = 4;

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

  const dataSources: DataSourceCTA[] = [
    { srcName: "gfit", ctaText: "Get Google Fit Data", icon: GoogleIcon },
    { srcName: "mfp", ctaText: "Get MyFitnessPal Data", icon: MFPIcon },
  ];

  useEffect(() => {
    const fetchLatestEntry = async () => {
      try {
        const response = await fetch("http://localhost:5040/api/latest-entry");
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

  return (
    <main>
      <div className="main-content">
        <div className="spaced-out">
          <div className="filters-column">
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
            {dataSources.map((src) => (
              <GetDataCTA
                key={src.srcName}
                dataSource={src.srcName}
                ctaText={src.ctaText}
                srcIcon={src.icon}
                onDataSyncRequest={props.onDataSyncRequest}
              />
            ))}

            {latestEntry !== null && (
              <p>Latest entry: {latestEntry.date ?? "No Data Yet"}</p>
            )}
          </div>
        </div>
        <Summary
          latestEntry={latestEntry}
          goalSelected={props.goalSelected}
          weeksFilterValues={weeksFilterValues}
          datesFilterValues={datesFilterValues}
          dataSyncComplete={props.dataSyncComplete}
          showToast={props.showToast}
        />
        <WeeklyDataTable
          goalSelected={props.goalSelected}
          weeksFilterValues={weeksFilterValues}
          datesFilterValues={datesFilterValues}
          dataSyncComplete={props.dataSyncComplete}
          showToast={props.showToast}
        />
      </div>
    </main>
  );
}
