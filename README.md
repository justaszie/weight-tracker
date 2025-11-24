[![Code Quality Check Flow](https://github.com/justaszie/weight-tracker/actions/workflows/backend_code_quality.yaml/badge.svg)](https://github.com/justaszie/weight-tracker/actions/workflows/backend_code_quality.yaml)
[![Testing Flow](https://github.com/justaszie/weight-tracker/actions/workflows/backend_testing.yaml/badge.svg)](https://github.com/justaszie/weight-tracker/actions/workflows/backend_testing.yaml)

# Weight Tracker - Full Stack Portfolio Project

This is a weight tracking application that fetches data from external sources (Google Fit API), stores that data, performs analytics, and presents insights through a modern web interface to help users track their weight goals. It's built primarily as a software portfolio project to demonstrate full-stack development, OAuth implementation, 3rd party API integration, modular architecture, and CI/CD practices.

---

## Table of Contents
- [Live Demo](#live-demo)
- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Running the Project Locally](#running-the-project-locally)
- [Design Patterns & Best Practices](#design-patterns--best-practices)
- [Limitations and Enhancements](#limitations-and-enhancements)
- [Contact Me](#contact-me)

---

## Live Demo

**[Try the live application](https://tracker.justas.tech)**

**Demo credentials**
- Email: `wtdemo@justas.tech`
- Pwd: `demo1`

> **Note on Google Fit Integration:**
The credentials above give access to **demo mode** where you can try the features using a mock data source instead of real Google Fit API data. The app is currently in the testing phase on Google’s platform, so it can access a user’s Google Fit data only if that user is part of the testing group. I can add users to the testing group and create accounts on the app upon request (please mention your gmail address): [contact me]((#contact-me)). Alternatively, the complete app with Google Fit integration can be run and tested [locally](#running-the-project-locally).

---

## Project Overview

### Why This Project?

I built this application to solve a personal need and because it presented some advanced tech challenges important in full-stack application development.
1. **Personal problem** - When tracking progress on weight goals it's more productive to look at weekly averages and trends, rather than day-to-day fluctuations. The Google Fit mobile app is useful to log the weight and have a quick overview but not enoughto analyze trends. I haven't found any app that does it conveniently.
2. **Tech Challenges** - secure OAuth 2.0 auth flow with Google, fetching, processing and storing real-world data from Google Fit API, React SPA powered by REST APIs, automated testing, production deployment.

### Learning Outcomes
This is the first full-stack project that I shipped to production. It taught me many valuable skills to be used in the next projects.
- **Building full-stack apps** (Single Page Application) with Python/FastAPI backend and React frontend
- **OAuth 2.0** flow implementation to get access to user's Google Fit data
- **API design** following REST principles
- **Database design and querying** with PostgreSQL and SQLModel
- **Version Control** with remote Github repo, commit and PR hygiene
- **CI/CD practices** including pre-commit hooks for code quality and automated testing
- **Type safety** with Python type hints (mypy) and TypeScript
- **Cloud deployment** on modern platforms: Koyeb (backend) and Cloudlfare Pages (frontend)

### AI tools
Since learning was the main goal, the codebase was written manually. **No AI code generation was used**, except help with debugging and evaluating my own code.
Drafts of the UI design were generated using [v0](https://v0.app/chat/simple-weight-tracker-design-ouWpH9FyHKR?ref=KSHPPZ) but I used them just as a visual inspiration and wrote the code from scratch myself.

---

## Features

### User Features

**📈 Progress Dashboard**
- **Weight change overview** over a selected period: total change from dates X to Y (in absolute and relative terms), average weekly change, average estimated caloric surplus / deficit
- **Weekly details** key metrics for every week in the selected period
- **Filtering data**
  - View data for a specific date range (from/to dates)
  - View data for the last N weeks
  - Real-time updates when filters change
- **Syncing data with external sources** - user can request to get data from their selected source (currently only Google Fit supported)
- **Responsive design** clean minimalistic UI that adjusts to various screen sizes, including mobile
- **Meaningful metrics** PTs and nutritionists recommend to keep the weight change to ~0.5% - 1% per week for a healthy and sustainable change. The app calculates this rate for the user's data and allows them to evaluate if they're following healthy weight change.

**🎯 Goal-Based Evaluation**
- Switch between three fitness goals: Lose Fat, Maintain Weight, Gain Muscle
- Color coded progress indicators (positive/negative) based on your selected goal

### Backend Features

**🔐 Authentication & Authorization**
- **JWT authentication via Supabase** to log in to the frontend and to access the app's REST APIs.
- **Google OAuth 2.0** implementation to get access to fetch the user's Google Fit data. This includes secure access token storage and refresh mechanism

**💾 Data Management**
- **Data syncing strategy** - on user's request, fetch and store user's data from the external source (Google Fit)
- **Database as source of truth**  - eternal source weight entries are only inserted if there's no entry for that user and date in the DB yet.
- **Flexible storage layer** - the app supports multiple storage systems: PostgreSQL and file-based storage
- **Analytics module** - calculates and returns metrics for the stored weight data

**🔌 External Integrations**
- **Google Fit REST API** - Fetch user's weight entries
- **Supabase Auth** - User authentication and JWT validation

**🏗️ Architecture**
- **RESTful API** design with FastAPI
- **Protocol-based abstractions** for storage layer and external data sources
- **Dependency injections** for clean, testable code
- **Exception handling** with meaningful responses and logging
- **Type safety** with strict MyPy checking

### Screenshots
![App Screenshot](/doc/wt-screenshot-1.png)
![App Screenshot - No Data](/doc/wt-screenshot-2.png)
![App Screenshot - Login](doc/wt-screenshot-login.png)
![App Screenshot - Mobile](doc/wt-screenshot-mobile.png)
---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.12** | Backend logic |
| **FastAPI** | Framework for FastAPIs with automated request/response validation (Pydantic. Includes uvicorn server) |
| **Pydantic** | Automated data vaidation: HTTP request / responses, ORM objects |
| **SQLModel** | SQL ORM with Pydantic integration |
| **PostgreSQL** | Relational DB (managed by Supabase in prod) |
| **Pandas** | Data processing and analytics |
| **Poetry** | Dependency management and packaging |
| **Supabase** | Protecting APIs with JWT auth |
| **Google APIs** | OAuth 2.0 and Google Fit integration |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | SPA Frontend built around components and state management |
| **TypeScript** | Frontend logic |
| **Vite** | Frontend build tool and dev server |
| **Custom HTML/CSS** | BEM methodology for maintainability |
| **Supabase JS** | Authentication client |

### DevOps & Quality Assurance
| Tool | Purpose |
|------|---------|
| **Pre-commit** | Git hooks for code quality and quick tests|
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

## Architecture Overview

### High Level Architecture

![Architecture](/doc/architecture.png)

### Project Structure
```
weight-tracker/                        # Project Root
│
└── Documentation
    └── README.md                      # This file
    └── doc                            # Doc related assets
├── Backend (Python/FastAPI)
│   ├── app/
│   │   ├── main.py                    # Application starting point
│   │   ├── api.py                     # REST API routes & endpoints
│   │   ├── google_fit.py              # Google OAuth & Fit API
│   │   ├── data_integration.py        # Data sync orchestration
│   │   ├── db_storage.py              # PostgreSQL storage layer
│   │   ├── file_storage.py            # File-based storage
│   │   ├── analytics.py               # Analytics functions
│   │   ├── project_types.py           # Type definitions & abstraction protocols
│   │   ├── utils.py                   # Helper functions
│   │   ├── demo.py                    # Demo mode implementation
│   │   └── .env.example               # Backend env variables template
│   │
│   ├── pyproject.toml                 # Python dependencies (Poetry)
│   └── poetry.lock                    # Locked dependencies
│
├── Frontend (React/TypeScript)
│   └── ui-react/
│       ├── src/
│       │   ├── main.tsx               # React entry point
│       │   ├── App.tsx                # Root component
│       │   ├── index.css              # Global styles (BEM)
│       │   ├── components/            # React components
│       │   └── types/                 # TypeScript type definitions
│       └── .env.example               # Frontend env variables
│
├── Tests
│   └── tests/backend/
│       ├── unit/                      # Unit tests
│       └── integration/               # Integration tests
|
├── DevOps & CI/CD
│   ├── .github/workflows/
│   │   ├── backend_code_quality.yaml  # Linting, formatting and type checking
│   │   └── backend_testing.yaml       # Automated testing
│   └── .pre-commit-config.yaml        # Pre-commit hooks
│
```

### Backend Modules

| Module | Purpose |
|------------|---------|
| **main.py** | FastAPI app setup, API route registration |
| **api.py** | Logic of the main REST API routes powering the app. Includes helper functions, HTTP request / response model validations, user's JWT validation. Uses FastAPI dependency injection to get the relevant data storage, external data source, and database connection instances |
| **data_integration.py** | `DataIntegrationService` orchestrates data sync between DB data and external sources. Uses DI to support any implementation of data storage and data source protocols |
| **db_storage.py / file_storage/py** | 2 different implementations `DataStorage` protocol that give CRUD access to data storage |
| **analytics.py** | Analytics engine. Calculates and returns weekly aggregates and summary metrics from daily weight entries using pandas |
| **google_fit.py** | Logic related to Google OAuth flow and Google Fit API integration. Defines 2 API routes used to handle Google OAuth 2.0 flow (one to redirect user to Google consent flow, another to handle authorization callback from the server). Also, ontains `GoogleFitAuth` client that stores, loads and refreshes OAuth tokens. Finaly, `GoogleFitClient` that fetches raw data from Google Fit API and transforms it to standard format |
| **mfp.py** | Integrates with MyFitnessPal as alternative to Google Fit and demonstrates flexibility of `DataSourceClient` protocol. Currently disabled due to 3rd party library package issues - [PR raised](https://github.com/coddingtonbear/python-myfitnesspal/pull/201) to fix it |
| **project_types.py** | Complex type definitions for type annotation and type safety checks. Includes definitions of the `DataStorage` and `DataSourceClient` protocols |
| **demo.py** | Implements mock implementaion of the `DataSourceClient` protocol to be used in demo mode in production |

### Frontend Components

| Component | Purpose |
|------------|---------|
| **App.tsx** | Root component. Overall layout of the SPA (Header and Main subcomponents),  top-level logic and callbacks passed down to sub-components. Includes logic to manage the auth state, triggering toast messages, triggering data sync to refresh the whole app, etc. |
| **Header.tsx** | Logo, goal selection, current user info and sign out option |
| **Login.tsx** | Login form, dispalyed if there is no active authenticated user session |
| **Main.tsx** | Layout of the main section of the app. Also contains filter components and a selection of CTAs to trigger data sync from various sources |
| **Summary.tsx**  | Cards that summarize the weight change over the selected period |
| **WeeklyDataTable.tsx**  | Table with one row for each week in the selected period with key metrics for that week. Color coded results based on selected goal  |
| **Filters.tsx**  | Controls to select the data period (last N weeks or from dates X to Y) |
| **NoDataView.tsx**  | View displayed when user has no weight data stored yet and includes CTAs to get data |

The screens below show the position of the main components in the UI:

![UI Components](/doc/ui-components-1.png)
![UI Components - No Data](/doc/ui-components-2.png)
![UI Components - Login](/doc/ui-components-login.png)

### CI/CD Pipeline

**Developer Workflow**

![CI / CD Workflow](doc/ci_cd_flow.png)

---
## API Documentation
### Authentication

All API endpoints require Authorization header with JWT, validated via Supabase Auth.

**Authorization Header:**
```http
Authorization: Bearer <supabase_jwt_token>
```

### REST API Endpoints
The app is powered by the following endpoints (only data associated with authenticated user is returned)
- `GET /daily-entries` -> the user's daily weight entries stored in DB
- `GET /weekly-aggregates` -> the user's weight entries aggregated on a weekly basis and calculates key metrics
- `GET /summarry` -> the weight change metrics over a given period
- `GET /latest-entry` -> the latest daily weight entry (for date closest to current date)
- `POST /sync-data` -> triggers fetching data from the selected external data source and inserting new entries in the app storage
- `GET /healthz` -> API status check

API is prefixed with `/api/<version_number>`. The latest prefix is included in the API documentation (see below).

Full API documentation is generated automatically by FastAPI:
- [Swagger](https://api.tracker.justas.tech/docs)
- [ReDoc](https://api.tracker.justas.tech/redoc)

### OAuth Endpoints
The app has 2 endpoints that are used in the Google OAuth 2.0 flow to obtain user's google access tokens that are used to fetch Google Fit data.

#### **GET** `/auth/google-signin`

Frontend client redirects end user to this endpoint to initiate Google OAuth 2.0 flow. This endpoint prepares the config needed for auth flow and redirects the user to Google consent page.

#### **GET** `/auth/google-auth`

Google OAuth server calls this endpoint after successful consent from user. Thie endpoint fetches the access/refresh tokens given the authorization code and stores it to give the app access to user's Google Fit data.

---

## Testing

- Tests only cover backend at the moment and uses `pytest` framework.
- The test suite includes unit and integration tests.
- Unit tests are defined by module and integration tests are split by feature groups.
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

Ensure you have the following installed:

- **Docker Desktop** - For local Supabase instance
- **Supabase CLI** - Database management
  ```bash
  brew install supabase/tap/supabase
  ```
- **Python 3.12+** with Poetry
  ```bash
  brew install python@3.12
  curl -sSL https://install.python-poetry.org | python3 -
  ```
- **Node.js 18+** and npm
  ```bash
  brew install node
  ```
- **(Optional) Google Cloud Console** credentials for Google Fit integration

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
   supabase start
   ```

   📝 **Important:** Save the output values:
   - `API URL`
   - `anon key`
   - `service_role key`
   - `JWT secret`

4. **Configure environment:**

Sample .env files:
- Backend: [.env.example](/app/.env.example)
- Frontend:  [.env.example](/ui-react/.env.example)

   ```bash
   cp app/.env.example app/.env
   ```

   Edit `app/.env` with your Supabase values:
   ```bash
   APP_ENV=dev
   STORAGE_TYPE=database
   DB_CONNECTION_STRING=postgresql+psycopg2://postgres:postgres@localhost:54322/postgres
   SUPABASE_URL=http://localhost:54321
   SUPABASE_KEY=<your_anon_key>
   SUPABASE_JWT_SECRET=<your_jwt_secret>
   DEMO_USER_ID=<generate_a_uuid>
   FRONTEND_URL=http://localhost:5173
   ```

1. **(Optional) Google Fit setup:**

   If you want to test Google Fit integration:

   a. Create a project in [Google Cloud Console](https://console.cloud.google.com)

   b. Enable **Google Fit API**

   c. Create **OAuth 2.0 credentials** (Web application)

   d. Add authorized redirect URI: `http://localhost:8000/auth/google-auth`

   e. Download `credentials.json` and place it:
   ```bash
   mkdir -p app/auth
   # Move credentials.json to app/auth/
   ```

   f. Add to `app/.env`:
   ```bash
   GOOGLE_CLIENT_ID=<your_client_id>
   GOOGLE_CLIENT_SECRET=<your_client_secret>
   ```

2. **Initialize database:**
   ```bash
   poetry run python -c "from app.db_storage import DatabaseStorage; DatabaseStorage()"
   ```

3. **Start the backend server:**
   ```bash
   poetry run uvicorn app.main:app --reload --port 8000
   ```

   ✅ Backend running at: http://localhost:8000

   📖 API documentation: http://localhost:8000/docs

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
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```bash
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_PREFIX=api/v1
   VITE_SUPABASE_URL=http://localhost:54321
   VITE_SUPABASE_ANON_KEY=<your_anon_key>
   VITE_DEMO_USER_ID=<same_uuid_as_backend>
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

   ✅ Frontend running at: http://localhost:5173

### Verify Setup

1. Open http://localhost:5173 in your browser
2. The app should load in demo mode
3. Click "Sign In" to test authentication
4. Try different goals and filters

---

## Design Patterns & Best Practices

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

**Dependency Injection**
```python
def get_data_storage(request: Request) -> DataStorage:
    return request.app.state.storage

DataStorageDependency = Annotated[DataStorage, Depends(get_data_storage)]

@router.get("/daily-entries")
def get_entries(storage: DataStorageDependency):
    return storage.get_weight_entries(user_id)
```
Storage instance is injected automatically into the API routes that use it. Storage can be swapped easily or mocked for testing.

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

# in /sync-data:
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
Using specific errors to help higher abstraction code provide clearer feedback.

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

Benefits: HTML and CSS are semantic, easy to read and maintain.
Limitations: Repeated CSS code for similar elements.

**Component Composition**
Sample composition:
```tsx
<App>
  <Header />
  <Main>
    <Summary />
    <Filters>
      <WeeksFilter />
      <DatesFilter />
    </Filters>
    <WeeklyDataTable />
  </Main>
</App>
```
Each component has a single responsibility.

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

## Limitations and Enhancements
### Limitations
- The production app is in Testing state on Google Auth platform. Only users added to testing group can access their Google Fit data. I don't plan to complete this verification due to lack of resources and the fact that Google Fit APIs [will be deprecated in 2026](https://developers.google.com/fit/rest).
- Backend APIs only support a single frontend domain. To support more diverse clients (e.g. mobile apps, automated scripts), the Google OAuth flow should be changed and the CORS authorized domain management should be made more flexible.
- Frontend and backend are in the same repo/project which adds time to deployments (e.g. Cloudflare pages have to install Python environment in their instance). It's good enough for a small project like this but could be improved.
- MyFitnessPal was implemented as an external data source, alternative to Google Fit API using a 3rd party scraping library. But the library has dependency conflicts with Supabase so the MFP module had to be disabled [until the library is updated](https://github.com/coddingtonbear/python-myfitnesspal/pull/201).
- The users' Google OAuth access and refresh tokens are stored securely in the Supabase production PostgreSQL DB but they are stored in clear. There's a risk of the tokens being misused if Supabase DB is breached. Encoding those tokens would improve security. It's not prioritized because the Google integration will remain in Testing stage.

### Enhancements
- Users can get their data only from the implemented external sources (currently just Google Fit API). Manual entry is a key feature to make it useful to production users.
- Sign up feature should be implemented on the Frontend using Supabase integration
- UI can be more polished - e.g. consistent feedback to user when a component is being refreshed, etc.
---

## Contact Me

I'd love to hear from you! Whether you're a hiring manager reviewing this portfolio project or a developer interested in collaboration or just want to share feedback.

**Justas Zieminykas**

- 🌐 **Github:** [justaszie](https://github.com/justaszie)
- **GitHub:** [@justaszie](https://github.com/justaszie)
- **Email:** justaxsz@gmail.com
- **LinkedIn:** [Justas Zieminykas](https://www.linkedin.com/in/justas-žieminykas-01423988)

**I am looking for** full-stack or backend-focused software engineering roles / contracts.

---