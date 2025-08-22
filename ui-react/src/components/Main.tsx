import { useEffect, useState } from "react";

import Filters from "./Filters";
import GetDataCTA from "./GetDataCTA";
import Summary from "./Summary";

import { ReactComponent as GoogleIcon } from "../assets/GoogleIcon.svg";
import { ReactComponent as MFPIcon } from "../assets/MFPIcon.svg";

import type { WeightEntry } from "../types/weight_entry";
import type { FiltersSelection } from "../types/filter";
import WeeklyDataTable from "./WeeklyDataTable";

const DEFAULT_WEEKS_LIMIT = 4;

export default function Main(props) {
  const [latestEntry, setLatestEntry] = useState<WeightEntry | null>(null);
  const [filtersSelection, setFiltersSelection] = useState<FiltersSelection>({
    weeksLimit: DEFAULT_WEEKS_LIMIT,
  });

  useEffect(() => {
    fetch("http://localhost:5040/api/latest-entry")
      .then((response) => response.json())
      .then((data) => setLatestEntry(data));
  }, [props.dataSyncComplete]);

  function handleFiltersSelectionChange(newSelection: FiltersSelection) {
    setFiltersSelection(newSelection);
  }

  //   const MFPIcon = (

  //   );

  return (
    <main>
      <div className="main-content">
        <div className="spaced-out">
          {/* Filters Selection */}
          <div className="filters-column">
            <Filters
              filtersSelection={filtersSelection}
              handleFiltersSelectionChange={handleFiltersSelectionChange}
            />
          </div>
          {/* Get Data CTAs*/}
          <div className="get-data">
            <GetDataCTA
              dataSource="gfit"
              ctaText="Get Google Fit Data"
              srcIcon={GoogleIcon}
              handleDataSyncComplete={props.handleDataSyncComplete}
              showToast={props.showToast}
            />
            <GetDataCTA
              dataSource="mfp"
              ctaText="Get MyFitnessPal Data"
              srcIcon={MFPIcon}
              handleDataSyncComplete={props.handleDataSyncComplete}
              showToast={props.showToast}
            />
            {latestEntry !== null && (
              <p>Latest entry: {latestEntry.date ?? "No Data Yet"}</p>
            )}
          </div>
        </div>
        {/*  Summary Component */}
        <Summary
          latestEntry={latestEntry}
          goalSelected={props.goalSelected}
          filterValues={filtersSelection}
          dataSyncComplete={props.dataSyncComplete}
        />
        <WeeklyDataTable
          filterValues={filtersSelection}
          goalSelected={props.goalSelected}
          dataSyncComplete={props.dataSyncComplete}
        />
      </div>
    </main>
  );
}
