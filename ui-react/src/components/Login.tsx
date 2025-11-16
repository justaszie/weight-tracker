import { useState } from "react";
import { supabase } from "@/supabaseClient.ts";

import type { LoginProps } from "@/types/props";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

export default function Login(props: LoginProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault();
    let formData: FormData = new FormData(
      event.currentTarget as HTMLFormElement
    );
    let email = formData.get("email") as string;
    let password = formData.get("password") as string;

    setIsLoading(true);
    if (!email || !password) {
      props.showToast("error", "Both email and password are required");
    } else {
      const { error } = await supabase.auth.signInWithPassword({
        email: email,
        password: password,
      });

      if (error) {
        props.showToast("error", error.message);
      } else {
        props.showToast("success", "Welcome back");
      }
    }
    setIsLoading(false);
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
        {isLoading ? (
          <Spinner className="spinner" />
        ) : (
          <form onSubmit={handleLogin} className="signin">
            <h2 className="signin__header">Please Sign In</h2>
            <div className="signin__row">
              <label htmlFor="signin-email" className="signin__label">
                Email
              </label>
              <input
                className="signin__input"
                type="email"
                id="signin-email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="signin__row">
              <label htmlFor="signin-password" className="signin__label">
                Password
              </label>
              <input
                id="signin-password"
                className="signin__input"
                type="password"
                name="password"
              />
            </div>
            <div className="signin__row">
              <button className="signin__cta" type="submit">
                Sign In
              </button>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
