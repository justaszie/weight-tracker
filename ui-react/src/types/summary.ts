export type SummaryUrlParams = {
    weeks_limit?: string;
    date_to?: string;
    date_from?: string;
}

export type SummaryData = {
    total_change?: number;
    avg_change?: number;
    avg_change_prc?: number;
    avg_net_calories?: number;
}