import type { ChangeEvent } from "react";
import type { FiltersSelection } from "../types/filter";

type WeeksFilterPropsType = {
    selectedValues:  { weeksLimit?: number };
    handleSelectionChange: (newSelection: FiltersSelection) => void
};



export default function WeeksFilter(props: WeeksFilterPropsType) {
    function handleWeeksLimitChange(event: ChangeEvent<HTMLInputElement>) {
        const newValue: number = Number(event.target.value);
        props.handleSelectionChange({weeksLimit: newValue});
    }

  return (
    <div className="weeks-filter">
      <svg
        className="weeks-filter__icon"
        fill="currentColor"
        stroke="none"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid meet"
      >
        <path d="M0 24h22V2h-4V0h-2v2H6V0H4v2H0zm16-10v-2h2v2zm2 1v2h-2v-2zm-5 2v-2h2v2zm2 1v2h-2v-2zm-2-4v-2h2v2zm-3 3v-2h2v2zm2 1v2h-2v-2zm-2-4v-2h2v2zm-3 3v-2h2v2zm2 1v2H7v-2zm-2-4v-2h2v2zm-1 1v2H4v-2zm-2 3h2v2H4zM4 4v2h2V4h10v2h2V4h2v4H2V4z" />
      </svg>
      <label className="weeks-filter__label" htmlFor="weeks_limit">
        Weeks:
      </label>
      <input
        name="weeks_limit"
        type="number"
        value={props.selectedValues.weeksLimit}
        id="weeks_limit"
        className="weeks-filter__input"
        onChange={handleWeeksLimitChange}
      />
      {/* <button className="weeks-filter__submit">
        <svg
          className="weeks-filter__icon"
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
