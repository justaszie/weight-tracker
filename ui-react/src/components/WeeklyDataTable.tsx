import { useEffect, useState } from "react";
import { toSignedString } from "@/utils";

import type { WeeklyDataTableProps } from "@/types/props";
import type {
  WeeklyDataUrlParams,
  WeeklyDataEntry,
} from "@/types/weekly-table";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

export default function WeeklyDataTable(props: WeeklyDataTableProps) {
  const [weeklyData, setWeeklyData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  function weekToRow(weekEntry: WeeklyDataEntry) {
    const { result } = weekEntry;
    return (
      <tr key={weekEntry["week_start"]} className="data-table__row">
        <td className="data-table__cell">{weekEntry["week_start"]}</td>
        <td className="data-table__cell">
          {weekEntry["avg_weight"].toFixed(2)} kg
        </td>
        <td
          className={`data-table__cell  ${
            result === "positive" ? "data-table__cell--positive" : ""
          }
            ${result === "negative" ? "data-table__cell--negative" : ""}`}
        >
          {toSignedString(weekEntry["weight_change"], 2)} kg
        </td>
        <td
          className={`data-table__cell  ${
            result === "positive" ? "data-table__cell--positive" : ""
          }
            ${result === "negative" ? "data-table__cell--negative" : ""}`}
        >
          {toSignedString(weekEntry["weight_change_prc"], 2)} %
        </td>
        <td
          className={`data-table__cell ${
            result === "positive" ? "data-table__cell--positive" : ""
          }
            ${result === "negative" ? " data-table__cell--negative" : ""}`}
        >
          {toSignedString(weekEntry["net_calories"])} kcal / day
        </td>
      </tr>
    );
  }

  // Fetching data when filter values change
  useEffect(() => {
    const fetchDataWithFilters = async () => {
      const { weeksLimit } = props.weeksFilterValues ?? {};
      const { dateTo, dateFrom } = props.datesFilterValues ?? {};

      const urlParams: WeeklyDataUrlParams = { goal: props.goalSelected };
      if (weeksLimit) {
        urlParams["weeks_limit"] = String(weeksLimit);
      }
      if (dateFrom) {
        urlParams["date_from"] = dateFrom;
      }
      if (dateTo) {
        urlParams["date_to"] = dateTo;
      }
      const weeklyDataURL = new URL(`${API_BASE_URL}/${API_PREFIX}/weekly-aggregates`);
      weeklyDataURL.search = new URLSearchParams(urlParams).toString();
      try {
        const response = await fetch(weeklyDataURL, {
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
        const body = await response.json();
        // body["weekly_data"].sort(
        //   (weekA: WeeklyDataEntry, weekB: WeeklyDataEntry) => sortByWeekStart(weekA, weekB)
        // );
        setWeeklyData(body["weekly_data"]);
      } catch (err: unknown) {
        setWeeklyData([]);
        if (err instanceof Error) {
          props.showToast("error", err.message);
        }
      }
      setIsLoading(false);
    };

    fetchDataWithFilters();

  }, [
    props.datesFilterValues,
    props.weeksFilterValues,
    props.goalSelected,
    props.dataUpdated,
  ]);

  return (
    <section>
      {isLoading ? (
        <Spinner className="spinner" />
      ) : (
        <table className="data-table">
          <thead>
            <tr className="data-table__header">
              <th className="data-table__cell">Week Starting</th>
              <th className="data-table__cell">Avg. Weight</th>
              <th className="data-table__cell">Change (kg)</th>
              <th className="data-table__cell">Change (%)</th>
              <th className="data-table__cell">Calorie Deficit / Surplus</th>
            </tr>
          </thead>
          {weeklyData.length > 0 && <tbody>{weeklyData.map(weekToRow)}</tbody>}
        </table>
      )}
    </section>
  );
}
