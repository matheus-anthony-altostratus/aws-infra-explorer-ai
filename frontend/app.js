const API_URL    = "https://gh41sneumj.execute-api.eu-west-1.amazonaws.com";
const COGNITO_URL = "https://cognito-idp.eu-west-1.amazonaws.com";
const CLIENT_ID  = "1hk5o7m7h2pkvbc5eh79tdgg8n";

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
        headers: { "Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": target },
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

function logout() { clearTokens(); showAuthScreen("login"); }

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

async function initApp() {
    document.getElementById("auth-screen").style.display = "none";
    document.getElementById("app-screen").style.display = "block";
    await _fetchAccounts();
    navigate("home");
}

async function _fetchAccounts() {
    try {
        const response = await fetch(`${API_URL}/accounts`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (!response.ok) return;
        const data = await response.json();
        _accountsData = data.groups || [];
        populateAccountSelect(_accountsData);
    } catch (err) {}
}

// ─── Auth screen ─────────────────────────────────────────────────────────────

let _pendingEmail = "", _pendingSession = "", _pendingUsername = "";

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
    if (!email.toLowerCase().endsWith("@altostratus.es")) { showAuthError("Solo se permiten correos @altostratus.es"); return; }
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

// ─── Accounts ────────────────────────────────────────────────────────────────

let _accountsData = [];
let _editingAccount = null;

async function loadAccounts() {
    const container = document.getElementById("accounts-container");
    container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">Cargando cuentas...</p>`;
    try {
        const response = await fetch(`${API_URL}/accounts`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await response.json();
        _accountsData = data.groups || [];
        renderAccounts(_accountsData);
        populateAccountSelect(_accountsData);
    } catch (err) {
        container.innerHTML = `<p style="color:#f472b6; font-size:14px;">Error al cargar las cuentas.</p>`;
    }
}

async function refreshAccountSelect() {
    await _fetchAccounts();
}

function renderAccounts(groups) {
    const container = document.getElementById("accounts-container");
    if (groups.length === 0) {
        container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">No hay cuentas registradas. Usa el formulario para añadir la primera.</p>`;
        return;
    }

    const html = groups.map(group => `
        <div style="margin-bottom:24px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                <span style="font-size:16px;">🏢</span>
                <h3 style="font-size:15px; font-weight:600; color:var(--text-primary); margin:0;">${group.group_name}</h3>
                <span style="font-size:11px; color:var(--text-secondary); background:rgba(255,255,255,0.05); border:1px solid var(--border); padding:2px 8px; border-radius:10px;">${group.accounts.length} cuenta${group.accounts.length !== 1 ? "s" : ""}</span>
            </div>
            <table style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border);">
                        <th style="padding:8px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Account Name</th>
                        <th style="padding:8px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Account ID</th>
                        <th style="padding:8px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Alias</th>
                        <th style="padding:8px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Región por defecto</th>
                        <th style="padding:8px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    ${group.accounts.map(acc => `
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:12px 16px; font-size:13px; font-weight:500; color:var(--text-primary);">${acc.account_name}</td>
                        <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary); font-family:monospace;">${acc.account_id}</td>
                        <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary);">${acc.alias || "—"}</td>
                        <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary);">${acc.default_region}</td>
                        <td style="padding:12px 16px; display:flex; gap:8px;">
                            <button onclick="openEditAccount('${group.group_id}', '${acc.account_id}')" style="font-size:12px; background:rgba(1,102,255,0.15); border:1px solid rgba(1,102,255,0.3); color:#60a5fa; padding:4px 10px; border-radius:6px; cursor:pointer;">Editar</button>
                            <button onclick="deleteAccount('${group.group_id}', '${acc.account_id}', '${acc.account_name}')" style="font-size:12px; background:rgba(242,14,112,0.1); border:1px solid rgba(242,14,112,0.3); color:#f472b6; padding:4px 10px; border-radius:6px; cursor:pointer;">Eliminar</button>
                        </td>
                    </tr>`).join("")}
                </tbody>
            </table>
        </div>
    `).join("");

    container.innerHTML = html;
}

