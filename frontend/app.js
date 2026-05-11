const API_URL = "https://gh41sneumj.execute-api.eu-west-1.amazonaws.com";
const COGNITO_URL = "https://cognito-idp.eu-west-1.amazonaws.com";
const CLIENT_ID = "1hk5o7m7h2pkvbc5eh79tdgg8n";

// ─── Auth ────────────────────────────────────────────────────────────────────

function getToken() { return localStorage.getItem("access_token"); }

function saveTokens(accessToken, idToken, expiresIn) {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("id_token", idToken);
    localStorage.setItem("token_expiry", Date.now() + expiresIn * 1000);
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("id_token");
    localStorage.removeItem("token_expiry");
}

function isTokenValid() {
    const expiry = localStorage.getItem("token_expiry");
    return expiry && Date.now() < parseInt(expiry);
}

function getUserEmail() {
    const idToken = localStorage.getItem("id_token");
    if (!idToken) return null;
    try { return JSON.parse(atob(idToken.split(".")[1])).email; }
    catch { return null; }
}

async function cognitoRequest(target, body) {
    const response = await fetch(COGNITO_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": target,
        },
        body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw data;
    return data;
}

async function login(email, password) {
    const data = await cognitoRequest("AWSCognitoIdentityProviderService.InitiateAuth", {
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: CLIENT_ID,
        AuthParameters: { USERNAME: email, PASSWORD: password },
    });
    if (data.ChallengeName === "NEW_PASSWORD_REQUIRED") {
        return { challenge: "NEW_PASSWORD_REQUIRED", session: data.Session, username: email };
    }
    const t = data.AuthenticationResult;
    saveTokens(t.AccessToken, t.IdToken, t.ExpiresIn);
    return { success: true };
}

async function register(email, password) {
    await cognitoRequest("AWSCognitoIdentityProviderService.SignUp", {
        ClientId: CLIENT_ID,
        Username: email,
        Password: password,
        UserAttributes: [{ Name: "email", Value: email }],
    });
    return { success: true };
}

async function confirmCode(email, code) {
    await cognitoRequest("AWSCognitoIdentityProviderService.ConfirmSignUp", {
        ClientId: CLIENT_ID,
        Username: email,
        ConfirmationCode: code,
    });
    return { success: true };
}

async function setNewPassword(username, newPassword, session) {
    const data = await cognitoRequest("AWSCognitoIdentityProviderService.RespondToAuthChallenge", {
        ClientId: CLIENT_ID,
        ChallengeName: "NEW_PASSWORD_REQUIRED",
        Session: session,
        ChallengeResponses: { USERNAME: username, NEW_PASSWORD: newPassword },
    });
    const t = data.AuthenticationResult;
    saveTokens(t.AccessToken, t.IdToken, t.ExpiresIn);
    return { success: true };
}

function logout() {
    clearTokens();
    showAuthScreen("login");
}

// ─── Init ────────────────────────────────────────────────────────────────────

window.addEventListener("load", () => {
    if (!isTokenValid()) {
        showAuthScreen("login");
        document.body.style.visibility = "visible";
        return;
    }
    const email = getUserEmail();
    if (email) {
        document.getElementById("user-email").textContent = email;
        document.getElementById("user-info").style.display = "flex";
    }
    document.body.style.visibility = "visible";
    initApp();
});

function initApp() {
    document.getElementById("auth-screen").style.display = "none";
    document.getElementById("app-screen").style.display = "block";
    navigate("home");
}

// ─── Auth screen ─────────────────────────────────────────────────────────────

let _pendingEmail = "";
let _pendingSession = "";
let _pendingUsername = "";

function showAuthScreen(view) {
    document.getElementById("auth-screen").style.display = "flex";
    document.getElementById("app-screen").style.display = "none";
    ["view-login", "view-register", "view-confirm", "view-newpassword"].forEach(id => {
        document.getElementById(id).style.display = "none";
    });
    document.getElementById("view-" + view).style.display = "block";
    document.getElementById("auth-error").style.display = "none";
}

function showAuthError(msg) {
    const el = document.getElementById("auth-error");
    el.textContent = msg;
    el.style.display = "block";
}

async function submitLogin() {
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const btn = document.getElementById("login-btn");
    if (!email || !password) { showAuthError("Completa todos los campos."); return; }
    btn.disabled = true; btn.textContent = "Iniciando sesión...";
    document.getElementById("auth-error").style.display = "none";
    try {
        const result = await login(email, password);
        if (result.challenge === "NEW_PASSWORD_REQUIRED") {
            _pendingSession = result.session;
            _pendingUsername = result.username;
            showAuthScreen("newpassword");
            return;
        }
        const userEmail = getUserEmail();
        if (userEmail) {
            document.getElementById("user-email").textContent = userEmail;
            document.getElementById("user-info").style.display = "flex";
        }
        initApp();
    } catch (err) {
        showAuthError(err.message || "Credenciales incorrectas.");
    } finally {
        btn.disabled = false; btn.textContent = "Iniciar sesión";
    }
}

