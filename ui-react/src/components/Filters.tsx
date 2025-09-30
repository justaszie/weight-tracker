import { useState } from 'react';
import type { FiltersProps } from "@/types/props";
import type { Filter } from "@/types/filter"

import WeeksFilter from './WeeksFilter'
import DatesFilter from './DatesFilter'

const DEFAULT_FILTER_CHOICE = 'weeks';

export default function Filters(props: FiltersProps) {
    const [filterChoice, setFilterChoice] = useState(DEFAULT_FILTER_CHOICE);

    function handleFilterChoiceChange(event: React.MouseEvent<HTMLAnchorElement>) {
        event.preventDefault();
        const filterChoice: Filter = event.currentTarget.dataset.filter as Filter;
        props.resetFilterValues();
        setFilterChoice(filterChoice);
    }

    return (
        <>
            <section className="filter-selection">
                <a href="#" onClick={handleFilterChoiceChange} data-filter='weeks' className={`filter-option ${filterChoice === 'weeks' ? 'filter-option--active' : ''}`}> Filter by Weeks</a>
                <a href="#" onClick={handleFilterChoiceChange} data-filter='dates' className={`filter-option ${filterChoice === 'dates' ? 'filter-option--active' : ''}`}> Filter by Days</a>
            </section>
            {
                filterChoice === 'weeks'
                ? <WeeksFilter
                    handleValueChange={props.handleWeeksFilterChange}
                    selectedValues={props.weeksFilterValues}
                    showToast={props.showToast}
                    />
                : <DatesFilter
                    handleValueChange={props.handleDatesFilterChange}
                    selectedValues={{
                        dateFrom: props.datesFilterValues?.dateFrom ?? '',
                        dateTo: props.datesFilterValues?.dateTo ?? '',
                    }}
                    showToast={props.showToast}
                    />
            }
        </>
    );
}