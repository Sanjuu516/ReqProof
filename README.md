# ReqProof: Multi-Artifact Requirement Verification for Software Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB.svg)](https://reactjs.org/)
[![Status](https://img.shields.io/badge/Status-MVP%20Ready-success.svg)]()

> **ReqProof** is an AI-assisted requirement verification system that combines evidence from source code, frontend components, backend APIs, and automated test reports using a deterministic evidence-fusion engine to detect implementation gaps and contradictions.

---

## 🌟 Key Highlights

1. **AI-Assisted Requirement Decomposition**: Uses the Google Gemini API to interpret high-level natural language requirements and decompose them into atomic, verifiable claims with explicit verification criteria.
2. **Multi-Artifact Evidence Harvesting**:
   - **Static Source Code**: Analyzes Java classes, route annotations (`@RestController`, `@GetMapping`, `@PostMapping`), and security configurations.
   - **Frontend Components**: Inspects TypeScript/React components for routes, forms, and input validation rules.
   - **Automated Tests**: Discovers and parses JUnit XML test execution reports.
   - **API Probing & Security Invariants**: Verifies route configurations and evaluates runtime behavior against expected criteria.
3. **Deterministic Evidence-Fusion Core**: Rather than relying on LLMs to invent verdicts, ReqProof applies a deterministic 8-step decision algorithm that classifies each claim into one of five defensible statuses:
   - **Fully Satisfied**: Corroborating evidence across all expected artifacts without contradiction.
   - **Partially Satisfied**: Partial behavior confirmed (e.g. frontend validation exists, but backend check missing).
   - **Missing**: Sufficient analysis confirms the requirement or behavior is completely absent.
   - **Contradictory**: Credible evidence sources conflict (e.g. source code validator exists, but runtime test fails or security config permits unauthorized bypass).
   - **Unverifiable**: Evidence is insufficient or artifacts could not be executed/evaluated.
4. **Bidirectional Traceability**: Cites specific file locations and line ranges (e.g., `src/auth/JwtValidator.java#L45`) for all supporting and contradicting observations.
5. **Interactive Visualization & Export**: React Flow dependency DAG visualization, real-time status dashboards, and one-click PDF & CSV export.

---

## 🏗️ System Architecture

```
ReqProof/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint & CORS middleware
│   │   ├── config.py         # System configuration & environment variables
│   │   ├── database.py       # SQLAlchemy engine & session management
│   │   ├── models/           # Domain entities (Users, Projects, Requirements, Claims, Evidence, Runs)
│   │   ├── schemas/          # Pydantic v2 validation contracts
│   │   ├── api/              # REST Endpoints (Auth, Projects, Requirements, Analysis, Reports)
│   │   ├── services/         # Business logic (Auth, ZIP scanner, Gemini decomposition, Reports)
│   │   ├── analyzers/        # Multi-artifact collectors (Java, TS, JUnit XML, API)
│   │   ├── engine/           # 5-status deterministic Evidence-Fusion Engine
│   │   └── tests/            # Test suites & benchmark verification
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + TypeScript + Vite Dashboard
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx           # Declarative React Router setup
│   │   ├── context/          # JWT authentication state
│   │   ├── components/       # Status badges, Evidence drilldown modal, Graph view
│   │   ├── pages/            # Login, Register, Projects, and Verification Dashboard
│   │   ├── services/api.ts   # Typed API client
│   │   └── types/            # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── samples/                  # Pre-packaged benchmark test apps
│   ├── sample-spring-react-app/
│   └── sample-spring-react-app.zip # Seeded contradiction benchmark
└── docker-compose.yml        # Multi-container local orchestration
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

---

### Option A: Local Development

#### 1. Start the FastAPI Backend
```bash
cd backend

# (Optional) Set your Gemini API key for live AI decomposition
export GEMINI_API_KEY="your-gemini-api-key"

# Run the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The API interactive Swagger documentation will be live at `http://localhost:8000/docs`.*

#### 2. Start the React Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
*The web interface will be accessible at `http://localhost:5173`.*

---

### Option B: Docker Compose

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`

---

## 🧪 Running the Automated Verification Tests

ReqProof includes comprehensive unit and integration tests verifying the evidence-fusion engine, full REST API lifecycle, and sample benchmark contradiction detection:

```bash
cd backend
PYTHONPATH=. python3 -m unittest discover -s app/tests
```

### Included Tests:
- `test_fusion_engine.py`: Verifies deterministic classification rules for `Fully Satisfied`, `Contradictory`, and `Unverifiable` states.
- `test_api.py`: Validates registration, project creation, requirement decomposition, graph generation, analysis runs, and report exports.
- `test_benchmark_sample.py`: Runs the complete multi-artifact pipeline on `sample-spring-react-app.zip`, demonstrating contradiction detection between a Java source validator and a failing JUnit test report.

---

## 📊 Ground-Truth Benchmark Case Study

The repository includes a controlled evaluation project (`samples/sample-spring-react-app.zip`):
- **Requirement**: *"The system must reject expired authentication tokens."*
- **Source Artifact**: `JwtValidator.java` contains `isExpired()` validation logic.
- **Security Config**: `SecurityConfig.java` permits unauthenticated access to `/api/auth/**`.
- **Automated Test Report**: `TEST-com.reqproof.auth.AuthTest.xml` records test failure:
  `AssertionFailedError: Expected 401 UNAUTHORIZED for expired token but received 200 OK`.
- **Result**: ReqProof flags this requirement as **`CONTRADICTORY`**, preventing a false-positive conclusion that code presence implies correct system behavior.

---

## 📄 License

This project is licensed under the MIT License.
