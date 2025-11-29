import { useState } from "react";
import { supabase } from "@/supabaseClient.ts";

import type { SignUpProps } from "@/types/props";

import { ReactComponent as Spinner } from "@/assets/spinner.svg";

export default function Login(props: SignUpProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");

  async function handleSignUp(event: React.FormEvent) {
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
      const { error } = await supabase.auth.signUp({
        email: email,
        password: password
      })

      if (error) {
        props.showToast("error", error.message);
      } else {
        props.showToast("success", "Welcome!");
      }
    }
    setIsLoading(false);
  }

  return (
    <>
        {isLoading ? (
          <Spinner className="spinner" />
        ) : (
          <form onSubmit={handleSignUp} className="signup">
            <h2 className="signup__header">Sign Up</h2>
            <div className="signup__row">
              <label htmlFor="signup-email" className="signup__label">
                Email
              </label>
              <input
                className="signup__input"
                type="email"
                id="signup-email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="signup__row">
              <label htmlFor="signup-password" className="signup__label">
                Password
              </label>
              <input
                id="signup-password"
                className="signup__input"
                type="password"
                name="password"
              />
            </div>
            <div className="signup__actions">
              <button className="signup__cta signup__cta--primary" type="submit">
                Sign Up
              </button>
              <button className="signup__cta signup__cta--secondary" type="button" onClick={props.onLoginCTAClick}>
                Log In
              </button>
            </div>
          </form>
        )}
    </>
  );
}
