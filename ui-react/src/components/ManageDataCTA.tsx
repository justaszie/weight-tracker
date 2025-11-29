import type { ManageDataCTAProps } from "@/types/props";

export default function ManageDataCTA(props: ManageDataCTAProps) {

  async function handleCTAClick(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    props.onCTAClick();
  }

  return (
    <button onClick={handleCTAClick} className={`get-data__cta`}>
      <span>{props.ctaText}</span>
    </button>
  );
}
