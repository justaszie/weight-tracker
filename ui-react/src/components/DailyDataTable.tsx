import { useEffect, useState } from "react";

import type { DailyDataTableProps } from "@/types/props";
import type { DailyDataUrlParams } from "@/types/daily-table";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";
import type { WeightEntry } from "@/types/weight-entry";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

export default function dailyEntriesTable(props: DailyDataTableProps) {
  const [dailyEntries, setDailyEntries] = useState<WeightEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  function dayToRow(dailyEntry: WeightEntry) {
    return (
      <tr key={dailyEntry["entry_date"]} className="data-table__row">
        <td className="data-table__cell">{dailyEntry["entry_date"]}</td>
        <td className="data-table__cell">
          {dailyEntry["weight"].toFixed(2)} kg
        </td>
        <td className="data-table__cell data-table__cell--action">
          <button
            className="data-table__delete-cta"
            onClick={() => deleteEntry(dailyEntry["entry_date"])}
          >
            Delete
          </button>
        </td>
      </tr>
    );
  }

  async function deleteEntry(entryDate: string) {
    setIsLoading(true);

    const deleteEntryURL = new URL(`${API_BASE_URL}/${API_PREFIX}/daily-entry`);
    const urlParams = { entry_date: entryDate };
    deleteEntryURL.search = new URLSearchParams(urlParams).toString();

    const result = await fetch(deleteEntryURL, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${props.session.access_token}`,
      },
    });

    if (!result.ok) {
      props.showToast("error", "Error while deleting entry");
      setIsLoading(false);
      return;
    }

    setDailyEntries((prev) =>
      prev.filter((entry) => entry.entry_date !== entryDate)
    );
    setIsLoading(false);
    props.handleDataUpdate();
    props.showToast("success", `Entry deleted for ${entryDate}`);
  }

  function sortedDesc(entries: WeightEntry[]): WeightEntry[] {
    entries.sort((a, b) => {
      if (a["entry_date"] > b["entry_date"]) {
        return -1;
      } else {
        return 1;
      }
    });
    return entries;
  }

  function calculateStartDate(weeksLookbackCount: number): string {
    const lookbackMs = weeksLookbackCount * 7 * 24 * 3600 * 1000;
    const startDate = new Date(Date.now() - lookbackMs);
    return startDate.toISOString().split("T")[0];
  }

  // Fetching data when filter values change
  useEffect(() => {
    setIsLoading(true);
    const fetchDataWithFilters = async () => {
      const { weeksLimit } = props.weeksFilterValues ?? {};
      const { dateTo, dateFrom } = props.datesFilterValues ?? {};

      const urlParams: DailyDataUrlParams = {};
      if (dateFrom) {
        urlParams["date_from"] = dateFrom;
      }
      if (dateTo) {
        urlParams["date_to"] = dateTo;
      } else if (weeksLimit) {
        urlParams["date_to"] = new Date().toISOString().split("T")[0];
        urlParams["date_from"] = calculateStartDate(weeksLimit);
      }
      const dailyEntriesURL = new URL(
        `${API_BASE_URL}/${API_PREFIX}/daily-entries`
      );
      dailyEntriesURL.search = new URLSearchParams(urlParams).toString();
      try {
        const response = await fetch(dailyEntriesURL, {
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
        setDailyEntries(sortedDesc(entries));
      } catch (err: unknown) {
        setDailyEntries([]);
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
              <th className="data-table__cell data-table__cell--action">
                Actions
              </th>
            </tr>
          </thead>
          {dailyEntries.length > 0 && (
            <tbody>{dailyEntries.map(dayToRow)}</tbody>
          )}
        </table>
      )}
    </section>
  );
}
