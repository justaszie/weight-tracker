import { useEffect, useState } from "react";

import type { FiltersSelection } from "../types/filter";
import type { Goal } from "../types/goal";

type WeeklyDataTablePropsType = {
    filterValues?: FiltersSelection;
    goalSelected: Goal;
}

type WeeklyDataUrlParamsType = {
    weeks_limit?: string;
    date_to?: string;
    date_from?: string;
    goal: Goal;
}

export default function WeeklyDataTable(props: WeeklyDataTablePropsType) {
    const [weeklyData, setWeeklyData] = useState([])
    // TODO - fetch weekly aggregate data and map entries to <tr> elements
    function weekToRow(weekEntry) {
        const { result } = weekEntry;
        return (
            <tr key={weekEntry['week_start']} className="data-table__row">
                            <td className="data-table__cell">{ weekEntry['week_start'] }</td>
                            <td className="data-table__cell">{ weekEntry['avg_weight'] } kg</td>
                            <td
                                // TODO - Add conditional positive / negative / neutral classes
                                className={`data-table__cell  ${result === 'positive' ? "data-table__cell--positive" : ''}
                                ${result === 'negative' ? "data-table__cell--negative" : ""}`}>
                                { weekEntry['weight_change'] } kg</td>
                            <td
                                className={`data-table__cell  ${result === 'positive' ? "data-table__cell--positive": ""}
                                ${result === 'negative' ? "data-table__cell--negative" : ""}`}>
                                { weekEntry['weight_change_prc'] } %</td>
                            <td
                                className={`data-table__cell = ${result === 'positive' ? "data-table__cell--positive": ""}
                                ${result === 'negative' ? " data-table__cell--negative" : ""}`}>
                                { weekEntry['net_calories'] } kcal / day</td>
                        </tr>
        )
    }

    // Fetching data when filter values change
    useEffect(() => {
        const { weeksLimit, dateTo, dateFrom } = props.filterValues;
        const urlParams: WeeklyDataUrlParamsType = { goal: props.goalSelected }
        if (weeksLimit) {
            urlParams['weeks_limit'] = String(weeksLimit);
        }
        if (dateFrom) {
            urlParams['date_from'] = dateFrom;
        }
        if (dateTo) {
            urlParams['date_to'] = dateTo;
        }

        const weeklyDataURL = new URL('http://localhost:5040/api/weekly-aggregates');
        weeklyDataURL.search = new URLSearchParams(urlParams).toString();
        fetch(weeklyDataURL)
            .then(response => response.json())
            .then(data => {
                setWeeklyData(data['weekly_data'])
            })
    }, [props]);

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
                        {
                            weeklyData.length > 0 &&
                            <tbody>
                                {weeklyData.map(weekToRow)}
                            </tbody>
                        }
                    </table>
                </section>
    )
}