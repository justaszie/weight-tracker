import GetDataSelection from "./GetDataSelection";
import ManageDataCTA from "./ManageDataCTA";

import type { NoDataViewProps } from "@/types/props";

export default function NoDataView(props: NoDataViewProps) {
  return (
    <section className="no-data-view">
      <div className="no-data-view__image-container">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="no-data-view__image"
          preserveAspectRatio="xMidYMid meet"
        >
          <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"></path>
          <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"></path>
          <path d="M7 21h10"></path>
          <path d="M12 3v18"></path>
          <path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"></path>
        </svg>
      </div>
      <header className="no-data-view__header">No weight data found</header>
      <p className="no-data-view__description">
        Start tracking your weight journey by getting data <br /> from the
        source of your choice:
      </p>
      <div className="get-data">
        <GetDataSelection onCTAClick={props.onGetDataCTAClick} />
        <ManageDataCTA ctaText="+ Add Data" onCTAClick={props.onAddDataCTAClick}/>
      </div>
    </section>
  );
}