async function submitRegister() {
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const btn = document.getElementById("register-btn");
    if (!email || !password) { showAuthError("Completa todos los campos."); return; }
    if (!email.toLowerCase().endsWith("@altostratus.es")) {
        showAuthError("Solo se permiten correos @altostratus.es");
        return;
    }
    if (password.length < 8) { showAuthError("La contraseña debe tener al menos 8 caracteres."); return; }
    btn.disabled = true; btn.textContent = "Registrando...";
    document.getElementById("auth-error").style.display = "none";
    try {
        await register(email, password);
        _pendingEmail = email;
        showAuthScreen("confirm");
    } catch (err) {
        const msg = err.message || "";
        if (msg.includes("altostratus")) showAuthError("Solo se permiten correos @altostratus.es");
        else if (msg.includes("already exists")) showAuthError("Este correo ya está registrado.");
        else showAuthError(msg || "Error al registrarse.");
    } finally {
        btn.disabled = false; btn.textContent = "Crear cuenta";
    }
}

async function submitConfirm() {
    const code = document.getElementById("confirm-code").value.trim();
    const btn = document.getElementById("confirm-btn");
    if (!code) { showAuthError("Ingresa el código de verificación."); return; }
    btn.disabled = true; btn.textContent = "Verificando...";
    document.getElementById("auth-error").style.display = "none";
    try {
        await confirmCode(_pendingEmail, code);
        showAuthScreen("login");
        document.getElementById("login-email").value = _pendingEmail;
    } catch (err) {
        showAuthError(err.message || "Código incorrecto.");
    } finally {
        btn.disabled = false; btn.textContent = "Verificar";
    }
}

async function submitNewPassword() {
    const password = document.getElementById("newpwd-password").value;
    const btn = document.getElementById("newpwd-btn");
    if (!password || password.length < 8) { showAuthError("Mínimo 8 caracteres."); return; }
    btn.disabled = true; btn.textContent = "Guardando...";
    try {
        await setNewPassword(_pendingUsername, password, _pendingSession);
        const userEmail = getUserEmail();
        if (userEmail) {
            document.getElementById("user-email").textContent = userEmail;
            document.getElementById("user-info").style.display = "flex";
        }
        initApp();
    } catch (err) {
        showAuthError(err.message || "Error al cambiar contraseña.");
    } finally {
        btn.disabled = false; btn.textContent = "Guardar contraseña";
    }
}

// ─── Analyzer ────────────────────────────────────────────────────────────────

async function analyze() {
    const accountId = document.getElementById("accountId").value.trim();
    const region = document.getElementById("region").value;
    const errorBox = document.getElementById("error-box");
    errorBox.style.display = "none";
    if (!accountId || !/^\d{12}$/.test(accountId)) {
        errorBox.textContent = "El Account ID debe ser un número de 12 dígitos.";
        errorBox.style.display = "block";
        return;
    }
    setLoading(true);
    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
            body: JSON.stringify({ account_id: accountId, region: region }),
        });
        if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Error desconocido");
        await pollStatus(data.analysis_id);
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.style.display = "block";
        setLoading(false);
    }
}

async function pollStatus(analysisId) {
    const errorBox = document.getElementById("error-box");
    while (true) {
        await sleep(5000);
        try {
            const response = await fetch(`${API_URL}/status/${analysisId}`, {
                headers: { "Authorization": `Bearer ${getToken()}` },
            });
            if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
            const data = await response.json();
            if (data.status === "completed") { showResults(data); return; }
            if (data.status === "error") throw new Error(data.error || "Error durante el análisis");
        } catch (error) {
            errorBox.textContent = error.message;
            errorBox.style.display = "block";
            setLoading(false);
            return;
        }
    }
}

function showResults(data) {
    document.getElementById("docContent").innerHTML = marked.parse(data.documentation);
    document.getElementById("sugContent").innerHTML = marked.parse(data.suggestions);
    const downloadLinks = document.getElementById("downloadLinks");
    downloadLinks.innerHTML = "";
    const fileLabels = {
        ["infra_" + data.region + ".json"]: "📄 JSON",
        ["documentation_" + data.region + ".md"]: "📄 Documentación (.md)",
        ["suggestions_" + data.region + ".md"]: "💡 Sugerencias (.md)",
        ["diagram_" + data.region + ".drawio"]: "🏗️ Diagrama draw.io",
    };
    for (const [filename, url] of Object.entries(data.downloads)) {
        const label = fileLabels[filename] || filename;
        const isPrimary = filename.endsWith(".drawio");
        downloadLinks.innerHTML += `<a href="${url}" target="_blank" class="download-btn ${isPrimary ? "primary" : ""}">${label}</a>`;
    }
    document.getElementById("resultRegion").textContent = data.region;
    document.getElementById("form-section").style.display = "none";
    document.getElementById("results-section").style.display = "block";
    setLoading(false);
}

// ─── UI helpers ──────────────────────────────────────────────────────────────

function switchTab(tab) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
    document.getElementById("tab-" + tab).classList.add("active");
    document.querySelector(`[data-tab="${tab}"]`).classList.add("active");
}

function resetForm() {
    document.getElementById("form-section").style.display = "block";
    document.getElementById("results-section").style.display = "none";
    document.getElementById("accountId").value = "";
    document.getElementById("error-box").style.display = "none";
}

function setLoading(loading) {
    document.getElementById("btnText").style.display = loading ? "none" : "flex";
    document.getElementById("btnLoading").style.display = loading ? "flex" : "none";
    document.getElementById("submitBtn").disabled = loading;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
