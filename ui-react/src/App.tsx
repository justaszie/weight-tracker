import { useState, useEffect } from "react";

import Header from "./components/Header";
import Main from "./components/Main";

import type { Goal } from "./types/goal";

const DEFAULT_GOAL: Goal = "maintain";

function App() {
  const goalStored: Goal | null = localStorage.getItem("goalSelected") as Goal;

  const [goalSelected, setGoalSelected] = useState<Goal>(
    goalStored ?? DEFAULT_GOAL
  );
  const [dataSyncComplete, setDataSyncComplete] = useState<boolean>(false);

  function triggerDataSync(data_source: string) {
    const SERVER_BASE_URL = "http://localhost:5040";
      // 1) trigger data sync (same as from get button CTA)
      fetch(`${SERVER_BASE_URL}/api/sync-data`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ data_source: data_source }),
      })
        .then((response) => response.json())
        .then((body) => {
          if (body.status === "auth_needed") {
            window.location.replace(`${SERVER_BASE_URL}${body.auth_url}`);
          } else if (body.status === "sync_success") {
            // 2) if sync success,  update state to trigger re-rendering
            markDataSyncComplete();
          }
        });
  }
  useEffect(() => {
    // 1) persist the goal value from the state to local storage
    localStorage.setItem("goalSelected", goalSelected);

    // 2) if we come from specific location, trigger some actions
    const queryParams = new URLSearchParams(window.location.search);
    if (queryParams.get("initiator") === "data_source_auth_success") {
      const dataSource = queryParams.get("source");
      if (dataSource != null) {
        triggerDataSync(dataSource);
      }
    }
  }, []);

  function handleGoalChange(goalSelection: Goal) {
    localStorage.setItem("goalSelected", goalSelection);
    setGoalSelected(goalSelection);
  }

  function markDataSyncComplete() {
    setDataSyncComplete(true);
  }

  return (
    <div className="page">
      <Header
        handleGoalChange={handleGoalChange}
        goalSelected={goalSelected}
        // goalSelected="maintain"
      />
      <Main
        goalSelected={goalSelected}
        handleDataSyncComplete={markDataSyncComplete}
      />
    </div>
  );
}

export default App;
