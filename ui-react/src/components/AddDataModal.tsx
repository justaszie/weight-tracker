import { useState } from "react";
import type { AddDataModalProps } from "@/types/props";
import type { ChangeEvent, FormEvent } from "react";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

export default function AddDataModal(props: AddDataModalProps) {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [weightValue, setWeightValue] = useState<string>(props.latestWeight);

  const submitForm = async function (event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData: FormData = new FormData(
      event.currentTarget as HTMLFormElement
    );

    let entryDate = formData.get('entry-date')

    if (entryDate && entryDate > dateToday()) {
      props.showToast('error', 'Date cannot be in the future');
      return
    }

    setIsLoading(true);
    const route_url = `${API_BASE_URL}/${API_PREFIX}/daily-entry`;
    let result = await fetch(route_url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${props.session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        entry_date: formData.get("entry-date"),
        weight: formData.get("weight"),
      }),
    });

    if (result.ok) {
      props.showToast(
        "success",
        `Entry added for ${formData.get("entry-date")}`
      );
      props.closeModal();
      props.handleDataUpdate();
    } else if (result.status === 409) {
      const body = await result.json();
      const errorMessage =
        "detail" in body
          ? body["detail"]
          : "Entry with that data already exists";
      props.showToast("error", errorMessage);
    } else {
      const body = await result.json();
      let errorMessage = body?.detail[0].msg;
      props.showToast("error", errorMessage);
    }

    setIsLoading(false);
  };

  const dateToday = () => {
    const today = new Date();
    return today.toISOString().split("T")[0];
  };

  function handleWeightChange(event: ChangeEvent<HTMLInputElement>) {
    setWeightValue(event.target.value);
  }

  return (
    <>
      <div className="add-weight">
        <h2 className="add-weight__header"> Add Weight Entry </h2>
        <form className="add-weight__form" onSubmit={submitForm}>
          <label className="add-weight__input-label" htmlFor="entry-date-input">
            Date
          </label>
          <input
            className="add-weight__input"
            type="date"
            name="entry-date"
            id="entry-date-input"
            required
            max={dateToday()}
            defaultValue={dateToday()}
          ></input>
          <label className="add-weight__input-label" htmlFor="weight-input">
            Weight (kg)
          </label>
          <input
            className="add-weight__input"
            type="number"
            step="0.01"
            name="weight"
            placeholder="Enter weight"
            id="weight-input"
            min="1"
            onChange={handleWeightChange}
            value={weightValue}
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
