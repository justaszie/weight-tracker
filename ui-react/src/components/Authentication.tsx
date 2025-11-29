import { useState } from "react";
import type { AuthenticationProps } from "@/types/props";

import Login from "@/components/Login";
import SignUp from "@/components/SignUp";

export default function Authentication(props: AuthenticationProps) {
  const [authStage, setAuthStage] = useState<string>("login");

  function switchToSignUp() {
    setAuthStage("signup");
  }

  function switchToLogin() {
    setAuthStage("login");
  }

  return (
    <>
      <header className="header">
        <div className="main-content spaced-out">
          <div>
            <h1 className="header__title">
              <a className="header__home-link" href="/">
                Weight Tracker
              </a>
            </h1>
            <p className="header__subtitle">
              Track your weight changes without a calculator
            </p>
          </div>
        </div>
      </header>
      <div className="main-content">
        {authStage === "login" ? (
          <Login showToast={props.showToast} onSignUpCTAClick={switchToSignUp} />
        ) : (
          <SignUp showToast={props.showToast} onLoginCTAClick={switchToLogin} />
        )}
      </div>
    </>
  );
}
