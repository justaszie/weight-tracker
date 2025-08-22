import type { Goal } from '../types/goal.ts';
type HeaderPropsType = {
    handleGoalChange: (goal: Goal) => void;
    goalSelected: Goal;
};

export default function Header(props: HeaderPropsType) {

    function handleGoalClick(event: React.MouseEvent<HTMLAnchorElement>): void {
        event.preventDefault();
        const optionClicked = event.currentTarget;
        const goalSelection = optionClicked.dataset.goal as Goal;
        props.handleGoalChange(goalSelection)
    }
    return (
       <header className="header">
            <div className="main-content spaced-out">
                <div>
                    <h1 className="header__title">
                        <a className="header__home-link" href="{{ url_for('home') }}">Weight Tracker</a>
                    </h1>
                    <p className="header__subtitle">
                        Track your weight changes without a calculator
                    </p>
                </div>
                <div className="goal-selection">
                    <p className="goal-selection__intro">What's your goal?</p>
                    <ul className="goal-selection__container">
                        <li>
                            <a data-goal="lose" onClick={handleGoalClick} className={`goal-selection__cta ${props.goalSelected === 'lose' ? 'goal-selection__cta--active' : ''}`}
                                // href="{{ url_for('tracker', filter=filter, weeks_limit=weeks_limit, date_to=date_to, date_from=date_from, goal='lose') }}"
                            href='#'
                            >
                                {/* <!-- Lose SVG --> */}
                                <svg className=" goal-selection__icon" xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                    strokeLinecap="round" strokeLinejoin="round"
                                    >
                                    <path
                                        d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z">
                                </path>
                                </svg>
                                <span className="goal-selection__label">Losing Fat</span>
                            </a>
                        </li>
                        <li>
                            <a data-goal="gain" onClick={handleGoalClick} className={`goal-selection__cta ${props.goalSelected === 'gain' ? 'goal-selection__cta--active' : ''}`}
                                // href="{{ url_for('tracker', filter=filter, weeks_limit=weeks_limit, date_to=date_to, date_from=date_from, goal='gain') }}"
                                href="#">
                                <svg className=" goal-selection__icon" xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                    strokeLinecap="round" strokeLinejoin="round"
                                    >
                                    <path d="M14.4 14.4 9.6 9.6"></path>
                                    <path
                                        d="M18.657 21.485a2 2 0 1 1-2.829-2.828l-1.767 1.768a2 2 0 1 1-2.829-2.829l6.364-6.364a2 2 0 1 1 2.829 2.829l-1.768 1.767a2 2 0 1 1 2.828 2.829z">
                                    </path>
                                    <path d="m21.5 21.5-1.4-1.4"></path>
                                    <path d="M3.9 3.9 2.5 2.5"></path>
                                    <path
                                        d="M6.404 12.768a2 2 0 1 1-2.829-2.829l1.768-1.767a2 2 0 1 1-2.828-2.829l2.828-2.828a2 2 0 1 1 2.829 2.828l1.767-1.768a2 2 0 1 1 2.829 2.829z">
                                    </path>
                                </svg>
                                <span className="goal-selection__label">Gaining Muscle</span>
                            </a>
                        </li>
                        <li>
                            <a data-goal="maintain" onClick={handleGoalClick} className={`goal-selection__cta ${props.goalSelected === 'maintain' ? 'goal-selection__cta--active' : ''}`}
                                // href="{{ url_for('tracker', filter=filter, weeks_limit=weeks_limit, date_to=date_to, date_from=date_from, goal='maintain') }}"
                                href="#">
                                <svg className=" goal-selection__icon" xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                    strokeLinecap="round" strokeLinejoin="round" >
                                    <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"></path>
                                    <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"></path>
                                    <path d="M7 21h10"></path>
                                    <path d="M12 3v18"></path>
                                    <path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"></path>
                                </svg>
                                <span className="goal-selection__label">Maintaining</span>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </header>
    );
}