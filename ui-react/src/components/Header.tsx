import { supabase } from "@/supabaseClient";
import type { HeaderProps } from "@/types/props";
import type { Goal } from "@/types/goal";

export default function Header(props: HeaderProps) {
  function handleGoalClick(event: React.MouseEvent<HTMLAnchorElement>): void {
    event.preventDefault();

    const optionClicked = event.currentTarget;
    const goalSelection = optionClicked.dataset.goal as Goal;
    props.handleGoalChange(goalSelection);
  }

  // function isDemoMode() {
  //   return import.meta.env.VITE_DEMO_MODE == "true";
  // }

  async function handleSignOut() {
    // Log user out of all sessions
    await supabase.auth.signOut();
  }

  return (
    <header className="header">
      <div className="main-content spaced-out">
        <div>
          <h1 className="header__title">
            <a className="header__home-link" href="/">
              Weight Tracker
            </a>
            {/* {isDemoMode() && <span className="demo-tag">Demo Mode</span>} */}
          </h1>
          <p className="header__subtitle">
            Track your weight changes without a calculator
          </p>
          <div className="profile">
            <div className="profile__header">
              <svg
                className="profile__icon"
                viewBox="0 0 20 20"
                version="1.1"
                xmlns="http://www.w3.org/2000/svg"
              >
                <g
                  id="Page-1"
                >
                  <g
                    id="Dribbble-Light-Preview"
                    transform="translate(-380.000000, -2159.000000)"
                    // fill="#FFF"
                  >
                    <g id="icons" transform="translate(56.000000, 160.000000)">
                      <path
                        d="M334,2011 C337.785,2011 340.958,2013.214 341.784,2017 L326.216,2017 C327.042,2013.214 330.215,2011 334,2011 M330,2005 C330,2002.794 331.794,2001 334,2001 C336.206,2001 338,2002.794 338,2005 C338,2007.206 336.206,2009 334,2009 C331.794,2009 330,2007.206 330,2005 M337.758,2009.673 C339.124,2008.574 340,2006.89 340,2005 C340,2001.686 337.314,1999 334,1999 C330.686,1999 328,2001.686 328,2005 C328,2006.89 328.876,2008.574 330.242,2009.673 C326.583,2011.048 324,2014.445 324,2019 L344,2019 C344,2014.445 341.417,2011.048 337.758,2009.673"
                        id="profile-[#1336]"
                      ></path>
                    </g>
                  </g>
                </g>
              </svg>
              <p className="profile__email">{props.user.email}</p>
            </div>
            <a className="profile__signout" href="#" onClick={handleSignOut}>
              Sign Out
            </a>
          </div>
        </div>
        <div className="goal-selection">
          <p className="goal-selection__intro">What's your goal?</p>
          <ul className="goal-selection__container">
            <li>
              <a
                data-goal="lose"
                onClick={handleGoalClick}
                className={`goal-selection__cta ${
                  props.goalSelected === "lose"
                    ? "goal-selection__cta--active"
                    : ""
                }`}
                href="#"
              >
                {/* <!-- Lose SVG --> */}
                <svg
                  className="goal-selection__icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
                </svg>
                <span className="goal-selection__label">Losing Fat</span>
              </a>
            </li>
            <li>
              <a
                data-goal="gain"
                onClick={handleGoalClick}
                className={`goal-selection__cta ${
                  props.goalSelected === "gain"
                    ? "goal-selection__cta--active"
                    : ""
                }`}
                href="#"
              >
                <svg
                  className=" goal-selection__icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M14.4 14.4 9.6 9.6"></path>
                  <path d="M18.657 21.485a2 2 0 1 1-2.829-2.828l-1.767 1.768a2 2 0 1 1-2.829-2.829l6.364-6.364a2 2 0 1 1 2.829 2.829l-1.768 1.767a2 2 0 1 1 2.828 2.829z"></path>
                  <path d="m21.5 21.5-1.4-1.4"></path>
                  <path d="M3.9 3.9 2.5 2.5"></path>
                  <path d="M6.404 12.768a2 2 0 1 1-2.829-2.829l1.768-1.767a2 2 0 1 1-2.828-2.829l2.828-2.828a2 2 0 1 1 2.829 2.828l1.767-1.768a2 2 0 1 1 2.829 2.829z"></path>
                </svg>
                <span className="goal-selection__label">Gaining Muscle</span>
              </a>
            </li>
            <li>
              <a
                data-goal="maintain"
                onClick={handleGoalClick}
                className={`goal-selection__cta ${
                  props.goalSelected === "maintain"
                    ? "goal-selection__cta--active"
                    : ""
                }`}
                href="#"
              >
                <svg
                  className=" goal-selection__icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
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
