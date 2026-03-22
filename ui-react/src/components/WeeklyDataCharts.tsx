import { useEffect, useState } from "react";

// TODO - REVIEW - try to merge with weekly data table
import type { WeeklyDataChartsProps } from "@/types/props";
import type {
  WeeklyDataUrlParams,
  WeeklyDataEntry,
} from "@/types/weekly-charts";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

import {
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Bar,
  LineChart,
  Line,
} from "recharts";
import { RechartsDevtools } from "@recharts/devtools";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

export default function WeeklyDataCharts(props: WeeklyDataChartsProps) {
  const [weeklyData, setWeeklyData] = useState<WeeklyDataEntry[]>([]);
  const [isLoading, setIsLoading] = useState<Boolean>(true);

  function weekToBar(week: WeeklyDataEntry) {
    return {
      week: week.week_start,
      "Weight Change": week.weight_change,
      Weight: week.avg_weight,
    };
  }

  // Fetching data when filter values change
  useEffect(() => {
    setIsLoading(true);
    const fetchDataWithFilters = async () => {
      const { weeksLimit } = props.weeksFilterValues ?? {};
      const { dateTo, dateFrom } = props.datesFilterValues ?? {};

      const urlParams: WeeklyDataUrlParams = {};
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
        `${API_BASE_URL}/${API_PREFIX}/weekly-aggregates`
      );
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
        const weeklyData: Array<WeeklyDataEntry> = [...body["weekly_data"]];
        // For the chart we want the data sorted by week start date, in ascending order
        const sortedByWeekStart = weeklyData.sort((weekA, weekB) =>
          sortByWeekStart(weekA, weekB)
        );
        setWeeklyData(sortedByWeekStart); // Excluding the reference because it has 0 change
      } catch (err: unknown) {
        setWeeklyData([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDataWithFilters();
  }, [props.datesFilterValues, props.weeksFilterValues, props.dataUpdated]);

  function sortByWeekStart(weekA: WeeklyDataEntry, weekB: WeeklyDataEntry) {
    return weekA.week_start < weekB.week_start ? -1 : 1;
  }

  return (
    // weeklyData to map to charts
    <section>
      {isLoading ? (
        <Spinner className="spinner" />
      ) : (
        <>
          <div className="weekly-weight-chart">
            <h2 className="weekly-weight-chart__title">Weight Over Time</h2>
            <LineChart
              style={{
                width: "100%",
                height: "100%",
                maxHeight: "30vh",
                aspectRatio: 1.618,
              }}
              responsive
              data={weeklyData.map((week) => weekToBar(week))}
              margin={{
                top: 5,
                right: 5,
                left: 5,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis width="auto" domain={["dataMin - 1", "dataMax + 1"]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="Weight"
                stroke="#4b5563"
                activeDot={{ r: 6 }}
              />
              <RechartsDevtools />
            </LineChart>
          </div>
          <div className="weekly-change-chart">
            <h2 className="weekly-change-chart__title">Loss / Gain Over Time</h2>
            <BarChart
              style={{ width: "100%", maxHeight: "30vh", aspectRatio: 1.618 }}
              responsive
              // Exclude the 1st week (reference week as it has no change)
              data={weeklyData.slice(1).map((week) => weekToBar(week))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis width="auto" />
              <Tooltip />
              <Legend />
              <Bar dataKey="Weight Change" fill="#4b5563" />
              <RechartsDevtools />
            </BarChart>
          </div>
        </>
      )}
    </section>
  );
}
