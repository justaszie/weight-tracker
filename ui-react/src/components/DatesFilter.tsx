import type { ChangeEvent } from "react";
import type { DatesFilterProps } from "@/types/props";

function isValidISODate(date: string) {
  return !Number.isNaN(Date.parse(date));
}

export default function DatesFilter(props: DatesFilterProps) {
  function handleDateFilterChange(event: ChangeEvent<HTMLInputElement>) {
    let { dateFrom, dateTo } = props.selectedValues ?? {};

    if (event.target.name === "date_from") {
      dateFrom = event.target.value;
      if (dateFrom !== "" && !isValidISODate(dateFrom)) {
        props.showToast("error", "Invalid 'date from' value");
        return;
      }
    } else if (event.target.name === "date_to") {
      dateTo = event.target.value;
      if (dateTo != "" && !isValidISODate(dateTo)) {
        props.showToast("error", "Invalid 'date to' value");
        return;
      }
      if (dateTo != "" && dateFrom && dateFrom != "" && dateTo < dateFrom) {
        props.showToast("error", "'Date To' must be after 'Date From'");
        return;
      }
    }

    props.handleValueChange({
      dateFrom: dateFrom ?? "",
      dateTo: dateTo ?? "",
    });
  }

  return (
    <div className="dates-filter">
      <label className="dates-filter__label" htmlFor="date_from">
        From
      </label>
      <input
        name="date_from"
        value={props.selectedValues?.dateFrom ?? ""}
        type="date"
        id="date_from"
        className="dates-filter__input"
        onChange={handleDateFilterChange}
      />
      <label className="dates-filter__label" htmlFor="date_to">
        To
      </label>
      <input
        name="date_to"
        value={props.selectedValues?.dateTo ?? ""}
        type="date"
        id="date_to"
        className="dates-filter__input"
        onChange={handleDateFilterChange}
      />
    </div>
  );
}
