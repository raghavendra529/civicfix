/**
 * CivicFix Frontend API Client & Authentication Engine
 */
const API_BASE = "";

// Helper for formatted category names
const CATEGORY_NAMES = {
  broken_streetlight: "Broken Streetlight",
  crack: "Road Crack",
  garbage: "Garbage Debris",
  manhole: "Damaged Manhole",
  normal: "Normal Pavement",
  pipeline_leakage: "Pipeline Leakage",
  pothole: "Pothole"
};

const CATEGORY_BADGES = {
  pothole: "badge-pothole",
  crack: "badge-crack",
  manhole: "badge-manhole",
  garbage: "badge-garbage",
  broken_streetlight: "badge-broken_streetlight",
  pipeline_leakage: "badge-pipeline_leakage",
  normal: "badge-normal"
};

// --- Authentication State Helpers ---
function getAuthToken() {
  return localStorage.getItem("civicfix_token") || "";
}

function getStoredUser() {
  try {
    const raw = localStorage.getItem("civicfix_user");
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function setAuthSession(token, user) {
  localStorage.setItem("civicfix_token", token);
  localStorage.setItem("civicfix_user", JSON.stringify(user));
  renderAuthNav();
}

function clearAuthSession() {
  localStorage.removeItem("civicfix_token");
  localStorage.removeItem("civicfix_user");
  renderAuthNav();
}

// --- Auth API Calls ---
async function sendEmailOtp(email, name = "") {
  const res = await fetch(`${API_BASE}/api/auth/send-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, name })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to send verification code");
  return data;
}

async function verifyEmailOtp(email, otp) {
  const res = await fetch(`${API_BASE}/api/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, otp })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to verify code");
  setAuthSession(data.token, data.user);
  return data;
}

async function sendPhoneOtp(countryCode, phoneNumber) {
  const res = await fetch(`${API_BASE}/api/auth/send-phone-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ country_code: countryCode, phone_number: phoneNumber })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to send SMS code");
  return data;
}

async function getSmtpStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/smtp-status`);
    return await res.json();
  } catch (e) {
    return { configured: false };
  }
}

async function configureSmtp(email, appPassword) {
  const res = await fetch(`${API_BASE}/api/auth/configure-smtp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, app_password: appPassword })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to configure Gmail SMTP");
  return data;
}

async function verifyPhoneOtp(countryCode, phoneNumber, otp) {
  const res = await fetch(`${API_BASE}/api/auth/verify-phone-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ country_code: countryCode, phone_number: phoneNumber, otp: otp })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to verify phone code");
  setAuthSession(data.token, data.user);
  return data;
}

async function loginWithPassword(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Invalid email or password");
  setAuthSession(data.token, data.user);
  return data;
}

async function registerAccount(name, email, password, role = "citizen") {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Registration failed");
  setAuthSession(data.token, data.user);
  return data;
}

async function logoutUser() {
  const token = getAuthToken();
  try {
    if (token) {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
    }
  } catch (e) {
    console.error("Logout API call error:", e);
  } finally {
    clearAuthSession();
    showToast("You have been securely logged out.", "success");
    setTimeout(() => {
      window.location.href = "/";
    }, 800);
  }
}

async function checkAuthStatus() {
  const token = getAuthToken();
  if (!token) {
    clearAuthSession();
    return null;
  }
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.authenticated && data.user) {
      localStorage.setItem("civicfix_user", JSON.stringify(data.user));
      renderAuthNav();
      return data.user;
    } else {
      clearAuthSession();
      return null;
    }
  } catch (err) {
    console.error("Failed to check auth status:", err);
    return getStoredUser();
  }
}

// --- Dynamic Navbar Auth Display ---
function renderAuthNav() {
  const navContainer = document.getElementById("auth-nav-container");
  if (!navContainer) return;

  const user = getStoredUser();
  if (user) {
    const roleBadge = user.role === "admin" 
      ? '<span class="px-2 py-0.5 text-[10px] font-extrabold uppercase bg-purple-100 text-purple-700 rounded-full border border-purple-200">Municipal Admin</span>'
      : '<span class="px-2 py-0.5 text-[10px] font-extrabold uppercase bg-emerald-100 text-emerald-700 rounded-full border border-emerald-200">Citizen</span>';

    navContainer.innerHTML = `
      <div class="flex items-center space-x-2 sm:space-x-3">
        <div class="hidden md:flex flex-col text-right">
          <span class="text-xs font-bold text-slate-800 leading-tight">${user.name}</span>
          <span class="text-[10px] text-slate-400">${user.email}</span>
        </div>
        ${roleBadge}
        <button onclick="logoutUser()" title="Logout" class="px-3 py-1.5 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg border border-red-200 transition-colors flex items-center space-x-1">
          <i class="fa-solid fa-arrow-right-from-bracket"></i>
          <span class="hidden sm:inline">Logout</span>
        </button>
      </div>
    `;
  } else {
    navContainer.innerHTML = `
      <div class="flex items-center space-x-2">
        <a href="/login.html" class="px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:text-blue-600 rounded-lg hover:bg-slate-100 transition-colors">
          Log In
        </a>
        <a href="/register.html" class="px-3.5 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors">
          Register
        </a>
      </div>
    `;
  }
}

// --- Data APIs ---
async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch stats:", err);
    return null;
  }
}

async function fetchComplaints(params = {}) {
  try {
    const token = getAuthToken();
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/api/complaints?${query}`, { headers });
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch complaints:", err);
    return { complaints: [] };
  }
}

async function predictImage(file, threshold = 0.50) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("threshold", threshold);

  const res = await fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Prediction request failed");
  }
  return await res.json();
}

async function submitComplaint(formData) {
  const token = getAuthToken();
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/api/complaints`, {
    method: "POST",
    headers: headers,
    body: formData
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to submit complaint");
  }
  return await res.json();
}

async function updateStatus(id, newStatus) {
  const token = getAuthToken();
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/api/complaints/${id}/status`, {
    method: "PATCH",
    headers: headers,
    body: JSON.stringify({ status: newStatus })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to update status");
  }
  return await res.json();
}

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container") || createToastContainer();
  const toast = document.createElement("div");
  const bg = type === "success" ? "bg-emerald-600" : (type === "warning" ? "bg-amber-600" : "bg-red-600");
  toast.className = `${bg} text-white px-5 py-3 rounded-lg shadow-lg flex items-center space-x-2 text-sm font-medium transition-all transform translate-y-2 opacity-0 duration-300`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.classList.remove("translate-y-2", "opacity-0"); }, 10);
  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function createToastContainer() {
  const div = document.createElement("div");
  div.id = "toast-container";
  div.className = "fixed bottom-5 right-5 z-50 flex flex-col space-y-2";
  document.body.appendChild(div);
  return div;
}

// Auto-run on page load
document.addEventListener("DOMContentLoaded", () => {
  renderAuthNav();
  checkAuthStatus();
});
