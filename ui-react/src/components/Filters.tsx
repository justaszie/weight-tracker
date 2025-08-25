import { useState } from 'react';
import type { FiltersProps } from "@/types/props";
import type { Filter, FiltersSelection } from "@/types/filter";

import WeeksFilter from './WeeksFilter'
import DatesFilter from './DatesFilter'

const DEFAULT_FILTER_SELECTION = 'weeks'

export default function Filters(props: FiltersProps) {
    const [filterSelected, setFilterSelected] = useState(DEFAULT_FILTER_SELECTION);

    function handleFilterSelectionChange(event: React.MouseEvent<HTMLAnchorElement>) {
        event.preventDefault();
        const filterSelection: Filter = event.currentTarget.dataset.filter as Filter;
        setFilterSelected(filterSelection);
    }

    return (
        <div className="filters-column">
            <>
                <section className="filter-selection">
                    <a href="#" onClick={handleFilterSelectionChange} data-filter='weeks' className={`filter-option ${filterSelected === 'weeks' ? 'filter-option--active' : ''}`}> Filter by Weeks</a>
                    <a href="#" onClick={handleFilterSelectionChange} data-filter='dates' className={`filter-option ${filterSelected === 'dates' ? 'filter-option--active' : ''}`}> Filter by Days</a>
                </section>
                {
                    filterSelected === 'weeks'
                    ? <WeeksFilter
                        handleSelectionChange={props.handleFiltersSelectionChange}
                        selectedValues={{weeksLimit: props.filtersSelection.weeksLimit}}
                        />
                    : <DatesFilter
                        handleSelectionChange={props.handleFiltersSelectionChange}
                        selectedValues={{
                            dateFrom: props.filtersSelection.dateFrom ?? '',
                            dateTo: props.filtersSelection.dateTo ?? '',
                        }}
                        />
                }
            </>
        </div>
    );
}