function populateAccountSelect(groups) {
    const select = document.getElementById("accountSelect");
    if (!select) return;
    select.innerHTML = `<option value="">— Selecciona una cuenta —</option>`;
    groups.forEach(group => {
        const optgroup = document.createElement("optgroup");
        optgroup.label = group.group_name;
        group.accounts.forEach(acc => {
            const opt = document.createElement("option");
            opt.value = JSON.stringify({ account_id: acc.account_id, account_name: acc.account_name, default_region: acc.default_region });
            opt.textContent = `${acc.account_name} (${acc.account_id})`;
            optgroup.appendChild(opt);
        });
        select.appendChild(optgroup);
    });
}

function onAccountSelect() {
    const select = document.getElementById("accountSelect");
    if (!select.value) return;
    const acc = JSON.parse(select.value);
    document.getElementById("region").value = acc.default_region;
}

function openAddAccount() {
    _editingAccount = null;
    document.getElementById("account-form-title").textContent = "Añadir cuenta";
    document.getElementById("acc-group-id").value = "";
    document.getElementById("acc-group-name").value = "";
    document.getElementById("acc-group-name").style.display = "none";
    document.getElementById("acc-account-id").value = "";
    document.getElementById("acc-account-name").value = "";
    document.getElementById("acc-alias").value = "";
    document.getElementById("acc-region").value = "eu-west-1";
    document.getElementById("acc-account-id").disabled = false;
    _populateGroupSelect();
    document.getElementById("account-modal").style.display = "flex";
}

function _populateGroupSelect() {
    const select = document.getElementById("acc-group-select");
    select.innerHTML = `<option value="">— Selecciona un grupo —</option>`;
    _accountsData.forEach(g => {
        const opt = document.createElement("option");
        opt.value = g.group_id;
        opt.textContent = g.group_name;
        select.appendChild(opt);
    });
}

function onGroupSelect() {
    const select = document.getElementById("acc-group-select");
    const group  = _accountsData.find(g => g.group_id === select.value);
    if (group) {
        document.getElementById("acc-group-id").value   = group.group_id;
        document.getElementById("acc-group-name").value = group.group_name;
        document.getElementById("acc-group-name").style.display = "none";
    }
}

function toggleNewGroup() {
    const input  = document.getElementById("acc-group-name");
    const select = document.getElementById("acc-group-select");
    const showing = input.style.display !== "none";
    if (showing) {
        input.style.display = "none";
        input.value = "";
        select.disabled = false;
    } else {
        input.style.display = "block";
        input.focus();
        select.value = "";
        select.disabled = true;
        document.getElementById("acc-group-id").value = "";
    }
}

function openEditAccount(groupId, accountId) {
    const group = _accountsData.find(g => g.group_id === groupId);
    const acc   = group?.accounts.find(a => a.account_id === accountId);
    if (!acc) return;
    _editingAccount = { group_id: groupId, account_id: accountId };
    document.getElementById("account-form-title").textContent = "Editar cuenta";
    document.getElementById("acc-group-id").value = groupId;
    document.getElementById("acc-group-name").value = group.group_name;
    document.getElementById("acc-account-id").value = accountId;
    document.getElementById("acc-account-name").value = acc.account_name;
    document.getElementById("acc-alias").value = acc.alias || "";
    document.getElementById("acc-region").value = acc.default_region;
    document.getElementById("acc-account-id").disabled = true;
    document.getElementById("account-modal").style.display = "flex";
}

function closeAccountModal() {
    document.getElementById("account-modal").style.display = "none";
    document.getElementById("account-form-error").style.display = "none";
}

