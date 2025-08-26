export type Filter = 'weeks' | 'dates';

// export type FiltersSelection = {
//     dateFrom?: string;
//     dateTo?: string;
//     weeksLimit?: number;
// }

export type WeeksFilterValues = {
    weeksLimit?: number;
}

export type DatesFilterValues = {
    dateFrom?: string;
    dateTo?: string;
}
