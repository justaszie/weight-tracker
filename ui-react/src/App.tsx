import { useState, useEffect } from 'react'

import Header from './components/Header'
import Main from './components/Main'

import type { Goal } from './types/goal'

const DEFAULT_GOAL: Goal = 'maintain';

function App() {

  const goalStored: Goal | null = localStorage.getItem('goalSelected') as Goal;
  const [goalSelected, setGoalSelected] = useState(goalStored ?? DEFAULT_GOAL);

  // On first render, persist the goal value from the state to local storage
  useEffect(() => {
    localStorage.setItem('goalSelected', goalSelected);
  }, []);

  function handleGoalChange(goalSelection: Goal) {
    localStorage.setItem('goalSelected', goalSelection);
    setGoalSelected(goalSelection);
  }

  return (
    <div className="page">
      <Header
        handleGoalChange={handleGoalChange}
        goalSelected={goalSelected}
          // goalSelected="maintain"
        />
      <Main />
    </div>
  )
}

export default App;
