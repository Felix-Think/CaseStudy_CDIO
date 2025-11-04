// Định nghĩa base URL của API
const AGENT_API_BASE = "http://127.0.0.1:9000";

// Hàm gọi API
async function callApiSession(caseId, userAction) {
  try {
    const response = await fetch(`${AGENT_API_BASE}/api/agent/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        case_id: caseId,
        user_action: userAction,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("✅ API trả về:", data);
    return data;
  } catch (error) {
    console.error("❌ Lỗi khi gọi API:", error.message);
  }
}

// Gọi hàm test
(async () => {
  console.log("🚀 Đang gửi yêu cầu...");
  result= await callApiSession("drowning_pool_001", "Bắt đầu nhiệm vụ.");
  if (result?.session_id){
    console.log("🎉 Thành công! Session ID:", result.session_id);
  }
})();

