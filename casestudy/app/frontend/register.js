const REGISTER_ENDPOINT = "/api/auth/register";

const buildRegisterPayload = (formData) => ({
  email: formData.get("email")?.trim() || "",
  password: formData.get("password") || "",
  passwordConfirm: formData.get("passwordConfirm") || "",
});

document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.getElementById("register-form");
  const registerFeedback = document.getElementById("register-feedback");

  if (!registerForm) return;

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitBtn = registerForm.querySelector("button[type='submit']");
    if (!submitBtn) return;

    const defaultButtonMarkup = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = "Đang gửi hồ sơ...";
    if (registerFeedback) {
      registerFeedback.textContent = "";
    }

    const formData = new FormData(registerForm);
    const payload = buildRegisterPayload(formData);

    try {
      const response = await fetch(REGISTER_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Không thể đăng ký. Vui lòng thử lại.");
      }

      if (registerFeedback) {
        registerFeedback.textContent = data.message || "Đăng ký thành công.";
      }

      window.setTimeout(() => {
        window.location.assign(data.redirect || "/login");
      }, 600);
    } catch (error) {
      if (registerFeedback) {
        registerFeedback.textContent = error.message || "Có lỗi xảy ra. Vui lòng thử lại.";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = defaultButtonMarkup;
    }
  });
});
