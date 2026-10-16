const form = document.querySelector("#enquiry-form");
const statusMessage = document.querySelector("#form-status");
const submitButton = form.querySelector('button[type="submit"]');

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusMessage.textContent = "";
  statusMessage.dataset.state = "";
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "Sending...";

  const formData = new FormData(form);
  const enquiry = Object.fromEntries(formData.entries());

  try {
    const response = await fetch("/enquiries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(enquiry),
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail ?? "We couldn’t send your enquiry. Please try again.");
    }

    statusMessage.textContent = result.message;
    form.reset();
  } catch (error) {
    statusMessage.dataset.state = "error";
    statusMessage.textContent =
      error instanceof Error
        ? error.message
        : "Something went wrong. Please try again.";
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "Send your enquiry";
  }
});