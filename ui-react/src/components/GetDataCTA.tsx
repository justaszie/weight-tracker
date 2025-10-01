import { useState } from "react";
import type { GetDataCTAProps } from "@/types/props";
import { isDataSourceName } from "@/types/utils";

import { ReactComponent as Spinner} from "@/assets/spinner.svg"

export default function GetDataCTA(props: GetDataCTAProps) {
  const [isLoading, setIsLoading] = useState(false);

  async function handleCTAClick(event: React.MouseEvent<HTMLButtonElement>) {
    setIsLoading(true);
    const source = event.currentTarget.dataset.dataSource;
    event.preventDefault();
    if (isDataSourceName(source)) {
      await props.onDataSyncRequest(source);
    }
    setIsLoading(false);
  }

  const Icon = props.srcIcon;

  return (
    <button
      data-data-source={props.dataSource}
      onClick={handleCTAClick}
      disabled={ isLoading ? true : false}
      className={`get-data__cta ${isLoading ? 'get-data__cta--loading' : ''}`}
    >
      { isLoading ? <Spinner className="spinner spinner--cta"/> : (
          <>
            <Icon className="get-data__cta-icon" />
            <span>{props.ctaText}</span>
          </>
        )
      }
    </button>
  );
}
