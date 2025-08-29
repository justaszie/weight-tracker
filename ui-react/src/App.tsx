import { useState, useEffect } from "react";

import Header from "@/components/Header";
import Main from "@/components/Main";
import Toast from "@/components/Toast";

import type { Goal } from "@/types/goal";
import type { ToastMessageCategory, ToastMessage } from "@/types/toast";
import { isDataSourceName, type DataSourceName } from "@/types/utils";

const DEFAULT_GOAL = "maintain";
const DEFAULT_DATA_SOURCE = "gfit";
const SERVER_BASE_URL = "http://localhost:5040";

function App() {
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

  async function triggerDataSync(data_source?: DataSourceName) {
    try {
      const response = await fetch(`${SERVER_BASE_URL}/api/sync-data`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data_source: data_source || DEFAULT_DATA_SOURCE,
        }),
      });
      if (!response.ok) {
        const body = await response.json();
        const errorMessage =
          "message" in body
            ? body["message"]
            : "Error while syncing data";
        throw new Error(errorMessage);
      }
      const body = await response.json();
      if (body.status === "auth_needed") {
        window.location.replace(`${SERVER_BASE_URL}${body.auth_url}`);
      } else if (body.status === "sync_success") {
        // 2) if sync success,  update state to trigger re-rendering
        markDataSyncComplete();
      } else if (["data_up_to_date", "no_data_received", "no_new_data"].includes(body.status)) {
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

  useEffect(() => {
    // 1) persist the goal value from the state to local storage
    localStorage.setItem("goalSelected", goalSelected);

    // 2) if we come from successful data source authentication, trigger data sync
    const queryParams = new URLSearchParams(window.location.search);
    if (queryParams.get("initiator") === "data_source_auth_success") {
      const dataSource = queryParams.get("source");
      if (dataSource && isDataSourceName(dataSource)) {
        triggerDataSync(dataSource);
      }
    }
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
      <Header handleGoalChange={handleGoalChange} goalSelected={goalSelected} />
      <Main
        goalSelected={goalSelected}
        handleDataSyncComplete={markDataSyncComplete}
        dataSyncComplete={dataSyncComplete}
        onDataSyncRequest={triggerDataSync}
        showToast={showToast}
      />
      {toast && <Toast message={toast.message} category={toast.category} />}
    </div>
  );
}

export default App;
