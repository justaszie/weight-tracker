import React from 'react'

type GetDataCTAPropsType = {
    ctaText: string;
    srcIconElement: React.ReactElement;
    dataSource: string;
    handleDataSyncComplete: () => void;
}

export default function GetDataCTA(props: GetDataCTAPropsType) {
    const SERVER_BASE_URL = 'http://localhost:5040'

    async function handleCTAClick(event: React.MouseEvent<HTMLAnchorElement>) {
        event.preventDefault();
        const source = event.currentTarget.dataset.dataSource;

        // Send POST request and wait for response. Redirect if needed.
        let response = await fetch(`${SERVER_BASE_URL}/api/sync-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({data_source: source}),
        });
        let body = await response.json();
        if (body.status === 'auth_needed') {
            window.location.replace(`${SERVER_BASE_URL}${body.auth_url}`);
        } else if (body.status === 'sync_success') {
            props.handleDataSyncComplete();
        }
        // Else: any other info or error message, display toast component.

    }
    return (
        <a data-data-source={props.dataSource} href="#" onClick={handleCTAClick} className="get-data__cta">
            {props.srcIconElement}
            <span>{props.ctaText}</span>
        </a>
    )
}