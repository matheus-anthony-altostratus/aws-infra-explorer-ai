const API_URL    = "https://gh41sneumj.execute-api.eu-west-1.amazonaws.com";
const COGNITO_URL = "https://cognito-idp.eu-west-1.amazonaws.com";
const CLIENT_ID  = "1hk5o7m7h2pkvbc5eh79tdgg8n";

// ─── Auth ─────────────────────────────────────────────────────────────────────

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

// ─── Init ─────────────────────────────────────────────────────────────────────

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
        _accountsData = (data.groups || []).map(g => ({
            ...g,
            accounts: g.accounts.filter(a => a.account_id !== "PROFILE"),
        }));
        populateAccountSelect(_accountsData);
    } catch (err) {}
}

// ─── Auth screen ──────────────────────────────────────────────────────────────

let _pendingEmail = "", _pendingSession = "", _pendingUsername = "";

function showAuthScreen(view) {
    document.getElementById("auth-screen").style.display = "flex";
    document.getElementById("app-screen").style.display = "none";
    ["view-login", "view-register", "view-confirm", "view-newpassword", "view-resetpwd"].forEach(id => {
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
        showAuthError(_translateCognitoError(err.message));
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

// ─── Accounts ─────────────────────────────────────────────────────────────────

let _accountsData = [];
let _editingAccount = null;
let _profilesCache = {};

async function loadAccounts() {
    const container = document.getElementById("accounts-container");
    container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">Cargando cuentas...</p>`;
    try {
        const response = await fetch(`${API_URL}/accounts`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await response.json();
        _accountsData = (data.groups || []).map(g => ({
            ...g,
            accounts: g.accounts.filter(a => a.account_id !== "PROFILE"),
        }));
        _profilesCache = {};
        renderAccounts(_accountsData);
        populateAccountSelect(_accountsData);
    } catch (err) {
        container.innerHTML = `<p style="color:#f472b6; font-size:14px;">Error al cargar las cuentas.</p>`;
    }
}

function renderAccounts(groups) {
    const container = document.getElementById("accounts-container");
    window._openGroups = window._openGroups || {};
    if (groups.length === 0) {
        container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">No hay cuentas registradas.</p>`;
        return;
    }

    const cmcColors = { esencial: "#6B7280", avanzado: "#0166ff", gestionado: "#10b981" };
    const cmcLabels = { esencial: "Esencial", avanzado: "Avanzado", gestionado: "Gestionado" };

    const html = groups.map(group => {
        const color      = group.accounts[0]?.color || "#0166ff";
        const colorAlpha = color + "18";
        const profile    = _profilesCache[group.group_id] || {};
        const cmcLevel   = profile.cmc_level || "";
        const cmcColor   = cmcColors[cmcLevel] || "#6B7280";
        const hasTerraform = profile.iac === "Terraform";

        const badges = [
            cmcLevel ? `<span style="font-size:11px; background:${cmcColor}22; color:${cmcColor}; border:1px solid ${cmcColor}44; padding:2px 8px; border-radius:10px; font-weight:600;">${cmcLabels[cmcLevel]}</span>` : "",
            hasTerraform ? `<span style="font-size:11px; background:rgba(124,58,237,0.15); color:#a78bfa; border:1px solid rgba(124,58,237,0.3); padding:2px 8px; border-radius:10px;">Terraform</span>` : "",
        ].filter(Boolean).join("");

        return `
        <div style="margin-bottom:12px; border:1px solid var(--border); border-radius:12px; overflow:hidden;">
            <div onclick="toggleGroup('${group.group_id}')" style="display:flex; align-items:center; gap:10px; padding:14px 18px; cursor:pointer; background:${colorAlpha}; border-left:4px solid ${color}; user-select:none;">
                <span id="arrow-${group.group_id}" style="font-size:12px; color:var(--text-secondary); transition:transform .2s;">▶</span>
                <span style="font-size:16px;">🏢</span>
                <h3 style="font-size:14px; font-weight:600; color:var(--text-primary); margin:0; flex:1;">${group.group_name}</h3>
                <div style="display:flex; align-items:center; gap:6px;">
                    ${badges}
                    <span style="font-size:11px; color:var(--text-secondary); background:rgba(255,255,255,0.05); border:1px solid var(--border); padding:2px 8px; border-radius:10px;">${group.accounts.length} cuenta${group.accounts.length !== 1 ? "s" : ""}</span>
                <button onclick="event.stopPropagation(); openProfile('${group.group_id}', '${group.group_name}')" style="font-size:11px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399; padding:3px 10px; border-radius:6px; cursor:pointer;">📋 Perfil</button>
                    <button onclick="event.stopPropagation(); openAddAccountInGroup('${group.group_id}', '${group.group_name}')" style="font-size:11px; background:rgba(1,102,255,0.1); border:1px solid rgba(1,102,255,0.3); color:#60a5fa; padding:3px 10px; border-radius:6px; cursor:pointer;">+ Cuenta</button>
                    <button onclick="event.stopPropagation(); openEditGroup('${group.group_id}', '${group.group_name}')" style="font-size:11px; background:rgba(255,255,255,0.05); border:1px solid var(--border); color:var(--text-secondary); padding:3px 10px; border-radius:6px; cursor:pointer;">✏️</button>
                    <button onclick="event.stopPropagation(); deleteGroup('${group.group_id}', '${group.group_name}')" style="font-size:11px; background:rgba(242,14,112,0.1); border:1px solid rgba(242,14,112,0.3); color:#f472b6; padding:3px 10px; border-radius:6px; cursor:pointer;">🗑️</button>
                </div>
            </div>
            <div id="group-${group.group_id}" style="display:none;">
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background:#0a0f1e;">
                            <th style="padding:8px 18px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Account Name</th>
                            <th style="padding:8px 18px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Account ID</th>
                            <th style="padding:8px 18px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Alias</th>
                            <th style="padding:8px 18px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Región</th>
                            <th style="padding:8px 18px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em;">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${group.accounts.map(acc => `
                        <tr style="border-top:1px solid var(--border);">
                            <td style="padding:11px 18px; font-size:13px; font-weight:500; color:var(--text-primary);">${acc.account_name}</td>
                            <td style="padding:11px 18px; font-size:12px; color:var(--text-secondary); font-family:monospace;">${acc.account_id}</td>
                            <td style="padding:11px 18px; font-size:13px; color:var(--text-secondary);">${acc.alias || "—"}</td>
                            <td style="padding:11px 18px; font-size:13px; color:var(--text-secondary);">${acc.default_region}</td>
                            <td style="padding:11px 18px; display:flex; gap:8px;">
                                <button onclick="openEditAccount('${group.group_id}', '${acc.account_id}')" style="font-size:12px; background:rgba(1,102,255,0.15); border:1px solid rgba(1,102,255,0.3); color:#60a5fa; padding:4px 10px; border-radius:6px; cursor:pointer;">Editar</button>
                                <button onclick="deleteAccount('${group.group_id}', '${acc.account_id}', '${acc.account_name}')" style="font-size:12px; background:rgba(242,14,112,0.1); border:1px solid rgba(242,14,112,0.3); color:#f472b6; padding:4px 10px; border-radius:6px; cursor:pointer;">Eliminar</button>
                            </td>
                        </tr>`).join("")}
                    </tbody>
                </table>
            </div>
        </div>`;
    }).join("");

    container.innerHTML = html;
}

function toggleGroup(groupId) {
    const panel = document.getElementById(`group-${groupId}`);
    const arrow = document.getElementById(`arrow-${groupId}`);
    const open  = panel.style.display !== "none";
    panel.style.display   = open ? "none" : "block";
    arrow.style.transform = open ? "" : "rotate(90deg)";
    window._openGroups[groupId] = !open;
}

function populateAccountSelect(groups) {
    // Construye lista plana para el buscador
    window._allAccounts = [];
    groups.forEach(group => {
        group.accounts.forEach(acc => {
            window._allAccounts.push({
                label:          `${acc.account_name} (${acc.account_id})`,
                group:          group.group_name,
                value:          JSON.stringify({ account_id: acc.account_id, account_name: acc.account_name, default_region: acc.default_region }),
                default_region: acc.default_region,
            });
        });
    });
}

function filterAccounts() {
    const q = document.getElementById("accountSearch").value.toLowerCase();
    const dropdown = document.getElementById("accountDropdown");
    const matches = (window._allAccounts || []).filter(a =>
        a.label.toLowerCase().includes(q) || a.group.toLowerCase().includes(q)
    );
    renderAccountDropdown(matches);
    dropdown.style.display = matches.length ? "block" : "none";
}

function showAccountDropdown() {
    const q = document.getElementById("accountSearch").value.toLowerCase();
    const all = window._allAccounts || [];
    const matches = q ? all.filter(a => a.label.toLowerCase().includes(q) || a.group.toLowerCase().includes(q)) : all;
    renderAccountDropdown(matches);
    document.getElementById("accountDropdown").style.display = matches.length ? "block" : "none";
}

function hideAccountDropdown() {
    setTimeout(() => { document.getElementById("accountDropdown").style.display = "none"; }, 150);
}

function renderAccountDropdown(items) {
    const dropdown = document.getElementById("accountDropdown");
    if (!items.length) {
        dropdown.innerHTML = `<div style="padding:12px 14px; font-size:13px; color:var(--text-secondary);">Sin resultados</div>`;
        return;
    }
    // Guardar items en variable global para evitar problemas de escapado en HTML
    window._dropdownItems = items;
    dropdown.innerHTML = items.map((a, i) => `
        <div onmousedown="selectAccountByIndex(${i})"
             style="padding:10px 14px; cursor:pointer; border-bottom:1px solid var(--border); transition:background .1s;"
             onmouseover="this.style.background='rgba(1,102,255,0.1)'" onmouseout="this.style.background=''">
            <div style="font-size:13px; font-weight:500; color:var(--text-primary);">${a.label}</div>
            <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">${a.group}</div>
        </div>`).join("");
}

function selectAccountByIndex(i) {
    const a = window._dropdownItems[i];
    if (!a) return;
    document.getElementById("accountSelect").value = a.value;
    document.getElementById("accountSearch").value = a.label;
    document.getElementById("accountDropdown").style.display = "none";
    const acc = JSON.parse(a.value);
    document.getElementById("region").value = acc.default_region;
}

function selectAccount(value, label) {
    document.getElementById("accountSelect").value = value;
    document.getElementById("accountSearch").value = label;
    document.getElementById("accountDropdown").style.display = "none";
    try {
        const acc = JSON.parse(value);
        document.getElementById("region").value = acc.default_region;
    } catch {}
}

function clearAccountSelection() {
    document.getElementById("accountSelect").value = "";
    document.getElementById("accountSearch").value = "";
    document.getElementById("accountSearch").placeholder = "Buscar cuenta por nombre o grupo...";
}

function onAccountSelect() {}

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

function openAddAccount() {
    _editingAccount = null;
    document.getElementById("account-form-title").textContent = "Añadir cuenta";
    document.getElementById("acc-group-id").value = "";
    document.getElementById("acc-group-name").value = "";
    document.getElementById("acc-group-name").style.display = "none";
    document.getElementById("acc-group-select").disabled = false;
    document.getElementById("acc-account-id").value = "";
    document.getElementById("acc-account-name").value = "";
    document.getElementById("acc-alias").value = "";
    document.getElementById("acc-region").value = "eu-west-1";
    document.getElementById("acc-account-id").disabled = false;
    document.querySelector("input[name='acc-color'][value='#0166ff']").checked = true;
    _populateGroupSelect();
    document.getElementById("account-modal").style.display = "flex";
}

function openAddAccountInGroup(groupId, groupName) {
    openAddAccount();
    const select = document.getElementById("acc-group-select");
    select.value = groupId;
    document.getElementById("acc-group-id").value = groupId;
    document.getElementById("acc-group-name").value = groupName;
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
    const colorInput = document.querySelector(`input[name='acc-color'][value='${acc.color || "#0166ff"}']`);
    if (colorInput) colorInput.checked = true;
    _populateGroupSelect();
    document.getElementById("account-modal").style.display = "flex";
}

function openEditGroup(groupId, groupName) {
    const newName = prompt("Nuevo nombre del grupo:", groupName);
    if (!newName || newName.trim() === groupName) return;
    const group = _accountsData.find(g => g.group_id === groupId);
    if (!group) return;
    // Actualizar todas las cuentas del grupo con el nuevo nombre
    Promise.all(group.accounts.map(acc =>
        fetch(`${API_URL}/accounts/${groupId}/${acc.account_id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
            body: JSON.stringify({
                group_name:     newName.trim(),
                account_name:   acc.account_name,
                alias:          acc.alias || "",
                default_region: acc.default_region,
                color:          acc.color || "#0166ff",
            }),
        })
    )).then(() => loadAccounts()).catch(() => alert("Error al renombrar el grupo."));
}

async function deleteGroup(groupId, groupName) {
    const group = _accountsData.find(g => g.group_id === groupId);
    if (!group) return;
    const count = group.accounts.length;
    if (!confirm(`¿Eliminar el grupo "${groupName}" y sus ${count} cuenta${count !== 1 ? "s" : ""}? Esta acción no se puede deshacer.`)) return;
    try {
        await Promise.all(group.accounts.map(acc =>
            fetch(`${API_URL}/accounts/${groupId}/${acc.account_id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${getToken()}` },
            })
        ));
        loadAccounts();
    } catch {
        alert("Error al eliminar el grupo.");
    }
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
    const colorInput  = document.querySelector("input[name='acc-color']:checked");
    const color       = colorInput ? colorInput.value : "#0166ff";
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
                body: JSON.stringify({ group_name: groupName, account_name: accountName, alias, default_region: region, color }),
            });
        } else {
            response = await fetch(`${API_URL}/accounts`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
                body: JSON.stringify({ group_id: groupId || undefined, group_name: groupName, account_id: accountId, account_name: accountName, alias, default_region: region, color }),
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

// ─── Analyzer ─────────────────────────────────────────────────────────────────

async function analyze() {
    const select   = document.getElementById("accountSelect");
    const region   = document.getElementById("region").value;
    const errorBox = document.getElementById("error-box");
    errorBox.style.display = "none";

    if (!isTokenValid()) { clearTokens(); showAuthScreen("login"); return; }

    if (!document.getElementById("accountSelect").value) {
        errorBox.textContent = "Selecciona una cuenta para analizar.";
        errorBox.style.display = "block";
        return;
    }

    const acc = JSON.parse(document.getElementById("accountSelect").value);
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
    const errorBox  = document.getElementById("error-box");
    const stepLabel = document.getElementById("step-label");
    while (true) {
        await sleep(5000);
        try {
            const response = await fetch(`${API_URL}/status/${analysisId}`, {
                headers: { "Authorization": `Bearer ${getToken()}` },
            });
            if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
            const data = await response.json();
            if (data.step && stepLabel) stepLabel.textContent = data.step;
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
        [`infra_${data.region}.json`]:       "📄 JSON",
        [`documentation_${data.region}.md`]: "📄 Documentación (.md)",
        [`suggestions_${data.region}.md`]:   "💡 Sugerencias (.md)",
        [`diagram_${data.region}.drawio`]:   "🏗️ Diagrama draw.io",
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

// ─── History ──────────────────────────────────────────────────────────────────

async function loadHistory() {
    const container = document.getElementById("history-container");
    container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">Cargando historial...</p>`;
    try {
        const response = await fetch(`${API_URL}/history`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (response.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await response.json();
        renderHistory(data.groups || []);
    } catch (err) {
        container.innerHTML = `<p style="color:#f472b6; font-size:14px;">Error al cargar el historial.</p>`;
    }
}

function renderHistory(groups) {
    const container = document.getElementById("history-container");

    if (!groups || groups.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:48px 24px;">
                <div style="font-size:40px; margin-bottom:12px;">📭</div>
                <p style="font-size:15px; font-weight:600; color:var(--text-primary); margin:0 0 6px;">Sin análisis registrados</p>
                <p style="font-size:13px; color:var(--text-secondary); margin:0;">Los análisis completados aparecerán aquí automáticamente.</p>
            </div>`;
        return;
    }

    // Agrupar por group_name
    const byGroup = {};
    groups.forEach(g => {
        const key = g.group_name || g.account_id;
        if (!byGroup[key]) byGroup[key] = { group_name: key, color: g.color, items: [] };
        byGroup[key].items.push(g);
    });

    // Ordenar grupos por timestamp más reciente
    const sortedGroups = Object.values(byGroup).sort((a, b) => {
        const aLatest = a.items[0]?.analyses[0]?.timestamp || "";
        const bLatest = b.items[0]?.analyses[0]?.timestamp || "";
        return bLatest.localeCompare(aLatest);
    });

    // Obtener regiones únicas para el filtro
    const allRegions = [...new Set(groups.map(g => g.region))].sort();

    container.innerHTML = `
        <!-- Barra de filtros -->
        <div style="display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap;">
            <div style="position:relative; flex:1; min-width:200px;">
                <input id="hist-search" type="text" placeholder="Buscar por cuenta, grupo o Account ID..."
                       oninput="filterHistory()"
                       style="width:100%; background:#060d1a; border:1px solid var(--border); border-radius:8px;
                              padding:9px 14px 9px 36px; color:var(--text-primary); font-size:13px; outline:none;
                              transition:border-color .2s; box-sizing:border-box;"
                       onfocus="this.style.borderColor='var(--accent-blue)'"
                       onblur="this.style.borderColor='var(--border)'">
                <span style="position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--text-secondary); font-size:13px; pointer-events:none;">🔍</span>
            </div>
            <select id="hist-region" onchange="filterHistory()"
                    style="background:#060d1a; border:1px solid var(--border); border-radius:8px;
                           padding:9px 14px; color:var(--text-primary); font-size:13px; outline:none; cursor:pointer;">
                <option value="">Todas las regiones</option>
                ${allRegions.map(r => `<option value="${r}">${r}</option>`).join("")}
            </select>
        </div>

        <!-- Contador -->
        <div id="hist-counter" style="font-size:12px; color:var(--text-secondary); margin-bottom:16px;"></div>

        <!-- Grupos -->
        <div id="hist-groups"></div>`;

    // Guardar datos para el filtro
    window._historyGroups = sortedGroups;
    filterHistory();
}

function filterHistory() {
    const q       = (document.getElementById("hist-search")?.value || "").toLowerCase();
    const region  = document.getElementById("hist-region")?.value || "";
    const groups  = window._historyGroups || [];
    const counter = document.getElementById("hist-counter");
    const container = document.getElementById("hist-groups");

    let totalAccounts = 0;

    const html = groups.map(group => {
        // Filtrar cuentas dentro del grupo
        const filtered = group.items.filter(g => {
            const matchText = !q ||
                g.account_name.toLowerCase().includes(q) ||
                g.group_name.toLowerCase().includes(q) ||
                g.account_id.includes(q);
            const matchRegion = !region || g.region === region;
            return matchText && matchRegion;
        });

        if (!filtered.length) return "";
        totalAccounts += filtered.length;

        const color      = group.color || "#0166ff";
        const colorAlpha = color + "18";
        const colorBorder= color + "44";
        const groupKey   = `hg-${group.group_name.replace(/\s+/g, "_")}`;
        const latestTs   = filtered[0]?.analyses[0]?.timestamp || "";
        const latestDate = latestTs ? _timeAgo(latestTs) : "—";

        const accountCards = filtered.map(g => {
            const latest   = g.analyses[0];
            const date     = new Date(latest.timestamp).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" });
            const age      = (Date.now() - new Date(latest.timestamp).getTime()) / (1000 * 60 * 60 * 24);
            const expired  = age > 30;
            const daysLeft = Math.max(0, Math.ceil(30 - age));
            const accKey   = `ha-${g.account_id}_${g.region}`;

            const dlBtns = expired
                ? `<span style="font-size:12px; color:var(--text-secondary); background:rgba(255,255,255,0.04);
                                border:1px solid var(--border); padding:5px 12px; border-radius:6px;">⏱️ Archivos expirados</span>`
                : `<div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
                    ${[
                        { key: "json",    icon: "📊", label: "JSON"        },
                        { key: "docs",    icon: "📄", label: "Docs"        },
                        { key: "suggest", icon: "💡", label: "Sugerencias" },
                        { key: "drawio",  icon: "🏗️", label: "Diagrama"    },
                    ].map(f => `
                    <a onclick="downloadFile('${g.s3_prefix}', '${g.region}', '${f.key}')"
                       style="display:inline-flex; align-items:center; gap:4px; font-size:12px; font-weight:500;
                              background:rgba(255,255,255,0.04); border:1px solid var(--border); color:var(--text-primary);
                              padding:5px 11px; border-radius:6px; cursor:pointer; text-decoration:none; transition:all .15s;"
                       onmouseover="this.style.background='rgba(1,102,255,0.12)'; this.style.borderColor='${color}66';"
                       onmouseout="this.style.background='rgba(255,255,255,0.04)'; this.style.borderColor='var(--border)';">
                        ${f.icon} ${f.label}
                    </a>`).join("")}
                    <span style="font-size:11px; color:var(--text-secondary); margin-left:2px;">⏳ ${daysLeft}d</span>
                    <button onclick="sendToNotion('${g.s3_prefix}', '${g.account_id}')"
                            style="display:inline-flex; align-items:center; gap:4px; font-size:12px; font-weight:500;
                                   background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.3); color:#a5b4fc;
                                   padding:5px 11px; border-radius:6px; cursor:pointer; transition:all .15s;"
                            onmouseover="this.style.background='rgba(99,102,241,0.22)'"
                            onmouseout="this.style.background='rgba(99,102,241,0.12)'">
                        📝 Notion
                    </button>
                   </div>`;

            const prevAnalyses = g.analyses.slice(1);
            const prevSection  = prevAnalyses.length > 0 ? `
                <div style="margin-top:12px; padding-top:12px; border-top:1px solid var(--border);">
                    <button onclick="toggleHistoryCard('${accKey}')" id="btn-${accKey}"
                            style="background:none; border:none; color:var(--text-secondary); font-size:12px;
                                   cursor:pointer; display:flex; align-items:center; gap:5px; padding:0;"
                            onmouseover="this.style.color='var(--text-primary)'"
                            onmouseout="this.style.color='var(--text-secondary)'">
                        <span id="arrow-${accKey}" style="font-size:10px; transition:transform .2s; display:inline-block;">▶</span>
                        ${prevAnalyses.length} análisis anterior${prevAnalyses.length > 1 ? "es" : ""}
                    </button>
                    <div id="prev-${accKey}" style="display:none; flex-direction:column; gap:6px; margin-top:8px;">
                        ${prevAnalyses.map(a => {
                            const d    = new Date(a.timestamp).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" });
                            const aAge = (Date.now() - new Date(a.timestamp).getTime()) / (1000 * 60 * 60 * 24);
                            return `
                            <div style="display:flex; align-items:center; justify-content:space-between;
                                        padding:7px 12px; background:rgba(255,255,255,0.02);
                                        border-radius:7px; border:1px solid var(--border);">
                                <div style="display:flex; align-items:center; gap:10px;">
                                    <span style="font-size:12px; color:var(--text-secondary);">📅 ${d}</span>
                                    <span style="font-size:12px; color:var(--text-secondary);">·</span>
                                    <span style="font-size:12px; color:var(--text-secondary);">👤 ${a.user_email || "—"}</span>
                                </div>
                                ${aAge > 30
                                    ? `<span style="font-size:11px; color:var(--text-secondary);">Expirado</span>`
                                    : `<button onclick="redownload('${g.s3_prefix}', '${g.region}')"
                                              style="font-size:11px; background:rgba(1,102,255,0.1); border:1px solid rgba(1,102,255,0.3);
                                                     color:#60a5fa; padding:3px 10px; border-radius:6px; cursor:pointer;">
                                           Ver archivos
                                       </button>`}
                            </div>`;
                        }).join("")}
                    </div>
                </div>` : "";

            return `
            <div style="background:#0a0f1e; border:1px solid var(--border); border-radius:10px; padding:14px 16px; margin-bottom:10px;">
                <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:10px;">
                    <div>
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:3px;">
                            <span style="font-size:14px; font-weight:600; color:var(--text-primary);">${g.account_name}</span>
                            <span style="font-size:11px; background:${color}22; color:${color}; border:1px solid ${color}44;
                                         padding:1px 8px; border-radius:10px; font-weight:500;">${g.region}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:11px; font-family:monospace; color:var(--text-secondary);">${g.account_id}</span>
                            <span style="font-size:11px; color:var(--text-secondary);">·</span>
                            <span style="font-size:12px; color:var(--text-secondary);">📅 ${date}</span>
                            <span style="font-size:11px; color:var(--text-secondary);">·</span>
                            <span style="font-size:12px; color:var(--text-secondary);">👤 ${latest.user_email || "—"}</span>
                        </div>
                    </div>
                    <span style="font-size:11px; color:var(--text-secondary); white-space:nowrap; flex-shrink:0;
                                 background:rgba(255,255,255,0.04); border:1px solid var(--border);
                                 padding:2px 8px; border-radius:10px;">
                        ${g.analyses.length} análisis
                    </span>
                </div>
                ${dlBtns}
                ${prevSection}
            </div>`;
        }).join("");

        return `
        <div style="margin-bottom:12px; border:1px solid ${colorBorder}; border-radius:12px; overflow:hidden;">

            <!-- Cabecera del grupo — clickable -->
            <div onclick="toggleHistGroup('${groupKey}')"
                 style="display:flex; align-items:center; gap:10px; padding:14px 18px;
                        background:${colorAlpha}; border-left:4px solid ${color};
                        cursor:pointer; user-select:none;">
                <span id="garrow-${groupKey}" style="font-size:11px; color:${color}; transition:transform .2s; display:inline-block;">▶</span>
                <span style="font-size:15px; font-weight:700; color:var(--text-primary); flex:1;">${group.group_name}</span>
                <span style="font-size:12px; color:var(--text-secondary);">${filtered.length} cuenta${filtered.length !== 1 ? "s" : ""}</span>
                <span style="font-size:11px; color:var(--text-secondary);">·</span>
                <span style="font-size:12px; color:var(--text-secondary);">Último: ${latestDate}</span>
            </div>

            <!-- Cuentas del grupo — cerrado por defecto -->
            <div id="${groupKey}" style="display:none; padding:12px 14px;">
                ${accountCards}
            </div>
        </div>`;
    }).join("");

    const visible = html.replace(/<div style="margin-bottom:12px[^"]*"[^>]*>\s*<\/div>/g, "").trim();
    container.innerHTML = html || `
        <div style="text-align:center; padding:32px;">
            <p style="font-size:14px; color:var(--text-secondary);">Sin resultados para los filtros aplicados.</p>
        </div>`;

    const total = groups.reduce((s, g) => s + g.items.length, 0);
    if (counter) counter.textContent = `${totalAccounts} cuenta${totalAccounts !== 1 ? "s" : ""} · ${total} análisis en total`;
}

function toggleHistGroup(groupKey) {
    const panel = document.getElementById(groupKey);
    const arrow = document.getElementById(`garrow-${groupKey}`);
    const open  = panel.style.display !== "none";
    panel.style.display   = open ? "none" : "block";
    arrow.style.transform = open ? "" : "rotate(90deg)";
}

function toggleHistoryCard(accKey) {
    const panel = document.getElementById(`prev-${accKey}`);
    const arrow = document.getElementById(`arrow-${accKey}`);
    const open  = panel.style.display !== "none";
    panel.style.display   = open ? "none" : "flex";
    arrow.style.transform = open ? "" : "rotate(90deg)";
}

function _timeAgo(isoString) {
    const diff = Date.now() - new Date(isoString).getTime();
    const mins  = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days  = Math.floor(diff / 86400000);
    if (mins  < 60)  return `hace ${mins}m`;
    if (hours < 24)  return `hace ${hours}h`;
    if (days  < 30)  return `hace ${days}d`;
    return new Date(isoString).toLocaleDateString("es-ES");
}


function toggleHistoryCard(groupKey) {
    const panel = document.getElementById(`prev-${groupKey}`);
    const arrow = document.getElementById(`arrow-${groupKey}`);
    const btn   = document.getElementById(`btn-${groupKey}`);
    const open  = panel.style.display !== "none";
    panel.style.display  = open ? "none" : "flex";
    arrow.style.transform = open ? "" : "rotate(90deg)";
}

async function downloadFile(s3Prefix, region, fileKey) {
    const keyMap = {
        json:    `infra_${region}.json`,
        docs:    `documentation_${region}.md`,
        suggest: `suggestions_${region}.md`,
        drawio:  `diagram_${region}.drawio`,
    };
    const filename = keyMap[fileKey];
    if (!filename) return;
    try {
        // Pedir URL fresca al backend — regenera la presigned URL en el momento
        const res  = await fetch(`${API_URL}/download/${s3Prefix}/${filename}`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
            redirect: "manual",
        });
        // El endpoint /download devuelve 302 con Location header
        const url = res.headers.get("location") || res.url;
        if (url && url.startsWith("http")) {
            window.open(url, "_blank");
        } else {
            // Fallback: leer del status.json
            const statusRes  = await fetch(`${API_URL}/status/${s3Prefix}`, {
                headers: { "Authorization": `Bearer ${getToken()}` },
            });
            const data = await statusRes.json();
            const freshUrl = data.downloads?.[filename];
            if (freshUrl) window.open(freshUrl, "_blank");
            else alert("Archivo no disponible o expirado.");
        }
    } catch {
        alert("Error al obtener el archivo.");
    }
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
            [`infra_${region}.json`]:       { label: "Inventario JSON",        icon: "📊" },
            [`documentation_${region}.md`]: { label: "Documentación técnica",  icon: "📄" },
            [`suggestions_${region}.md`]:   { label: "Sugerencias Well-Arch.", icon: "💡" },
            [`diagram_${region}.drawio`]:   { label: "Diagrama draw.io",       icon: "🏗️" },
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

function downloadAll(urls) { urls.forEach(url => window.open(url, "_blank")); }

function closeDownloadsModal() {
    document.getElementById("downloads-modal").style.display = "none";
}

// ─── Service Profile ──────────────────────────────────────────────────────────

let _profileGroupId = null;

async function openProfile(groupId, groupName) {
    _profileGroupId = groupId;
    document.getElementById("profile-modal-title").textContent = groupName;
    document.getElementById("profile-view").style.display = "block";
    document.getElementById("profile-edit").style.display = "none";
    document.getElementById("profile-modal").style.display = "flex";
    document.getElementById("profile-loading").style.display = "block";
    document.getElementById("profile-view-content").style.display = "none";

    try {
        const res  = await fetch(`${API_URL}/profiles/${groupId}`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        const data = await res.json();
        const profile = data.profile || {};
        _profilesCache[groupId] = profile;
        _renderProfileView(profile);
    } catch {
        document.getElementById("profile-loading").textContent = "Error al cargar el perfil.";
    }
}

function _renderProfileView(p) {
    document.getElementById("pv-notion").textContent = p.notion_page_id
        ? "✅ Configurado"
        : "⚠️ No configurado";

    document.getElementById("profile-loading").style.display = "none";
    document.getElementById("profile-view-content").style.display = "block";

    const cmcColors = { esencial: "#6B7280", avanzado: "#0166ff", gestionado: "#10b981" };
    const cmcLabels = { esencial: "Esencial", avanzado: "Avanzado", gestionado: "Gestionado" };
    const level = p.cmc_level || "";
    const color = cmcColors[level] || "#6B7280";

    document.getElementById("pv-cmc").innerHTML = level
        ? `<span style="background:${color}22; color:${color}; border:1px solid ${color}44; padding:3px 12px; border-radius:20px; font-size:13px; font-weight:600;">${cmcLabels[level]}</span>`
        : `<span style="color:var(--text-secondary); font-size:13px;">No definido</span>`;

    document.getElementById("pv-identity").textContent = p.identity || "—";
    document.getElementById("pv-cicd").textContent     = (p.cicd || []).join(", ") || "—";
    document.getElementById("pv-iac").textContent      = p.iac || "—";
    document.getElementById("pv-monitoring").textContent = p.monitoring ? "Telefónica" : "—";

    const runbook = p.runbook || "";
    document.getElementById("pv-runbook").innerHTML = runbook
        ? marked.parse(runbook)
        : `<p style="color:var(--text-secondary); font-size:13px;">Sin runbook definido.</p>`;

    document.getElementById("profile-modal")._data = p;
}

function openProfileEdit() {
    const p = document.getElementById("profile-modal")._data || {};
    document.getElementById("profile-view").style.display = "none";
    document.getElementById("profile-edit").style.display = "block";

    document.querySelectorAll("input[name='pe-cmc']").forEach(r => r.checked = r.value === (p.cmc_level || ""));
    document.getElementById("pe-identity").value = p.identity || "";
    document.getElementById("pe-iac").value       = p.iac || "";

    document.querySelectorAll("input[name='pe-cicd']").forEach(cb => {
        cb.checked = (p.cicd || []).includes(cb.value);
    });

    document.getElementById("pe-monitoring").checked = !!p.monitoring;
    document.getElementById("pe-runbook").value = p.runbook || "";
    document.getElementById("pe-notion-page-id").value = p.notion_page_id || "";

}

function closeProfileEdit() {
    document.getElementById("profile-view").style.display = "block";
    document.getElementById("profile-edit").style.display = "none";
}

async function saveProfile() {
    const cmc_level      = document.querySelector("input[name='pe-cmc']:checked")?.value || "";
    const identity       = document.getElementById("pe-identity").value;
    const iac            = document.getElementById("pe-iac").value;
    const cicd           = [...document.querySelectorAll("input[name='pe-cicd']:checked")].map(c => c.value);
    const monitoring     = document.getElementById("pe-monitoring").checked;
    const runbook        = document.getElementById("pe-runbook").value;
    const notion_page_id = document.getElementById("pe-notion-page-id").value.trim();

    const btn = document.getElementById("profile-save-btn");
    btn.disabled = true; btn.textContent = "Guardando...";

    try {
        const res = await fetch(`${API_URL}/profiles/${_profileGroupId}`, {
            method:  "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
            body:    JSON.stringify({ cmc_level, identity, iac, cicd, monitoring, runbook, notion_page_id }),
        });
        if (!res.ok) throw new Error("Error al guardar");
        const p = { cmc_level, identity, iac, cicd, monitoring, runbook, notion_page_id };
        _profilesCache[_profileGroupId] = p;
        document.getElementById("profile-modal")._data = p;
        _renderProfileView(p);
        closeProfileEdit();
        renderAccounts(_accountsData);
    } catch {
        alert("Error al guardar el perfil.");
    } finally {
        btn.disabled = false; btn.textContent = "Guardar";
    }
}

function closeProfileModal() {
    document.getElementById("profile-modal").style.display = "none";
}

async function sendToNotion(s3Prefix, accountId) {
    // Buscar notion_page_id en el profile del grupo correspondiente
    const group = (_accountsData || []).find(g =>
        g.accounts.some(a => a.account_id === accountId)
    );
    const groupId = group?.group_id;

    if (!groupId) {
        alert("No se encontró el grupo de esta cuenta. Asegúrate de que está registrada en Cuentas.");
        return;
    }

    // Leer profile para obtener notion_page_id
    let notionPageId = "";
    try {
        const res  = await fetch(`${API_URL}/profiles/${groupId}`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        const data = await res.json();
        notionPageId = data.profile?.notion_page_id || "";
    } catch {}

    if (!notionPageId) {
        alert("Este cliente no tiene una página de Notion configurada.\n\nVe a Cuentas → Service Profile del cliente → añade el Page ID de Notion.");
        return;
    }

    const btn = event.target.closest("button");
    const originalText = btn.innerHTML;
    btn.disabled  = true;
    btn.innerHTML = "⏳ Enviando...";

    try {
        const res = await fetch(`${API_URL}/notion/${s3Prefix}`, {
            method:  "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
            body:    JSON.stringify({ notion_page_id: notionPageId }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Error desconocido");

        btn.innerHTML = "✅ Enviado";
        btn.style.background = "rgba(16,185,129,0.12)";
        btn.style.borderColor = "rgba(16,185,129,0.3)";
        btn.style.color = "#34d399";

        if (data.url) {
            setTimeout(() => window.open(data.url, "_blank"), 500);
        }
    } catch (err) {
        btn.disabled  = false;
        btn.innerHTML = originalText;
        alert(`Error al enviar a Notion: ${err.message}`);
    }
}

// ─── Users ───────────────────────────────────────────────────────────────────

async function loadUsers() {
    document.getElementById("users-container").innerHTML =
        `<p style="color:var(--text-secondary); font-size:14px;">Cargando...</p>`;
    try {
        const res = await fetch(`${API_URL}/users`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (res.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await res.json();
        renderUsers(data.users || []);
    } catch {
        document.getElementById("users-container").innerHTML =
            `<p style="color:#f472b6; font-size:14px;">Error al cargar los usuarios.</p>`;
    }
    loadUsersLog();
}

function renderUsers(users) {
    const container = document.getElementById("users-container");
    if (!users.length) {
        container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">No hay usuarios registrados.</p>`;
        return;
    }
    const me = getUserEmail();
    const statusColors = {
        CONFIRMED:             { bg: "rgba(16,185,129,0.1)",  border: "rgba(16,185,129,0.3)",  text: "#34d399", label: "Activo" },
        FORCE_CHANGE_PASSWORD: { bg: "rgba(245,158,11,0.1)",  border: "rgba(245,158,11,0.3)",  text: "#fbbf24", label: "Pendiente login" },
        UNCONFIRMED:           { bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.3)", text: "#94a3b8", label: "Sin confirmar" },
    };
    const thStyle = `padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--border);`;
    const rows = users.map(u => {
        const s = statusColors[u.status] || statusColors["UNCONFIRMED"];
        const created = new Date(u.created_at).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" });
        const isMe = u.email === me;
        return `<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:12px 16px; font-size:13px; color:var(--text-primary); font-weight:500;">${u.email}</td>
            <td style="padding:12px 16px;">
                <span style="font-size:11px; background:${s.bg}; color:${s.text}; border:1px solid ${s.border}; padding:2px 10px; border-radius:10px; font-weight:600;">${s.label}</span>
            </td>
            <td style="padding:12px 16px; font-size:12px; color:var(--text-secondary);">${created}</td>
            <td style="padding:12px 16px;">
                ${isMe
                    ? `<span style="font-size:12px; color:var(--text-secondary);">Tu cuenta</span>`
                    : `<button onclick="resetUserPassword('${u.email}')" style="font-size:12px; background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); color:#fbbf24; padding:4px 10px; border-radius:6px; cursor:pointer; margin-right:6px;">🔑 Reset</button><button onclick="deleteUser('${u.email}')" style="font-size:12px; background:rgba(242,14,112,0.1); border:1px solid rgba(242,14,112,0.3); color:#f472b6; padding:4px 10px; border-radius:6px; cursor:pointer;">Eliminar</button>`}
            </td>
        </tr>`;
    }).join("");
    container.innerHTML = `
        <table style="width:100%; border-collapse:collapse;">
            <thead><tr>
                <th style="${thStyle}">Email</th>
                <th style="${thStyle}">Estado</th>
                <th style="${thStyle}">Creado</th>
                <th style="${thStyle}">Acciones</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
}

async function loadUsersLog() {
    const container = document.getElementById("users-log-container");
    try {
        const res = await fetch(`${API_URL}/users/log`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (!res.ok) { container.innerHTML = ""; return; }
        const data = await res.json();
        const logs = data.logs || [];
        if (!logs.length) {
            container.innerHTML = `<p style="color:var(--text-secondary); font-size:13px;">Sin actividad registrada.</p>`;
            return;
        }
        container.innerHTML = logs.map(l => {
            const date = new Date(l.timestamp).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" });
            const colors = { CREATE: "#34d399", DELETE: "#f472b6", RESET_PASSWORD: "#fbbf24" };
            const icons  = { CREATE: "✅", DELETE: "🗑️", RESET_PASSWORD: "🔑" };
            const verbs  = { CREATE: "creó la cuenta de", DELETE: "eliminó la cuenta de", RESET_PASSWORD: "reseteó la contraseña de" };
            const color = colors[l.action] || "#94a3b8";
            const icon  = icons[l.action] || "•";
            const verb  = verbs[l.action] || l.action;
            return `<div style="display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid var(--border); font-size:13px;">
                <span>${icon}</span>
                <span style="color:var(--text-secondary);">${date}</span>
                <span style="color:var(--text-primary); font-weight:500;">${l.user_email}</span>
                <span style="color:var(--text-secondary);">${verb}</span>
                <span style="color:${color}; font-weight:500;">${l.target}</span>
            </div>`;
        }).join("");
    } catch {
        container.innerHTML = "";
    }
}

function openAddUser() {
    document.getElementById("new-user-email").value = "";
    document.getElementById("add-user-error").style.display = "none";
    document.getElementById("add-user-modal").style.display = "flex";
}

function closeAddUser() {
    document.getElementById("add-user-modal").style.display = "none";
}

async function createUser() {
    const email = document.getElementById("new-user-email").value.trim().toLowerCase();
    const errorEl = document.getElementById("add-user-error");
    const btn = document.getElementById("add-user-btn");
    errorEl.style.display = "none";
    if (!email) { errorEl.textContent = "El email es requerido."; errorEl.style.display = "block"; return; }
    if (!email.endsWith("@altostratus.es")) {
        errorEl.textContent = "Solo se permiten correos @altostratus.es";
        errorEl.style.display = "block";
        return;
    }
    btn.disabled = true; btn.textContent = "Creando...";
    try {
        const res = await fetch(`${API_URL}/users`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
            body: JSON.stringify({ email }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Error al crear usuario");
        closeAddUser();
        loadUsers();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    } finally {
        btn.disabled = false; btn.textContent = "Crear usuario";
    }
}

async function deleteUser(email) {
    if (!confirm(`¿Eliminar el acceso de ${email}?\nEsta acción quedará registrada.`)) return;
    try {
        const res = await fetch(`${API_URL}/users/${encodeURIComponent(email)}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Error al eliminar");
        loadUsers();
    } catch (err) {
        alert(err.message);
    }
}

async function resetUserPassword(email) {
    if (!confirm(`¿Enviar email de reset de contraseña a ${email}?\nEl usuario recibirá un código para establecer una nueva contraseña.`)) return;
    try {
        const res = await fetch(`${API_URL}/users/${encodeURIComponent(email)}/reset`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Error al resetear");
        alert(`✅ Email de reset enviado a ${email}`);
        loadUsers();
    } catch (err) {
        alert(err.message);
    }
}

async function submitResetPassword() {
    const email    = document.getElementById("reset-email").value.trim();
    const code     = document.getElementById("reset-code").value.trim();
    const password = document.getElementById("reset-newpwd").value;
    const btn      = document.getElementById("resetpwd-btn");
    if (!email || !code || !password) { showAuthError("Completa todos los campos."); return; }
    if (password.length < 8) { showAuthError("Mínimo 8 caracteres."); return; }
    btn.disabled = true; btn.textContent = "Restableciendo...";
    try {
        await cognitoRequest("AWSCognitoIdentityProviderService.ConfirmForgotPassword", {
            ClientId: CLIENT_ID,
            Username: email,
            ConfirmationCode: code,
            Password: password,
        });
        showAuthScreen("login");
        document.getElementById("login-email").value = email;
        alert("✅ Contraseña restablecida. Ya puedes iniciar sesión.");
    } catch (err) {
        showAuthError(_translateCognitoError(err.message));
    } finally {
        btn.disabled = false; btn.textContent = "Restablecer contraseña";
    }
}

function _translateCognitoError(msg) {
    if (!msg) return "Error de autenticación.";
    const map = {
        "User does not exist":              "El usuario no existe.",
        "Incorrect username or password":   "Email o contraseña incorrectos.",
        "Password attempts exceeded":       "Demasiados intentos. Espera unos minutos.",
        "User is not confirmed":            "Tu cuenta no ha sido verificada.",
        "User is disabled":                 "Tu cuenta ha sido desactivada.",
        "Invalid password":                 "La contraseña no cumple los requisitos (mín. 8 caracteres, mayúscula y número).",
        "Username/client id combination not found": "El usuario no existe.",
    };
    for (const [key, val] of Object.entries(map)) {
        if (msg.includes(key)) return val;
    }
    return msg;
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

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
    document.getElementById("btnText").style.display    = loading ? "none" : "flex";
    document.getElementById("btnLoading").style.display = loading ? "flex" : "none";
    document.getElementById("submitBtn").disabled       = loading;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

async function loadDashboard() {
    try {
        const res = await fetch(`${API_URL}/dashboard`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (res.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await res.json();
        renderDashboard(data);
    } catch {
        document.getElementById("dashboard-table").innerHTML =
            `<p style="color:#f472b6; font-size:14px;">Error al cargar el dashboard.</p>`;
    }
}

function renderDashboard(data) {
    document.getElementById("dm-clients").textContent = data.total_clients ?? "—";
    document.getElementById("dm-accounts").textContent = data.total_accounts ?? "—";
    document.getElementById("dm-alerts").textContent = data.total_alerts ?? 0;
    document.getElementById("dm-score").textContent = data.avg_score != null ? data.avg_score : "—";

    const container = document.getElementById("dashboard-table");
    const clients = data.clients || [];
    if (!clients.length) {
        container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">Sin cuentas registradas. Ve a Cuentas para añadir la primera.</p>`;
        return;
    }

    const thStyle = `padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--border);`;
    const rows = clients.map(c => {
        const scoreColor = c.score == null ? "#6B7280" : c.score >= 80 ? "#34d399" : c.score >= 50 ? "#fbbf24" : "#f472b6";
        const scoreBg = c.score == null ? "rgba(107,114,128,0.1)" : c.score >= 80 ? "rgba(16,185,129,0.1)" : c.score >= 50 ? "rgba(245,158,11,0.1)" : "rgba(242,14,112,0.1)";
        const scoreLabel = c.score != null ? c.score : "—";
        const dot = c.score == null ? "⚪" : c.score >= 80 ? "🟢" : c.score >= 50 ? "🟡" : "🔴";
        const lastDate = c.last_analysis ? _timeAgo(c.last_analysis) : "Sin análisis";
        return `<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:11px 16px; font-size:13px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:8px; height:8px; border-radius:50%; background:${c.color};"></span>
                    <span style="font-weight:500; color:var(--text-primary);">${c.group_name}</span>
                    <span style="color:var(--text-secondary); font-size:12px;">/ ${c.account_name}</span>
                </div>
            </td>
            <td style="padding:11px 16px; font-size:12px; font-family:monospace; color:var(--text-secondary);">${c.account_id}</td>
            <td style="padding:11px 16px; font-size:12px; color:var(--text-secondary);">${c.region}</td>
            <td style="padding:11px 16px;">
                <span style="display:inline-flex; align-items:center; gap:4px; font-size:12px; font-weight:600; color:${scoreColor}; background:${scoreBg}; border:1px solid ${scoreColor}33; padding:3px 10px; border-radius:10px;">
                    ${dot} ${scoreLabel}
                </span>
            </td>
            <td style="padding:11px 16px; font-size:12px; color:var(--text-secondary);">${c.alerts || 0}</td>
            <td style="padding:11px 16px; font-size:12px; color:var(--text-secondary);">${lastDate}</td>
        </tr>`;
    }).join("");

    container.innerHTML = `
        <table style="width:100%; border-collapse:collapse;">
            <thead><tr>
                <th style="${thStyle}">Cliente / Cuenta</th>
                <th style="${thStyle}">Account ID</th>
                <th style="${thStyle}">Región</th>
                <th style="${thStyle}">Health Score</th>
                <th style="${thStyle}">Alertas</th>
                <th style="${thStyle}">Último análisis</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
}

// ─── Dashboard Tabs & Alerts ────────────────────────────────────────────────

function switchDashboardTab(tab) {
    document.getElementById('dashboard-tab-summary').style.display = tab === 'summary' ? 'block' : 'none';
    document.getElementById('dashboard-tab-alerts').style.display = tab === 'alerts' ? 'block' : 'none';
    document.getElementById('dtab-summary').classList.toggle('active', tab === 'summary');
    document.getElementById('dtab-alerts').classList.toggle('active', tab === 'alerts');
    if (tab === 'alerts') loadAlerts();
}

let _alertsData = [];

async function loadAlerts() {
    try {
        const res = await fetch(`${API_URL}/alerts`, {
            headers: { "Authorization": `Bearer ${getToken()}` },
        });
        if (res.status === 401) { clearTokens(); showAuthScreen("login"); return; }
        const data = await res.json();
        _alertsData = data.alerts || [];
        populateAlertAccountFilter();
        renderAlerts(_alertsData);
    } catch {
        document.getElementById("alerts-table-container").innerHTML =
            `<p style="color:#f472b6; font-size:14px;">Error al cargar alertas.</p>`;
    }
}

function populateAlertAccountFilter() {
    const select = document.getElementById('alert-filter-account');
    const accounts = [...new Set(_alertsData.map(a => a.account_name))].sort();
    select.innerHTML = '<option value="">Todas las cuentas</option>' +
        accounts.map(n => `<option value="${n}">${n}</option>`).join('');
}

function filterAlerts() {
    const severity = document.getElementById('alert-filter-severity').value;
    const account = document.getElementById('alert-filter-account').value;
    let filtered = _alertsData;
    if (severity) filtered = filtered.filter(a => a.severity === severity);
    if (account) filtered = filtered.filter(a => a.account_name === account);
    renderAlerts(filtered);
}

function renderAlerts(alerts) {
    const container = document.getElementById('alerts-table-container');
    if (!alerts.length) {
        container.innerHTML = `<p style="color:var(--text-secondary); font-size:14px;">✅ No hay alertas activas con los filtros seleccionados.</p>`;
        return;
    }

    const severityBadge = (s) => {
        const map = {
            critical: { icon: '🔴', label: 'Crítica', color: '#f472b6', bg: 'rgba(242,14,112,0.1)' },
            high:     { icon: '🟠', label: 'Alta',    color: '#fb923c', bg: 'rgba(251,146,60,0.1)' },
            medium:   { icon: '🟡', label: 'Media',   color: '#fbbf24', bg: 'rgba(251,191,36,0.1)' },
            low:      { icon: '⚪', label: 'Baja',    color: '#94a3b8', bg: 'rgba(148,163,184,0.1)' },
            info:     { icon: 'ℹ️', label: 'Info',    color: '#60a5fa', bg: 'rgba(96,165,250,0.1)' },
        };
        const m = map[s] || map.info;
        return `<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:600;color:${m.color};background:${m.bg};border:1px solid ${m.color}33;padding:3px 9px;border-radius:10px;">${m.icon} ${m.label}</span>`;
    };

    // Agrupar por cuenta
    const groups = {};
    alerts.forEach(a => {
        const key = a.account_id || 'unknown';
        if (!groups[key]) groups[key] = { ...a, alerts: [] };
        groups[key].alerts.push(a);
    });

    const scoreIcon = (count) => count >= 7 ? '🔴' : count >= 3 ? '🟡' : '🟢';

    const html = Object.values(groups).map((g, i) => {
        const thStyle = `padding:8px 12px; text-align:left; font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--border);`;
        const rows = g.alerts.map(a => `<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:8px 12px;">${severityBadge(a.severity)}</td>
            <td style="padding:8px 12px; font-size:12px; color:var(--text-secondary);">${a.type || ''}</td>
            <td style="padding:8px 12px; font-size:12px; color:var(--text-primary); font-family:monospace;">${a.resource || ''}</td>
            <td style="padding:8px 12px; font-size:13px; color:var(--text-secondary);">${a.msg || ''}</td>
        </tr>`).join('');

        return `<div style="border:1px solid var(--border); border-radius:10px; margin-bottom:10px; overflow:hidden;">
            <div onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'; this.querySelector('.chevron').textContent = this.nextElementSibling.style.display === 'none' ? '▶' : '▼';"
                 style="padding:14px 18px; cursor:pointer; display:flex; align-items:center; gap:12px; background:rgba(255,255,255,0.02); user-select:none;">
                <span class="chevron" style="font-size:10px; color:var(--text-secondary);">▶</span>
                <span style="width:10px; height:10px; border-radius:50%; background:${g.color || '#0166ff'};"></span>
                <span style="font-size:13px; font-weight:600; color:var(--text-primary);">${g.group_name || ''} / ${g.account_name || g.account_id}</span>
                <span style="font-size:12px; color:var(--text-secondary); font-family:monospace;">${g.account_id}</span>
                <span style="margin-left:auto; font-size:12px; color:var(--text-secondary);">${scoreIcon(g.alerts.length)} ${g.alerts.length} alerta${g.alerts.length !== 1 ? 's' : ''}</span>
            </div>
            <div style="display:none; padding:0 12px 12px;">
                <table style="width:100%; border-collapse:collapse;">
                    <thead><tr>
                        <th style="${thStyle}">Severidad</th>
                        <th style="${thStyle}">Tipo</th>
                        <th style="${thStyle}">Recurso</th>
                        <th style="${thStyle}">Descripción</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </div>`;
    }).join('');

    container.innerHTML = `
        <div style="font-size:12px; color:var(--text-secondary); margin-bottom:12px;">${alerts.length} alerta${alerts.length !== 1 ? 's' : ''} en ${Object.keys(groups).length} cuenta${Object.keys(groups).length !== 1 ? 's' : ''}</div>
        ${html}`;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
