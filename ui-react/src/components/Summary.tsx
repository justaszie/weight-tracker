import { useState, useEffect } from "react";

import type { SummaryProps } from "@/types/props";
import type { SummaryData, SummaryUrlParams } from "@/types/summary";
import type { Goal } from "@/types/goal";

import { toSignedString } from "@/utils";

const GOAL_LABELS: { [key in Goal]: string } = {
  lose: "Losing Fat",
  maintain: "Maintaining",
  gain: "Gaining Muscle",
};
const SERVER_BASE_URL = "http://localhost:5040";

export default function Summary(props: SummaryProps) {
  const [summaryData, setSummaryData] = useState<SummaryData>({});

  const { dateTo, dateFrom } = props.datesFilterValues ?? {};
  const { weeksLimit } = props.weeksFilterValues ?? {};

  const summaryHeader = weeksLimit
    ? `Summary for the past ${weeksLimit} weeks`
    : `Summary from ${dateFrom ? dateFrom : "beginning"} to
      ${dateTo ? dateTo : "today"}`;

  //   Fetch summary data
  useEffect(() => {
    const fetchSummaryDataWithFilters = async () => {
      const urlParams: SummaryUrlParams = {};
      if (weeksLimit) {
        urlParams["weeks_limit"] = String(weeksLimit);
      }
      if (dateFrom) {
        urlParams["date_from"] = dateFrom;
      }
      if (dateTo) {
        urlParams["date_to"] = dateTo;
      }

      const summaryURL = new URL(`${SERVER_BASE_URL}/api/summary`);
      summaryURL.search = new URLSearchParams(urlParams).toString();
      try {
        const response = await fetch(summaryURL);
        if(!response.ok) {
          const body = await response.json();
          const errorMessage = ('error_message' in body) ? body['error_message'] : 'Error while getting summary data';
          throw new Error(errorMessage);
        }
        const body = await response.json();
        setSummaryData(body.metrics);

      } catch (err: unknown) {
        setSummaryData({});
        if(err instanceof Error) {
          props.showToast('error', err.message);
        }
      }
    };

    fetchSummaryDataWithFilters();
  }, [props.datesFilterValues, props.weeksFilterValues, props.dataSyncComplete]);

  return (
    <section className="summary">
      <div className="summary__header spaced-out">
        <h2>{summaryHeader}</h2>
        <p className="summary__goal-reminder">
          <svg
            className="summary_icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
          </svg>
          <span>Current Goal: {GOAL_LABELS[props.goalSelected]}</span>
        </p>
      </div>

      {/* <!-- Cards --> */}
      <ul className="summary__cards-container">
        {props.latestEntry && props.latestEntry.weight && (
          <li className="summary-card">
            <p className="summary-card__header">
              <svg
                className=" goal-selection__icon"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"></path>
                <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"></path>
                <path d="M7 21h10"></path>
                <path d="M12 3v18"></path>
                <path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"></path>
              </svg>
              <span>Latest Weight</span>
            </p>
            <div className="summary-card__value-group">
              <h3 className="summary-card__value">
                {props.latestEntry.weight.toFixed(2)}
              </h3>
              <span className="summary-card__subtitle">kg</span>
            </div>
            <p className="summary-card__header">
              on <span>{props.latestEntry.date}</span>
            </p>
          </li>
        )}
        <li className="summary-card">
          <p className="summary-card__header">
            <svg
              className="summary-card__icon"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m21 16-4 4-4-4"></path>
              <path d="M17 20V4"></path>
              <path d="m3 8 4-4 4 4"></path>
              <path d="M7 4v16"></path>
            </svg>
            <span>Total Weight Change</span>
          </p>
          <div className="summary-card__value-group">
            <h3 className="summary-card__value">
              {summaryData.total_change &&
                toSignedString(summaryData.total_change, 2)}
            </h3>
            <span className="summary-card__subtitle">kg</span>
          </div>
        </li>
        <li className="summary-card">
          <p className="summary-card__header">
            <svg
              className="summary-card__icon"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m21 16-4 4-4-4"></path>
              <path d="M17 20V4"></path>
              <path d="m3 8 4-4 4 4"></path>
              <path d="M7 4v16"></path>
            </svg>
            <span>Avg. Weight Change</span>
          </p>
          <div className="summary-card__value-group">
            <h3 className="summary-card__value">
              {summaryData.avg_change &&
                toSignedString(summaryData.avg_change, 2)}
            </h3>
            <span className="summary-card__subtitle">kg / week</span>
          </div>
        </li>
        <li className="summary-card">
          <p className="summary-card__header">
            <svg
              className="summary-card__icon"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="19" x2="5" y1="5" y2="19"></line>
              <circle cx="6.5" cy="6.5" r="2.5"></circle>
              <circle cx="17.5" cy="17.5" r="2.5"></circle>
            </svg>
            <span>Avg. Weight Change (% of bodyweight)</span>
          </p>
          <div className="summary-card__value-group">
            <h3 className="summary-card__value">
              {summaryData.avg_change_prc &&
                toSignedString(summaryData.avg_change_prc, 2)}
            </h3>
            <span className="summary-card__subtitle">% / week</span>
          </div>
        </li>
        <li className="summary-card">
          <p className="summary-card__header">
            <svg
              className="summary-card__icon"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
            </svg>
            <span>Avg. Calorie Deficit / Surplus (est.) </span>
          </p>
          <div className="summary-card__value-group">
            {/* Convert to signed amount format  */}
            <h3 className="summary-card__value">
              {summaryData.avg_net_calories &&
                toSignedString(summaryData.avg_net_calories)}
            </h3>
            <span className="summary-card__subtitle">kcal / day</span>
          </div>
        </li>
      </ul>

      {/* <!-- Goal Progress evaluation box --> */}
      {/* {props.goal_progress && (
        <p className="summary_evaluation">
          <svg
            className="summary__icon summary_icon--evaluation"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"></path>
          </svg>
          <span>{props.goal_progress}</span>
        </p>
      )} */}
    </section>
  );
}
