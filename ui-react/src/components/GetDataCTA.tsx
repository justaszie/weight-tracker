import React from "react";
import type { GetDataCTAProps } from "@/types/props";
import { isDataSourceName } from "@/types/utils";

export default function GetDataCTA(props: GetDataCTAProps) {
  function handleCTAClick(event: React.MouseEvent<HTMLAnchorElement>) {
    const source = event.currentTarget.dataset.dataSource;
    event.preventDefault();
    if (isDataSourceName(source)) {
      props.onDataSyncRequest(source);
    }
  }

  const Icon = props.srcIcon;

  return (
    <a
      data-data-source={props.dataSource}
      href="#"
      onClick={handleCTAClick}
      className="get-data__cta"
    >
      <Icon className="get-data__cta-icon" />
      <span>{props.ctaText}</span>
    </a>
  );
}
