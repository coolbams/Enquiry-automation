import uvicorn


def main() -> None:
    """Run the FastAPI app via the package entry point."""
    uvicorn.run("enquiry_automation.main:app", host="0.0.0.0", port=8000, reload=True)
