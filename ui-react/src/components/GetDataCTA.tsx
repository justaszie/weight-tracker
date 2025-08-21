type GetDataCTAPropsType = {
    ctaText: string;
    srcIconElement: React.ReactElement;
}

export default function GetDataCTA(props: GetDataCTAPropsType) {
    return (
        <a href="#" className="get-data__cta">
            {props.srcIconElement}
            <span>{props.ctaText}</span>
        </a>
    )
}