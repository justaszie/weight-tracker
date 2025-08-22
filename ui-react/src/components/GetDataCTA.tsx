import React from "react";

type GetDataCTAPropsType = {
  ctaText: string;
  srcIcon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  dataSource: string;
  // handleDataSyncComplete: () => void;
  // showToast: (category: string, message: string) => void;
  onDataSyncRequest: (data_source?: string) => void;
};

export default function GetDataCTA(props: GetDataCTAPropsType) {
  // const SERVER_BASE_URL = "http://localhost:5040";

  function handleCTAClick(event: React.MouseEvent<HTMLAnchorElement>) {
    const source = event.currentTarget.dataset.dataSource;
    event.preventDefault();
    props.onDataSyncRequest(source);
  }


  //   // Send POST request and wait for response. Redirect if needed.
  //   let response = await fetch(`${SERVER_BASE_URL}/api/sync-data`, {
  //     method: "POST",
  //     headers: {
  //       "Content-Type": "application/json",
  //     },
  //     body: JSON.stringify({ data_source: source }),
  //   });
  //   let body = await response.json();
  //   if (body.status === "auth_needed") {
  //     window.location.replace(`${SERVER_BASE_URL}${body.auth_url}`);
  //   } else if (body.status === "sync_success") {
  //     props.handleDataSyncComplete();
  //   } else if (body.status === "data_up_to_date") {
  //     props.showToast("info", body.message);
  //   } else if (body.status === "no_data_received") {
  //     props.showToast("info", body.message);
  //   } else {
  //     props.showToast("error", body.message);
  //   }
  // }

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
