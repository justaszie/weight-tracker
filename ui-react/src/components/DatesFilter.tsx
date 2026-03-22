import { useEffect, useRef, useState, type ChangeEvent } from "react";
import type { DatesFilterProps } from "@/types/props";

const DEBOUNCE_MS = 450;

function isValidISODate(date: string) {
  return !Number.isNaN(Date.parse(date));
}

type DraftDates = { dateFrom: string; dateTo: string };

export default function DatesFilter(props: DatesFilterProps) {
  const [draft, setDraft] = useState<DraftDates>(() => ({
    dateFrom: props.selectedValues?.dateFrom ?? "",
    dateTo: props.selectedValues?.dateTo ?? "",
  }));

  const handleValueChangeRef = useRef(props.handleValueChange);
  const showToastRef = useRef(props.showToast);
  handleValueChangeRef.current = props.handleValueChange;
  showToastRef.current = props.showToast;

  useEffect(() => {
    setDraft({
      dateFrom: props.selectedValues?.dateFrom ?? "",
      dateTo: props.selectedValues?.dateTo ?? "",
    });
  }, [props.selectedValues?.dateFrom, props.selectedValues?.dateTo]);

  useEffect(() => {
    const id = window.setTimeout(() => {
      const { dateFrom, dateTo } = draft;

      if (dateFrom !== "" && !isValidISODate(dateFrom)) {
        showToastRef.current("error", "Invalid 'date from' value");
        return;
      }
      if (dateTo !== "" && !isValidISODate(dateTo)) {
        showToastRef.current("error", "Invalid 'date to' value");
        return;
      }
      if (
        dateTo !== "" &&
        dateFrom !== "" &&
        dateTo < dateFrom
      ) {
        showToastRef.current("error", "'Date To' must be after 'Date From'");
        return;
      }

      handleValueChangeRef.current({
        dateFrom,
        dateTo,
      });
    }, DEBOUNCE_MS);
    return () => window.clearTimeout(id);
  }, [draft]);

  function handleDateFilterChange(event: ChangeEvent<HTMLInputElement>) {
    const { name, value } = event.target;
    if (name === "date_from") {
      setDraft((prev) => ({ ...prev, dateFrom: value }));
    } else if (name === "date_to") {
      setDraft((prev) => ({ ...prev, dateTo: value }));
    }
  }

  return (
    <div className="dates-filter">
      <label className="dates-filter__label" htmlFor="date_from">
        From
      </label>
      <input
        name="date_from"
        value={draft.dateFrom}
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
        value={draft.dateTo}
        type="date"
        id="date_to"
        className="dates-filter__input"
        onChange={handleDateFilterChange}
      />
    </div>
  );
}
