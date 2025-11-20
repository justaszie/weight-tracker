import { ReactComponent as GoogleIcon } from "@/assets/GoogleIcon.svg";
import { ReactComponent as MFPIcon } from "@/assets/MFPIcon.svg";

import GetDataCTA from "./GetDataCTA";

import type { DataSourceCTA } from "@/types/utils";
import type { GetDataSelectionProps } from "@/types/props";

const dataSources: DataSourceCTA[] = [
    { srcName: "gfit", ctaText: "Get Google Fit Data", icon: GoogleIcon },
    { srcName: "mfp", ctaText: "Get MyFitnessPal Data", icon: MFPIcon },
  ];

export default function GetDataSelection(props: GetDataSelectionProps) {
  return (
    <div className="get-data__selection">
      {dataSources.map((src) => (
        <GetDataCTA
          key={src.srcName}
          dataSource={src.srcName}
          ctaText={src.ctaText}
          srcIcon={src.icon}
          onDataSyncRequest={props.onDataSyncRequest}
        />
      ))}
      </div>
  )
}