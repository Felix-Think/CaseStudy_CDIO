const LOGIN_ENDPOINT = "/api/auth/login";

const buildLoginPayload = (formData) => ({
  email: formData.get("email")?.trim() || "",
  password: formData.get("password") || "",
  remember: formData.get("remember") === "on",
});

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const feedback = document.getElementById("login-feedback");

  if (!loginForm) return;

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitBtn = loginForm.querySelector("button[type='submit']");
    if (!submitBtn) return;

    const defaultButtonMarkup = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = "Đang xác thực...";
    if (feedback) feedback.textContent = "";

    const payload = buildLoginPayload(new FormData(loginForm));

    try {
      const response = await fetch(LOGIN_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Đăng nhập thất bại. Vui lòng thử lại.");
      }

      if (feedback) {
        feedback.textContent = data.message || "Đăng nhập thành công.";
      }

      window.location.assign(data.redirect || "/nhap-case");
    } catch (error) {
      if (feedback) {
        feedback.textContent = error.message || "Có lỗi xảy ra. Vui lòng thử lại.";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = defaultButtonMarkup;
    }
  });
});
