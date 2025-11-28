[![Code Quality Check Flow](https://github.com/justaszie/weight-tracker/actions/workflows/backend_code_quality.yaml/badge.svg)](https://github.com/justaszie/weight-tracker/actions/workflows/backend_code_quality.yaml)
[![Testing Flow](https://github.com/justaszie/weight-tracker/actions/workflows/backend_testing.yaml/badge.svg)](https://github.com/justaszie/weight-tracker/actions/workflows/backend_testing.yaml)

# Weight Tracker - Full Stack Portfolio Project

This is a full-stack weight tracking application that:
- Fetches weight data from external sources (Google Fit API),
- Cleans, stores, and aggregates it
- Presents weekly trends and weight goal-based insights in a modern web UI.

I built it as a portfolio project to demonstrate end-to-end skills: full-stack development, OAuth 2.0, 3rd-party API integration, modular backend architecture, automated testing, and CI/CD.

---

## Live Demo

**[Try the live application](https://tracker.justas.tech)**

**Demo credentials**
- Email: `wtdemo@justas.tech`
- Password: `demo1`

> **Note on Google Fit Integration:**
The credentials above give access to **demo mode** where you can try the features using a mock data source instead of real Google Fit API data. The app is currently in the testing phase on Google’s platform, so only the testing group users can access their Google Fit data using this app. I can add users to the testing group and provide app credentials upon request - [contact me](#contact-me) (please mention your gmail address). Alternatively, the complete app with Google Fit integration can be run and tested [locally](#running-the-project-locally).

---

## Summary (for Hiring Teams)
- **Scope**: Full-stack SPA (React + TypeScript frontend and Python/FastAPI backend) with Google OAuth 2.0 + Google Fit API integration.
- **Architecture**: REST APIs, protocol-based interfaces, dependency injection, modular architecture, demo mode.
- **Key source code**:
  - Backend (`app/`): `main.py`, `api.py`, `google_fit.py`, `data_integration.py`, `analytics.py`
  - Frontend (`ui-react/`): `App.tsx`, `src/components` folder
- **Quality**: 85%+ unit test coverage, full business logic coverage via integration tests, static type checking, linting/formatting via pre-commit, GitHub Actions CI.
- **Deployment**: Backend on Koyeb, frontend on Cloudflare Pages, Supabase for Auth + PostgreSQL.
- **Security & Auth**: JWT-based auth via Supabase for frontend and APIs, secure Google OAuth 2.0 token storage/refresh to access Google data.

---

## Table of Contents
- [Live Demo](#live-demo)
- [Summary for Hiring Teams](#summary-for-hiring-teams)
- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture & Project Structure](#architecture--project-structure)
- [API Documentation](#api-documentation)
- [CI/CD Pipeline](#cicd-pipeline)
- [Testing](#testing)
- [Running the Project Locally](#running-the-project-locally)
- [Design Patterns & Best Practices](#design-patterns--best-practices)
- [Limitations & Enhancements](#limitations--enhancements)
- [Contact Me](#contact-me)

---

## Project Overview

### Why This Project?

I built this project because it:
1. **Solves a real problem** – When tracking weight, weekly averages and trends are more helpful than daily fluctuations. Google Fit and similar apps are good for logging data but don't provide a convenient interface for such analysis.
2. **Presents advanced full-stack challenges** – Secure OAuth 2.0 with Google, fetching and processing real-world data from 3rd party APIs, a React SPA powered by REST APIs, analytics on time-series data, automated testing, and production deployment.

### Learning Outcomes
This is the first full-stack application I shipped to production. It helped me build various skills such as:

- **Full-stack development** – React + TypeScript SPA frontend with a Python/FastAPI backend.
- **OAuth 2.0** – Implementing the flow to get access to user’s Google Fit data.
- **API design** – REST endpoints with clear responsibilities and versioning.
- **Database design and usage** – PostgreSQL + SQLModel for relational data.
- **Clean code principles** – modular architecture, DRY and SOLID (see [Best Practices](#design-patterns--best-practices)).
- **CI/CD** – GitHub Actions, pre-commit hooks, and thorough automated tests.
- **Type safety** – Python type hints + mypy, and TypeScript for the frontend.
- **Cloud deployment** – Koyeb (backend) and Cloudflare Pages (frontend), Supabase for managed PostgreSQL + Auth.

---

## Features

### User Features

**Progress Dashboard**
- **Weight change overview** over a selected period: total change from dates X to Y (in absolute and relative terms), average weekly change, average estimated caloric surplus / deficit
- **Weekly details** - key metrics for every week in the selected period
- **Filtering data**
  - View data for a specific date range (from/to dates)
  - View data for the last N weeks
  - Real-time updates when filters change
- **Syncing data with external sources** - the user can request to get data from their selected source (currently only Google Fit supported)
- **Responsive UI** - clean minimalistic UI that adjusts to various screen sizes, including mobile
- **Meaningful metrics**  - PTs and nutritionists generally recommend keeping weight change to ~0.5%–1% per week for a healthy and sustainable change. The app calculates this rate for the user’s data so they can see if their weight change is within a healthy range.

**Goal-Based Evaluation**
- Switch between three fitness goals: Lose Fat, Maintain Weight, Gain Muscle
- Color coded progress indicators (positive/negative) based on your selected goal

### Backend Features

**Authentication & Authorization**
- **JWT authentication via Supabase** to log in to the frontend and to access the app's REST APIs.
- **Google OAuth 2.0** implementation to get access the user's Google Fit data. This includes secure access token storage and refresh mechanism

**Data Management**
- **Data syncing strategy** - on user's request, fetch and store user's data from the external source (Google Fit)
- **Database as source of truth** - weight entries fetched from external sources are only inserted if there's no entry for that user and date in the DB yet.
- **Flexible storage layer** - the app supports multiple storage systems: PostgreSQL and file-based storage
- **Analytics module** - calculates and returns metrics for the stored weight data

**External Integrations**
- **Google Fit REST API** - Fetch user's weight entries
- **Supabase Auth** - User authentication and JWT validation

**Architecture**
- **RESTful API** design with FastAPI
- **Protocol-based abstractions** for storage layer and external data sources
- **Dependency injection** for clean, testable code
- **Exception handling** with meaningful responses and logging
- **Type safety** with strict MyPy checking

### Screenshots
![App Screenshot](/doc/wt-screenshot-1.png)

![App Screenshot - No Data](/doc/wt-screenshot-2.png)

![App Screenshot - Login](/doc/wt-screenshot-login.png)

![App Screenshot - Mobile](/doc/wt-screenshot-mobile.png)

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.12** | Backend logic |
| **FastAPI** | Framework for REST APIs with automated request/response validation (Pydantic). Includes uvicorn ASGI server |
| **Pydantic** | Automated data validation for HTTP requests/responses and ORM objects |
| **SQLModel** | SQL ORM with Pydantic integration |
| **PostgreSQL** | Relational DB (managed by Supabase in production) |
| **Pandas** | Data processing and analytics |
| **Poetry** | Dependency management and packaging |
| **Supabase** | Protecting APIs with JWT auth |
| **Google APIs** | OAuth 2.0 and Google Fit integration |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | SPA frontend built around reusable components and state management |
| **TypeScript** | Frontend logic |
| **Vite** | Frontend build tool and dev server |
| **Custom HTML/CSS** | BEM methodology for maintainability |
| **Supabase JS** | Authentication client |

### DevOps & Quality Assurance
| Tool | Purpose |
|------|---------|
| **Pre-commit** | Git pre-commit hooks for code quality (mypy, ruff lint, format) and integration tests |
| **MyPy** | Static type checking (strict mode) |
| **Ruff** | Python linter and formatter |
| **Pytest** | Automated unit and integration testing |
| **GitHub Actions** | CI / CD pipeline: automated code quality checks and tests |

### Deployment
| Platform | Purpose |
|----------|---------|
| **Koyeb** | Backend API hosting |
| **Cloudflare Pages** | Frontend hosting |
| **Supabase Cloud** | Managed PostgreSQL + Auth service |

---

## Architecture & Project Structure

### High Level Architecture

The diagram below presents the overall architecture of the system, including external elements.

![Architecture - High Level](/doc/architecture_high_level.png)

### Backend Architecture

The diagram below details the backend architecture - key modules, interfaces and classes, and their dependencies.

![Architecture - Backend](/doc/architecture_backend.png)

### Project Structure

```
weight-tracker/                        # Project root (managed with Poetry)
│
├── app/                               # Backend (Python / FastAPI)
│   ├── main.py                        # Application entry point
│   ├── api.py                         # REST API routes, validation models and helpers
│   ├── google_fit.py                  # Google OAuth endpoints, token management + Google Fit API integration
│   ├── data_integration.py            # Orchestration service to sync storage with external sources
│   ├── db_storage.py                  # PostgreSQL DataStorage implementation - weight data and tokens storage
│   ├── file_storage.py                # File system-based DataStorage implementation - weight data and tokens storage
│   ├── analytics.py                   # Weekly weight data aggregation and analytics calculations
│   ├── project_types.py               # Type definitions and Protocol-based interfaces
│   ├── utils.py                       # Helper functions
│   ├── demo.py                        # Demo-mode DataSourceClient implementation
│   └── .env.example                   # Backend environment variable config template
│
├── ui-react/                          # Frontend (React / TypeScript)
│   ├── src/
│   │   ├── main.tsx                   # Frontend React app entry point
│   │   ├── App.tsx                    # Root component with global state management
│   │   ├── index.css                  # Global styles (BEM style)
│   │   ├── components/                # Reusable React components
│   │   └── types/                     # Frontend TypeScript type definitions
│   └── package.json                   # Frontend dependencies (npm)
│   └── vite.config.ts                 # Vite build tool configuration
│   └── .env.example                   # Frontend environment variable config template
│
├── tests/                             # Backend test suite
│   └── backend/
│       ├── unit/                      # Unit tests (module-level)
│       └── integration/               # Integration tests (organized by feature group)
│
├── .github/workflows/                 # CI/CD pipeline workflows
│   ├── backend_code_quality.yaml      # Code Quality check flow
│   └── backend_testing.yaml           # Unit & integration test flow
│
├── doc/                               # Documentation assets (architecture diagrams, screenshots)
|
├── README.md                          # Project documentation (this file)
├── pyproject.toml                     # Backend dependencies (Managed by Poetry)
├── poetry.lock                        # Locked Python dependency versions
└── .pre-commit-config.yaml            # Pre-commit hooks (linter, formatter, type-check, integration tests)
```

### Backend Modules

| Module | Purpose |
|------------|---------|
| **main.py** | FastAPI app setup, API route registration |
| **api.py** | Logic of the main REST API routes powering the app. Includes helper functions, HTTP request / response model validations, user's JWT validation. Uses FastAPI dependency injection to get the relevant data storage, external data source, and database connection instances |
| **data_integration.py** | `DataIntegrationService` orchestrates data sync between DB data and external sources. Uses DI to support any implementation of data storage and data source protocols |
| **db_storage.py / file_storage.py** | Two different implementations of the `DataStorage` protocol that give CRUD access to stored weight data |
| **analytics.py** | Analytics engine. Calculates and returns weekly aggregates and summary metrics from daily weight entries using pandas |
| **google_fit.py** | Logic related to Google OAuth flow and Google Fit API integration. Defines 2 API routes used to handle Google OAuth 2.0 flow (one to redirect user to Google consent flow, another to handle authorization callback from the server). Also, contains a `GoogleFitAuth` class that stores, loads and refreshes OAuth tokens. Finally, the `GoogleFitClient` class fetches raw data from Google Fit API and transforms it to standard format |
| **mfp.py** | Integrates with MyFitnessPal as alternative to Google Fit and demonstrates flexibility of `DataSourceClient` protocol. **Currently disabled** due to 3rd party library package issues - [PR raised](https://github.com/coddingtonbear/python-myfitnesspal/pull/201) to fix it |
| **project_types.py** | Complex type definitions for type annotation and type safety checks. Includes definitions of the `DataStorage` and `DataSourceClient` protocols |
| **demo.py** | Implements mock implementation of the `DataSourceClient` protocol with mock source data. It's in demo mode (when logging in with demo user credentials) |

### Frontend Components
Below are key React components that constitute the frontend (smaller components not mentioned)

| Component | Purpose |
|------------|---------|
| **App.tsx** | Root component. Overall layout of the SPA (Header and Main subcomponents),  top-level logic and callbacks passed down to sub-components. Includes logic to manage the auth state, triggering toast messages, triggering data sync to refresh the whole app, etc. |
| **Header.tsx** | Logo, goal selection, current user info and sign out option |
| **Login.tsx** | Page with the login form, displayed if there is no active authenticated user session |
| **Main.tsx** | Layout of the main section of the app. Also contains filter components and a selection of CTAs to trigger data sync from various sources |
| **Summary.tsx**  | Cards that summarize the weight change over the selected period |
| **WeeklyDataTable.tsx**  | Table with one row for each week in the selected period with key metrics for that week. Color coded results based on selected goal  |
| **Filters.tsx**  | Controls to select the data period (last N weeks or from dates X to Y) |

The screenshot below shows the layout of the key components in the UI:

![UI Components](/doc/ui-components-1.png)

---
## API Documentation
### Authentication

All API endpoints require Authorization header with JWT, validated via Supabase Auth.

**Authorization Header:**
```http
Authorization: Bearer <supabase_jwt_token>
```

### CORS
Currently, the APIs can only be accessed from the domain hosting the React Frontend app (defined as an environment variable `FRONTEND_URL`)

### REST API Endpoints
The app is powered by the following endpoints (only data associated with authenticated user is returned)
- **`GET /daily-entries`** -> the user's daily weight entries stored in DB
- **`GET /weekly-aggregates`** -> calculates weekly averages and other key metrics grouped by week
- **`GET /summary`** -> total weight change metrics over a given period
- **`GET /latest-entry`** -> the latest daily weight entry (for date closest to current date)
- **`POST /sync-data`**-> triggers fetching data from the selected external data source and inserting new entries in the app storage
- **`GET /healthz`** -> API status check

API is prefixed with `/api/<version_number>`. The latest prefix is included in the API documentation (see below).

Full API documentation is generated automatically by FastAPI and is available at:
- [Swagger](https://api.tracker.justas.tech/docs)
- [ReDoc](https://api.tracker.justas.tech/redoc)

### OAuth Endpoints
The app has 2 endpoints that are used in the Google OAuth 2.0 flow to obtain access tokens that are used to fetch the user's Google Fit data.

#### **GET** `/auth/google-signin`

Frontend client redirects end user to this endpoint to initiate Google OAuth 2.0 flow. This endpoint prepares the config needed for auth flow and redirects the user to Google consent page.

#### **GET** `/auth/google-auth`

Google OAuth server calls this endpoint after successful consent from user. This endpoint fetches the access/refresh tokens given the authorization code and stores it to give the app access to user's Google Fit data.

### Database Schema

When database is used as storage mode, app uses a PostgreSQL database that contains two main tables managed by SQLModel ORM:

#### `weight_entries` Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | UUID | PRIMARY KEY | User ID (managed by Supabase Auth) |
| `entry_date` | DATE | PRIMARY KEY | Date when the weight measurement was taken |
| `weight` | FLOAT | NOT NULL | Weight value in kilograms |

**Composite Primary Key:** `(user_id, entry_date)` - only one weight entry allowed per user per day

**Note:** No foreign key constraint on `user_id` because user  account management is handled externally by Supabase Auth.

#### `google_credentials` Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | UUID | PRIMARY KEY | User whose access token we store here (users managed by Supabase Auth) |
| `token` | VARCHAR | NOT NULL | OAuth access token to access user's Google Fit data |
| `refresh_token` | VARCHAR | NOT NULL | OAuth refresh token for obtaining new access tokens |
| `scopes` | VARCHAR | NOT NULL | JSON array of Google API scopes |
| `token_uri` | VARCHAR | NOT NULL | Google OAuth token endpoint URI |
| `expiry` | TIMESTAMP | NULLABLE | Access token expiration timestamp |

---

## CI/CD Pipeline
The project includes best practices to manage code versioning and get it to prod while assuring quality. The diagram below details the developer workflow I used to ship new code to production.

![CI / CD Workflow](doc/ci_cd_flow.png)

---

## Testing
- Tests currently cover only the backend and use `pytest` framework.
- The test suite includes unit and integration tests. Unit tests are defined by module and integration tests are split by feature groups.
- Unit tests have a total ~85% coverage with all business logic covered.
- Integration tests use isolated environments to test end-to-end features (separate test database, mocked Google Fit integration)

Test suite structure:

```
tests/backend/
├── unit/
│   ├── test_analytics.py
│   ├── test_api.py
│   ├── test_data_integration.py
│   ├── test_db_storage.py
│   ├── test_file_storage.py
│   ├── test_google_fit.py
│   └── test_utils.py
│
└── integration/
    ├── test_sync_data.py
    ├── test_get_data.py
    └── test_demo_mode.py
```

#### Running tests
**All tests:**
```bash
poetry run pytest
```

**Unit tests only:**
```bash
poetry run pytest tests/backend/unit
```

**Integration tests only:**
```bash
poetry run pytest tests/backend/integration
```

---

## Running the Project Locally

### Prerequisites
The project requires the following:
- **Docker Desktop** - local Supabase (needed for Auth) runs inside Docker container: https://www.docker.com/products/docker-desktop/
- **Supabase CLI** - running a local Supabase instance with Auth and PostgreSQL DB if needed:
https://supabase.com/docs/guides/local-development/cli/getting-started

- **Python 3.12+** with Poetry package manager
  ```bash
  brew install python@3.12
  python -m pip install --upgrade pip
  pip install poetry
  ```
- **Node.js 18+ Runtime** and npm
  ```bash
  brew install node
  ```
- **(Optional) Google Cloud Project** credentials for Google Fit integration (see below)

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/justaszie/weight-tracker.git
   cd weight-tracker
   ```

2. **Install Python dependencies:**
   ```bash
   poetry install
   ```

3. **Start local Supabase:**
   ```bash
   supabase init
   supabase start
   ```

   **Important:** Save the output values when starting Supabase:
   - `API URL`
   - `Publishable key`
   - `Database URL` (if you plan to use Supabase PostgreSQL as storage layer)
   - `Studio URL:` - URL to the admin panel

4. **Configure environment:**
    Copy the sample .env file and fill it with values as described in the sample file.

    [.env.example](/app/.env.example)

    ```bash
    cp ./app/.env.example ./app/.env
    ```

5. **(Optional) Google Fit Integration setup:**

    **Important**: Google plans to deprecate the Google Fit REST APIs in 2026

    If you want to test Google Fit integration, you need to set up a Google API client on Google Cloud Platform:
    1.  Create a project in [GCP Console](https://console.cloud.google.com)
    2. Enable **Fitness API** : https://console.cloud.google.com/apis/dashboard
    3. Create **OAuth 2.0 credentials / Client** (Web application): https://console.cloud.google.com/apis/credentials
    4. Open the Client page and add authorized redirect URI: `http://localhost:8000/auth/google-auth` or a different port value depending on the port your FastAPI backend runs on.
    5. Download `credentials.json`. Use its values to populate the `app/.env` file. Use the following scopes:


6. **Create Test User Account**
    1. Go to the Supabase Studio URL (value output when starting supabase)
    2. Go to the `Auth` section and create a test user.

7. **Start the backend server:**
    ```bash
    poetry run uvicorn app.main:app --reload --port 8000 # or other port if 8000 is taken
    ```

    - Backend running at: http://localhost:8000
    - API documentation: http://localhost:8000/docs

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd ui-react
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**

    Copy the sample .env file and fill it with values as described in the sample file.

    [.env.example](/ui-react/.env.example)

    ```bash
    cp .env.example .env
    ```

4. **Start local development server:**
    ```bash
    npm run dev
    ```

    Frontend running at: http://localhost:5173

5. **Test the App**

    Go to http://localhost:5173 and log in using the test credentials created in Supabase.
---

## Design Patterns & Best Practices

### Note on using AI tools
Since learning was the main goal, I wrote all code manually. I did **not** use AI to generate production code, other than occasional small snippet when using new libraries / APIs.
I occasionally used AI tools for debugging support and design feedback.

The initial UI drafts were created with [v0](https://v0.app/chat/simple-weight-tracker-design-ouWpH9FyHKR?ref=KSHPPZ) tool but I treated them as visual inspiration and implemented the frontend components and styles (HTML, CSS and React/TS) from scratch.

### Backend Architecture

**Interfaces Through Protocols**
```python
# Protocol specifying features to be implemented by the storage layer
class DataStorage(Protocol):
    def get_weight_entries(self, user_id: UUID) -> list[WeightEntry]: ...
    def create_weight_entries(self, entries: Iterable[WeightEntry]) -> None: ...
```
This allows swapping between database and file storage without changing business logic.

```python
# Protocol specifying features to be implemented by the external data source integrations
class DataSourceClient(Protocol):
    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> Any: ...
    def convert_to_daily_entries(self, raw_dataset: Any) -> list[WeightEntry]: ...
```

This allows extending the app functionality with new external data sources with minimal change to existing code.

**Factory Functions**
```python
# factory function in main.py:
def create_data_storage() -> DataStorage:
    storage_type = os.environ.get("STORAGE_TYPE", "database")
    match storage_type:
        case "database":
            return DatabaseStorage()
        case "file":
            return FileStorage()
        case _:
            raise ValueError(f"Unsupported storage type {storage_type}")

# Instantiating auth service, storage and logging config as part of app startup
@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    data_storage = create_data_storage()
    app.state.data_storage = data_storage
    logger.info(
        f"App started with {data_storage.__class__.__name__} as Storage Backend"
    )
```

This allows changing the storage mode of the app from a single point in the app.

**Dependency Injection**
```python
  DataStorageDependency = Annotated[DataStorage, Depends(get_data_storage)]
  UserDependency = Annotated[UUID, Depends(get_current_user)]

  @router_v1.get("/daily-entries", response_model=list[WeightEntry])
  def get_daily_entries(
      user_id: UserDependency,
      data_storage: DataStorageDependency,
      date_from: dt.date | None = None,
      date_to: dt.date | None = None,
  ) -> list[WeightEntry]:
```
Data storage instance and the authenticated user ID are injected automatically into the API routes that use it. We can change the code in a single place (the dependency functions) to make the change in the whole API. Also, these dependencies can be easily mocked in testing.

```python
class DataIntegrationService:
    def __init__(
        self, data_storage: DataStorage, data_source: DataSourceClient
    ) -> None:
        self.storage = data_storage
        self.source = data_source
```
Data integration logic can work with any data storage implementation and any external data source as these dependencies are injected by the caller.

**Strict Type Safety**

Catching errors before runtime by implementing clean type annotations wherever possible and running `mypy` for static type checking pre-commit and before deploying to prod. Note that some libraries like pandas are very dynamic and difficult to annotate specifically.

**Error Handling Strategy**
```python
def get_data_source_client(
    request: Request, source_name: DataSourceName, user_id: UUID
) -> DataSourceClient:
        ...
        oauth_credentials: Credentials | None = GoogleFitAuth().load_credentials(
            data_storage, user_id
        )
        if not oauth_credentials:
            raise NoCredentialsError("Google API credentials required")

        return GoogleFitClient(user_id, oauth_credentials)

# in /sync-data route logic:
...
except NoCredentialsError:
        logger.warning("Google Fit credentials missing or expired")
        return JSONResponse(
            status_code=401,
            content={
                "message": "Google Fit authentication needed",
                "auth_url": (
                    f"{http_request.app.url_path_for('google_signin')}?user_id={user_id}"
                ),
            },
        )
```
Using specific error types helps the higher-level code provide clearer feedback.

**Separation of Concerns**
- `api.py` - HTTP layer, params handling, validation, response formatting
- `data_integration.py` - Business logic for data sync. Implements the sync strategy
- `analytics.py` - Pure analytics calculation functions
- `db_storage.py` - Database operations only
- etc.

### Frontend Architecture

**BEM CSS Methodology**

Organizing HTML elements using class names and grouping them into blocks that contain elements and can have various states using modifiers.

```css
/* Block */
.get-data { }

/* Element */
.get-data__cta { }

/* State Modifier */
.get-data__cta--loading { }
```

- Benefits: HTML and CSS are semantic, easy to read and maintain.
- Limitations: Repeated CSS code for similar elements.

**Component Composition**

Sample composition:
```tsx
<App>
  <Header />
  <Main>
    <Filters>
        <WeeksFilter />
        <DatesFilter />
      </Filters>
    <GetDataSelection />
    <NoDataView />
      <GetDataSelection />
    <Summary />
    <WeeklyDataTable />
  </Main>
</App>
```

Components have clear responsibilities and are easily reusable. For example, `GetDataSelection` is used at the top of the main content as well as inside the `NoDataView` component

**Type-Safety**
```typescript
type Goal = 'lose' | 'maintain' | 'gain';

interface SummaryProps {
  goalSelected: Goal;
  datesFilterValues: DatesFilterValues | null;
  weeksFilterValues: WeeksFilterValues | null;
  session: Session;
  showToast: ShowToastFunction;
  dataSyncComplete: boolean;
  latestEntry: WeightEntry | null;
}
```

## Limitations & Enhancements
### Limitations
- The production app is in Testing state on Google Auth platform. Only users added to the testing group can access their Google Fit data. I don't plan to complete this verification due to the fact that Google Fit APIs [will be deprecated in 2026](https://developers.google.com/fit/rest).
- Backend APIs only support a single frontend domain. To support more diverse clients (e.g. mobile apps, automated scripts), the Google OAuth flow should be changed and the CORS authorized domain management should be made more flexible.
- Frontend and backend are in the same repo/project which adds time to deployments (e.g. Cloudflare pages have to install Python environment in their instance). It's good enough for a small project like this but could be improved.
- MyFitnessPal was implemented as an external data source, alternative to Google Fit API using a 3rd party scraping library. This demonstrates the flexibility of the DataSourceClient protocol. But the library has dependency conflicts with Supabase so the MFP module had to be disabled. I raised a fix PR and am waiting [for the merge](https://github.com/coddingtonbear/python-myfitnesspal/pull/201).


### Enhancements
- Users can get their data only from the implemented external sources (currently just Google Fit API). Manual entry is a key feature to make it useful to production users.
- Sign-up feature should be implemented on the frontend using Supabase integration
- The users' Google OAuth access and refresh tokens should be encrypted before storing them in PostgreSQL DB. This would mitigate the risk of the Supabase PostgreSQL DB being breached.
- UI can be more polished - e.g. consistent feedback to the user when a component is being refreshed, etc.
---

## Contact Me
I’d love to hear from you—whether you’re a hiring manager reviewing this project, a developer interested in collaborating, or someone who would like to share feedback. **I am looking for** full-stack or backend-focused software engineering roles or contracts.

**Justas Zieminykas**
- **GitHub:** [justaszie](https://github.com/justaszie)
- **Email:** justas.zieminykas@gmail.com
- **LinkedIn:** [Justas Zieminykas](https://www.linkedin.com/in/justas-žieminykas-01423988)

---
