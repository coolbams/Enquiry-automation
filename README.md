<<<<<<< HEAD
# Enquiry-automation

Automated enquiry handling and related tooling.

## Overview

This repository contains code and assets for automating enquiry workflows. It includes Python-based backend logic and front-end assets built with HTML, CSS, and JavaScript.

## Features

- Enquiry processing and automation
- Simple web interface support
- Front-end styling and interaction logic
- Python-based workflow automation

## Repository information

- Owner: `coolbams`
- Repository: `Enquiry-automation`
- Default branch: `main`
- Primary language: `Python`

## Requirements

- Python 3.8+
- pip
- Optional: Node.js / npm if front-end tooling is added later

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/coolbams/Enquiry-automation.git
   cd Enquiry-automation
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .\.venv\Scripts\activate   # Windows
   ```

3. Install dependencies if a requirements file is present:

   ```bash
   pip install -r requirements.txt
   ```

## Project structure

A typical structure for this project may look like:

```text
Enquiry-automation/
├── app/
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── ...
├── templates/
│   └── ...
├── tests/
│   └── ...
├── requirements.txt
├── README.md
└── ...
```

If the repository layout differs, update this section to match the actual project structure.

## Usage

Use the project entry point or script appropriate to this repository. Typical examples:

```bash
python app.py
```

or

```bash
python main.py
```

If the app has a Flask, Django, or other framework entry point, replace the sample command above with the real command used by the project.

## Development

- Run tests with:

  ```bash
  pytest
  ```

- Format Python files with:

  ```bash
  black .
  ```

## Contributing

Contributions are welcome. Please open an issue or pull request with a clear description of the change and any relevant testing steps.

## License

No license file was detected in the repository metadata. Add a license if this project is intended to be open source.

---

This README was generated automatically and can be refined with project-specific details once the actual app entry points and structure are confirmed.
=======
# Enquiry Automation

A fast, production-ready enquiry intake and auto-responder service built with **FastAPI**, **SQLAlchemy**, and the **Resend API**, featuring multi-layered spam defense and automated CI testing.

---

## ✨ Features

- **Responsive Landing Page**: Clean, modern contact interface ("Northstar") served directly from FastAPI static files.
- **Instant Response with Background Tasks**: Enquiries are saved immediately, while confirmation emails are dispatched asynchronously in the background via FastAPI's `BackgroundTasks`.
- **Multi-Layered Spam Protection**:
  - **Honeypot Trap**: Invisible field in HTML traps automated web scrapers and drops them with zero database writes or email dispatches.
  - **Database Cooldown**: 5-minute cooldown query prevents repeat confirmation emails if the same email address submits multiple messages in quick succession.
- **SQLAlchemy & SQLite**: Lightweight, zero-config relational storage for incoming enquiries with timestamps and UUID primary keys.
- **Automated Test Suite**: Full `pytest` integration using in-memory SQLite and mocked email calls to ensure reliable test runs without consuming external API credits.
- **CI/CD with GitHub Actions**: Automated pipeline using `uv` and Python 3.14 that runs all unit and integration tests on every push.

---

## 🛠️ Tech Stack

- **Runtime & Package Manager**: Python `>=3.14`, [`uv`](https://github.com/astral-sh/uv)
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database & ORM**: SQLite, [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Email Service**: [Resend Python SDK](https://resend.com/)
- **Testing**: `pytest`, `httpx` (`TestClient`)
- **CI/CD**: GitHub Actions

---

## 📁 Project Structure

```
enquiry-automation/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline
├── src/
│   ├── templates/
│   │   ├── Index.html           # Contact form markup with honeypot
│   │   ├── Style.css            # Responsive styling
│   │   └── app.js               # Form submission handling
│   └── enquiry_automation/
│       ├── apis/
│       │   └── resendEmailApi.py # Resend email delivery integration
│       ├── database/
│       │   ├── connection.py    # Database engine and session dependency
│       │   └── models.py        # SQLAlchemy Enquiry model
│       └── main.py              # FastAPI app, endpoints, and background worker
├── tests/
│   ├── conftest.py              # In-memory SQLite fixtures & DB overrides
│   └── test_enquiries.py        # Automated test cases
├── pyproject.toml               # Project metadata & dependencies
├── uv.lock                      # Locked dependency tree
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have [uv](https://docs.astral.sh/uv/) installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository

```bash
git clone https://github.com/coolbams/Enquiry-automation.git
cd Enquiry-automation
```

### 3. Environment Variables

Create a `.env` file in the root directory:
```bash
RESEND_API_KEY=re_your_api_key_here
```

### 4. Install Dependencies

Install project dependencies into a virtual environment with `uv`:
```bash
uv sync
```

### 5. Run the Server

Start the FastAPI development server:
```bash
uv run fastapi dev src/enquiry_automation/main.py
```
Or with Uvicorn:
```bash
uv run uvicorn src.enquiry_automation.main:app --reload
```

The app will be available at:
- **Webpage**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Tests

The test suite runs against an isolated, in-memory SQLite database and mocks the Resend email API so no live emails are sent:

```bash
uv run pytest
```

---

## 📡 API Endpoints

### `GET /`
Serves the contact form HTML.

### `POST /enquiries`
Accepts a new enquiry submission.

#### Request Body
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "message": "We would like to discuss a project with your team.",
  "website": null
}
```

> **Note**: `website` is the hidden honeypot field. Legitimate users submit `null` or empty string. If filled, the request is silently dropped without saving to the database.

#### Response (`200 OK`)
```json
{
  "message": "Enquiry received successfully"
}
```

---

## 🛡️ Anti-Spam Architecture

```mermaid
flowchart TD
    A["User submits enquiry"] --> B{"Honeypot filled?<br/>(website != null)"}
    B -- Yes (Bot) --> C["Log warning & return 200 OK<br/>(No DB save, No email)"]
    B -- No (Human) --> D["Save Enquiry to SQLite"]
    D --> E{"Submitted in last 5 minutes?"}
    E -- Yes --> F["Skip email dispatch<br/>(Cooldown active)"]
    E -- No --> G["Enqueue send_email in BackgroundTasks"]
    G --> H["Deliver confirmation email via Resend"]
```

---

## 👤 Author

- **Sam** ([@coolbams](https://github.com/coolbams)) - *oyerindesamuel207@gmail.com*
>>>>>>> 2bfe8fe (Update Readme)
