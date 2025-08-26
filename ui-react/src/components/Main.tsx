import { useEffect, useState } from "react";

import type { MainProps } from "@/types/props";
import type { WeightEntry } from "@/types/weight-entry";
import type { FiltersSelection } from "@/types/filter";
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
  const [filtersSelection, setFiltersSelection] = useState<FiltersSelection>({
    weeksLimit: DEFAULT_WEEKS_LIMIT,
  });

  const dataSources: DataSourceCTA[] = [
    {srcName: 'gfit', ctaText: 'Get Google Fit Data', icon: GoogleIcon},
    {srcName: 'mfp', ctaText: 'Get MyFitnessPal Data', icon: MFPIcon},
  ]

  useEffect(() => {
    fetch("http://localhost:5040/api/latest-entry")
      .then((response) => response.json())
      .then((data) => setLatestEntry(data));
  }, [props.dataSyncComplete]);

  function handleFiltersSelectionChange(newSelection: FiltersSelection) {
    setFiltersSelection(newSelection);
  }

  return (
    <main>
      <div className="main-content">
        <div className="spaced-out">
          <div className="filters-column">
            <Filters
              filtersSelection={filtersSelection}
              handleFiltersSelectionChange={handleFiltersSelectionChange}
              showToast={props.showToast}
            />
          </div>
          <div className="get-data">
            {
              dataSources.map(src => (
                <GetDataCTA
                  key={src.srcName}
                  dataSource={src.srcName}
                  ctaText={src.ctaText}
                  srcIcon={src.icon}
                  onDataSyncRequest={props.onDataSyncRequest}
                />
              ))
            }

            {latestEntry !== null && (
              <p>Latest entry: {latestEntry.date ?? "No Data Yet"}</p>
            )}
          </div>
        </div>
        <Summary
          latestEntry={latestEntry}
          goalSelected={props.goalSelected}
          filterValues={filtersSelection}
          dataSyncComplete={props.dataSyncComplete}
          showToast={props.showToast}
        />
        <WeeklyDataTable
          filterValues={filtersSelection}
          goalSelected={props.goalSelected}
          dataSyncComplete={props.dataSyncComplete}
          showToast={props.showToast}
        />
      </div>
    </main>
  );
}
