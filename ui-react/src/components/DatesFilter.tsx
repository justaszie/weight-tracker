import { ChangeEvent } from "react";
import type { FiltersSelection } from "../types/filter";

type DatesFilterPropsType = {
  selectedValues: { dateTo?: string; dateFrom?: string };
  handleSelectionChange: (newSelection: FiltersSelection) => void;
};

export default function DatesFilter(props: DatesFilterPropsType) {
  function handleDateFilterChange(event: ChangeEvent<HTMLInputElement>) {
    // console.log(props.selectedValues);

    let { dateFrom, dateTo } = props.selectedValues;
    if (event.target.name === "date_from") {
      dateFrom = event.target.value;
    } else if (event.target.name === "date_to") {
      dateTo = event.target.value;
    }

    props.handleSelectionChange({
      dateFrom,
      dateTo,
    });
  }

  return (
    <div className="dates-filter">
      <label className="dates-filter__label" htmlFor="date_from">
        From
      </label>
      <input
        name="date_from"
        value={props.selectedValues.dateFrom}
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
        value={props.selectedValues.dateTo}
        type="date"
        id="date_to"
        className="dates-filter__input"
        onChange={handleDateFilterChange}
      />
      {/* <button className="dates-filter__submit">
        <svg
          className="dates-filter__icon"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
        </svg>
        <span>Apply Filter</span>
      </button> */}
    </div>
  );
}
