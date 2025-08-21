export type Filter = 'weeks' | 'dates';

export type FiltersSelection = {
    dateFrom?: string;
    dateTo?: string;
    weeksLimit?: number;
}
