import { useState, useEffect } from "react";

import Header from "@/components/Header";
import Main from "@/components/Main";
import Toast from "@/components/Toast";
import Login from "@/components/Login";

import { supabase } from "./supabaseClient.ts";

import type { Session } from "@supabase/supabase-js";
import type { Goal } from "@/types/goal";
import type { ToastMessageCategory, ToastMessage } from "@/types/toast";
import { isDataSourceName, type DataSourceName } from "@/types/utils";

const DEFAULT_GOAL = "maintain";
const DEFAULT_DATA_SOURCE = "gfit";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const API_PREFIX = import.meta.env.VITE_API_PREFIX as string;

function App() {
  const [session, setSession] = useState<Session | null>(null);

  const goalStored: Goal | null = localStorage.getItem("goalSelected") as Goal;
  const [goalSelected, setGoalSelected] = useState<Goal>(
    goalStored ?? DEFAULT_GOAL
  );
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [dataSyncComplete, setDataSyncComplete] = useState<boolean>(false);

  function showToast(category: ToastMessageCategory, message: string) {
    setToast({ category, message });
    setTimeout(() => {
      setToast(null);
    }, 2000);
  }

  async function triggerDataSync(data_source?: DataSourceName, ) {
    try {
      if (!session) {
        console.log(`Session value: ${session}`);
        throw new Error("Must be signed in to get data");
      }
      const response = await fetch(`${API_BASE_URL}/${API_PREFIX}/sync-data`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data_source: data_source || DEFAULT_DATA_SOURCE,
        }),
      });
      if (!response.ok) {
        const body = await response.json();
        // If auth is needed, launch google auth flow
        if (response.status === 401) {
          let authUrl = `${API_BASE_URL}${body.auth_url}`;
          window.location.replace(authUrl);
          return;
        }
        const errorMessage =
          "message" in body ? body["message"] : "Error while syncing data";
        throw new Error(errorMessage);
      }
      const body = await response.json();
      if (body.status === "sync_success") {
        // If sync success,  update state to trigger re-rendering
        markDataSyncComplete();
      } else if (
        ["data_up_to_date", "no_data_received", "no_new_data"].includes(
          body.status
        )
      ) {
        showToast("info", body.message);
      } else {
        throw new Error(body.message);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        showToast("error", err.message);
      }
    }
  }

  // Auth checks: using supabase, check if the user is signed in or not
  async function authenticate() {
    let { data } = await supabase.auth.getSession();
    return data.session;
  }

  async function initializeApp() {
    let session = await authenticate();
    setSession(session);

    // Set up a listener that will get auth state updates
    // and update client session accordingly
    supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    // Persist the user's goal value from the state to local storage
    localStorage.setItem("goalSelected", goalSelected);

    // If the request comes from the flow of getting authorization
    // from the data source to get data (e.g. gfit), trigger data sync flow
    const queryParams = new URLSearchParams(window.location.search);
    if (queryParams.get("initiator") === "data_source_auth_success") {
      const dataSource = queryParams.get("source");
      if (dataSource && isDataSourceName(dataSource)) {
        triggerDataSync(dataSource);
      }
    }
  }

  useEffect(() => {
    initializeApp();
  }, []);

  function handleGoalChange(goalSelection: Goal) {
    localStorage.setItem("goalSelected", goalSelection);
    setGoalSelected(goalSelection);
  }

  function markDataSyncComplete() {
    showToast("success", "Data updated successfully");
    setDataSyncComplete(true);
  }

  return (
    <div className="page">
      {session == null ? (
        <Login showToast={showToast} />
      ) : (
        <>
          <Header
            handleGoalChange={handleGoalChange}
            goalSelected={goalSelected}
            user={{
              userId: session.user.id,
              email: session.user.email || null,
            }}
          />
          <Main
            goalSelected={goalSelected}
            session={session}
            handleDataSyncComplete={markDataSyncComplete}
            dataSyncComplete={dataSyncComplete}
            onDataSyncRequest={triggerDataSync}
            showToast={showToast}
          />
        </>
      )}
      {toast && <Toast message={toast.message} category={toast.category} />}
    </div>
  );
}

export default App;
