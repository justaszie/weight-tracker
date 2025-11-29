import { useState } from "react";
import type { AddDataModalProps } from "@/types/props";
import type { ChangeEvent, FormEvent } from "react";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

export default function AddDataModal(props: AddDataModalProps) {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [weightValue, setWeightValue] = useState<string>(props.latestWeight);

  const submitForm = async function (event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);

    // TODO: Call add data, display toast and close the form if success

    setIsLoading(false);
  };

  const dateToday = () => {
    const today = new Date();
    return `${today.getFullYear()}-${today.getMonth()}-${today.getDate()}`;
  };

  function handleWeightChange(event: ChangeEvent<HTMLInputElement>) {
    setWeightValue(event.target.value);
  }

  return (
    <>
      <div className="add-weight">
        <h2 className="add-weight__header"> Add Weight Entry </h2>
        <form className="add-weight__form" onSubmit={submitForm}>
          <label className="add-weight__input-label" htmlFor="weight-input">
            Weight (kg)
          </label>
          {/* TODO - research step size to make it 2 decimal nums */}
          <input
            className="add-weight__input"
            type="number"
            step="0.1"
            name="weight"
            placeholder="Enter weight"
            id="weight-input"
            onChange={handleWeightChange}
            value={weightValue}
          ></input>
          <label className="add-weight__input-label" htmlFor="entry-date-input">
            Date
          </label>
          <input
            className="add-weight__input"
            type="date"
            name="entry-date"
            id="entry-date-input"
            defaultValue={dateToday()}
          ></input>
          <div className="add-weight__actions">
            <button
              className="add-weight__cta add-weight__cta--cancel"
              type="button"
              onClick={props.closeModal}
            >
              Cancel
            </button>
            <button
              className={`add-weight__cta add-weight__cta--confirm ${
                isLoading ? "add-weight__cta--loading" : ""
              }`}
              type="submit"
            >
              {isLoading ? (
                <Spinner className="spinner spinner--cta" />
              ) : (
                <span>Add Weight</span>
              )}
            </button>
          </div>
        </form>
      </div>
      <div className="modal-overlay" onClick={props.closeModal}></div>
    </>
  );
}
