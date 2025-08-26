import { useEffect, useState } from "react";
import { toSignedString } from "@/utils";

import type { WeeklyDataTableProps } from "@/types/props";
import type {
  WeeklyDataUrlParams,
  WeeklyDataEntry,
} from "@/types/weekly-table";

const SERVER_BASE_URL = "http://localhost:5040";

export default function WeeklyDataTable(props: WeeklyDataTableProps) {
  const [weeklyData, setWeeklyData] = useState([]);
  // TODO - fetch weekly aggregate data and map entries to <tr> elements
  function weekToRow(weekEntry: WeeklyDataEntry) {
    const { result } = weekEntry;
    return (
      <tr key={weekEntry["week_start"]} className="data-table__row">
        <td className="data-table__cell">{weekEntry["week_start"]}</td>
        <td className="data-table__cell">
          {weekEntry["avg_weight"].toFixed(2)} kg
        </td>
        <td
          // TODO - Add conditional positive / negative / neutral classes
          className={`data-table__cell  ${
            result === "positive" ? "data-table__cell--positive" : ""
          }
                    ${
                      result === "negative" ? "data-table__cell--negative" : ""
                    }`}
        >
          {toSignedString(weekEntry["weight_change"], 2)} kg
        </td>
        <td
          className={`data-table__cell  ${
            result === "positive" ? "data-table__cell--positive" : ""
          }
                    ${
                      result === "negative" ? "data-table__cell--negative" : ""
                    }`}
        >
          {toSignedString(weekEntry["weight_change_prc"], 2)} %
        </td>
        <td
          className={`data-table__cell ${
            result === "positive" ? "data-table__cell--positive" : ""
          }
                    ${
                      result === "negative" ? " data-table__cell--negative" : ""
                    }`}
        >
          {toSignedString(weekEntry["net_calories"])} kcal / day
        </td>
      </tr>
    );
  }

  // Fetching data when filter values change
  useEffect(() => {
    const fetchDataWithFilters = async () => {
      const { weeksLimit, dateTo, dateFrom } = props.filterValues;
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
      const weeklyDataURL = new URL(
        `${SERVER_BASE_URL}/api/weekly-aggregates`
      );
      weeklyDataURL.search = new URLSearchParams(urlParams).toString();
      try {
        const response = await fetch(weeklyDataURL);
        if (!response.ok) {
            const body = await response.json();
            const errorMessage = ('error_message' in body) ? body['error_message'] : 'Error while fetching data';
            throw new Error(errorMessage);
        }
        const body = await response.json();
        setWeeklyData(body["weekly_data"]);
      } catch (err: unknown) {
        setWeeklyData([]);
        if (err instanceof Error) {
            props.showToast('error', err.message);
        }
      }
    };

    fetchDataWithFilters();
  }, [props.filterValues, props.goalSelected, props.dataSyncComplete]);

  return (
    <section>
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
    </section>
  );
}
