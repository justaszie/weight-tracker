import { useEffect, useState } from "react";

import type { DailyDataTableProps } from "@/types/props";
import type { DailyDataUrlParams } from "@/types/daily-table";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";
import type { WeightEntry } from "@/types/weight-entry";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

export default function DailyDataTable(props: DailyDataTableProps) {
  const [dailyData, setDailyData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  function dayToRow(dailyEntry: WeightEntry) {
    return (
      <tr key={dailyEntry["entry_date"]} className="data-table__row">
        <td className="data-table__cell">{dailyEntry["entry_date"]}</td>
        <td className="data-table__cell">
          {dailyEntry["weight"].toFixed(2)} kg
        </td>
        <td className="data-table__cell data-table__cell--action">
          <button key={dailyEntry["entry_date"]} className="data-table__delete-cta" onClick={deleteEntry}>Delete</button>
        </td>
      </tr>
    );
  }

  function deleteEntry(event: React.MouseEvent<HTMLButtonElement>): void {
    console.log('Delete event');
  }

  function sortedDesc(entries: WeightEntry[]): void {
    entries.sort((a, b) => {
      if (a["entry_date"] > b["entry_date"]) {
        return -1;
      } else {
        return 1;
      }
    });
  }

  // Fetching data when filter values change
  useEffect(() => {
    setIsLoading(true);
    const fetchDataWithFilters = async () => {
      const { weeksLimit } = props.weeksFilterValues ?? {};
      const { dateTo, dateFrom } = props.datesFilterValues ?? {};

      const urlParams: DailyDataUrlParams = {};
      if (weeksLimit) {
        urlParams["weeks_limit"] = String(weeksLimit);
      }
      if (dateFrom) {
        urlParams["date_from"] = dateFrom;
      }
      if (dateTo) {
        urlParams["date_to"] = dateTo;
      }
      const dailyDataURL = new URL(
        `${API_BASE_URL}/${API_PREFIX}/daily-entries`
      );
      dailyDataURL.search = new URLSearchParams(urlParams).toString();
      try {
        const response = await fetch(dailyDataURL, {
          headers: {
            Authorization: `Bearer ${props.session.access_token}`,
          },
        });
        if (!response.ok) {
          const body = await response.json();
          const errorMessage =
            "error_message" in body
              ? body["error_message"]
              : "Error while fetching data";
          throw new Error(errorMessage);
        }
        const entries = await response.json();
        sortedDesc(entries);
        setDailyData(entries);
      } catch (err: unknown) {
        setDailyData([]);
        if (err instanceof Error) {
          props.showToast("error", err.message);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchDataWithFilters();
  }, [props.datesFilterValues, props.weeksFilterValues, props.dataUpdated]);

  return (
    <section>
      {isLoading ? (
        <Spinner className="spinner" />
      ) : (
        <table className="data-table">
          <thead>
            <tr className="data-table__header">
              <th className="data-table__cell">Entry Date</th>
              <th className="data-table__cell">Weight</th>
              <th className="data-table__cell data-table__cell--action">Actions</th>
            </tr>
          </thead>
          {dailyData.length > 0 && <tbody>{dailyData.map(dayToRow)}</tbody>}
        </table>
      )}
    </section>
  );
}