async function saveAccount() {
    const groupId     = document.getElementById("acc-group-id").value.trim();
    const groupName   = document.getElementById("acc-group-name").value.trim();
    const accountId   = document.getElementById("acc-account-id").value.trim();
    const accountName = document.getElementById("acc-account-name").value.trim();
    const alias       = document.getElementById("acc-alias").value.trim();
    const region      = document.getElementById("acc-region").value;
    const errorEl     = document.getElementById("account-form-error");
    errorEl.style.display = "none";

    if (!groupName || !accountId || !accountName) {
        errorEl.textContent = "Grupo, Account ID y Account Name son requeridos.";
        errorEl.style.display = "block";
        return;
    }
    if (!/^\d{12}$/.test(accountId)) {
        errorEl.textContent = "El Account ID debe ser un número de 12 dígitos.";
        errorEl.style.display = "block";
        return;
    }

    const btn = document.getElementById("account-save-btn");
    btn.disabled = true; btn.textContent = "Guardando...";

    try {
        let response;
        if (_editingAccount) {
            response = await fetch(`${API_URL}/accounts/${_editingAccount.group_id}/${_editingAccount.account_id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
                body: JSON.stringify({ group_name: groupName, account_name: accountName, alias, default_region: region }),
            });
        } else {
            response = await fetch(`${API_URL}/accounts`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
                body: JSON.stringify({ group_id: groupId || undefined, group_name: groupName, account_id: accountId, account_name: accountName, alias, default_region: region }),
            });
        }
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Error al guardar");
        }
        closeAccountModal();
        loadAccounts();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    } finally {
        btn.disabled = false; btn.textContent = "Guardar";
    }
}

async function deleteAccount(groupId, accountId, accountName) {
    if (!confirm(`¿Eliminar la cuenta "${accountName}" (${accountId})?`)) return;
    try {
        const response = await fetch(`${API_URL}/accounts/${groupId}/${accountId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (!response.ok) throw new Error("Error al eliminar");
        loadAccounts();
    } catch (err) {
        alert(err.message);
    }
}

// ─── Analyzer ────────────────────────────────────────────────────────────────

async function analyze() {
    const select    = document.getElementById("accountSelect");
    const region    = document.getElementById("region").value;
    const errorBox  = document.getElementById("error-box");
    errorBox.style.display = "none";

    if (!select.value) {
        errorBox.textContent = "Selecciona una cuenta para analizar.";
        errorBox.style.display = "block";
        return;
    }

    const acc = JSON.parse(select.value);
    setLoading(true);
    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
            body: JSON.stringify({ account_id: acc.account_id, region, user_email: getUserEmail() }),
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
        [`infra_${data.region}.json`]:          "📄 JSON",
        [`documentation_${data.region}.md`]:    "📄 Documentación (.md)",
        [`suggestions_${data.region}.md`]:      "💡 Sugerencias (.md)",
        [`diagram_${data.region}.drawio`]:      "🏗️ Diagrama draw.io",
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

// ─── History ─────────────────────────────────────────────────────────────────

async function loadHistory() {
    const container = document.getElementById("history-container");
    container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">Cargando historial...</p>`;
    try {
        const response = await fetch(`${API_URL}/history`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await response.json();
        renderHistory(data.analyses || []);
    } catch (err) {
        container.innerHTML = `<p style="color:#f472b6; font-size:14px;">Error al cargar el historial.</p>`;
    }
}

function renderHistory(analyses) {
    const container = document.getElementById("history-container");
    if (analyses.length === 0) {
        container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">No hay análisis registrados aún.</p>`;
        return;
    }

    const rows = analyses.map(a => {
        const date    = new Date(a.timestamp).toLocaleString("es-ES", { dateStyle: "short", timeStyle: "short" });
        const age     = (Date.now() - new Date(a.timestamp).getTime()) / (1000 * 60 * 60 * 24);
        const expired = age > 30;
        const downloads = expired
            ? `<span style="color:var(--text-secondary); font-size:12px;">Expirado</span>`
            : `<a onclick="redownload('${a.analysis_id}', '${a.region}')" style="color:#60a5fa; cursor:pointer; font-size:13px;">Ver descargas</a>`;
        return `
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary);">${date}</td>
            <td style="padding:12px 16px;">
                <p style="font-size:13px; font-weight:600; color:var(--text-primary); margin:0;">${a.account_name || a.account_id}</p>
                <p style="font-size:11px; color:var(--text-secondary); margin:2px 0 0;">${a.group_name || ""}</p>
            </td>
            <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary); font-family:monospace;">${a.account_id}</td>
            <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary);">${a.region}</td>
            <td style="padding:12px 16px; font-size:13px; color:var(--text-secondary);">${a.user_email || "—"}</td>
            <td style="padding:12px 16px;">${downloads}</td>
        </tr>`;
    }).join("");

    container.innerHTML = `
        <table style="width:100%; border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid var(--border);">
                    <th style="padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Fecha</th>
                    <th style="padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Cuenta</th>
                    <th style="padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Account ID</th>
                    <th style="padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Región</th>
                    <th style="padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Analizado por</th>
                    <th style="padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Archivos</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>`;
}

async function redownload(analysisId, region) {
    const modal   = document.getElementById("downloads-modal");
    const content = document.getElementById("downloads-modal-content");
    content.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">Cargando archivos...</p>`;
    modal.style.display = "flex";

    try {
        const response = await fetch(`${API_URL}/status/${analysisId}`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        const data = await response.json();
        if (data.status !== "completed" || !data.downloads) {
            content.innerHTML = `<p style="color:#f472b6; font-size:14px;">Los archivos de este análisis ya no están disponibles.</p>`;
            return;
        }

        const fileLabels = {
            [`infra_${region}.json`]:          { label: "Inventario JSON",          icon: "📊" },
            [`documentation_${region}.md`]:    { label: "Documentación técnica",    icon: "📄" },
            [`suggestions_${region}.md`]:      { label: "Sugerencias Well-Arch.",   icon: "💡" },
            [`diagram_${region}.drawio`]:      { label: "Diagrama draw.io",         icon: "🏗️" },
        };

        const items = Object.entries(data.downloads).map(([filename, url]) => {
            const meta = fileLabels[filename] || { label: filename, icon: "📁" };
            return { filename, url, ...meta };
        });

        content.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:10px;">
                ${items.map(f => `
                <div style="display:flex; align-items:center; justify-content:space-between; padding:12px 16px; background:#060d1a; border:1px solid var(--border); border-radius:8px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:20px;">${f.icon}</span>
                        <span style="font-size:13px; font-weight:500; color:var(--text-primary);">${f.label}</span>
                    </div>
                    <a href="${f.url}" target="_blank" style="font-size:12px; background:rgba(1,102,255,0.15); border:1px solid rgba(1,102,255,0.3); color:#60a5fa; padding:6px 14px; border-radius:6px; text-decoration:none; white-space:nowrap;">⬇ Descargar</a>
                </div>`).join("")}
            </div>
            <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--border); display:flex; justify-content:flex-end;">
                <button onclick="downloadAll(${JSON.stringify(items.map(f => f.url))})" style="background:rgba(1,102,255,0.2); border:1px solid rgba(1,102,255,0.4); color:#60a5fa; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer;">⬇ Descargar todos</button>
            </div>`;
    } catch (err) {
        content.innerHTML = `<p style="color:#f472b6; font-size:14px;">Error al obtener los archivos.</p>`;
    }
}

function downloadAll(urls) {
    urls.forEach(url => window.open(url, "_blank"));
}

function closeDownloadsModal() {
    document.getElementById("downloads-modal").style.display = "none";
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
    document.getElementById("accountSelect").value = "";
    document.getElementById("error-box").style.display = "none";
}

function setLoading(loading) {
    document.getElementById("btnText").style.display     = loading ? "none" : "flex";
    document.getElementById("btnLoading").style.display  = loading ? "flex" : "none";
    document.getElementById("submitBtn").disabled        = loading;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
