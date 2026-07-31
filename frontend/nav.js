function navigate(sectionId) {
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    document.querySelectorAll(".sidebar-item").forEach(i => i.classList.remove("active"));

    document.getElementById("section-" + sectionId).classList.add("active");
    document.getElementById("nav-" + sectionId).classList.add("active");

    if (sectionId === "home")     { loadDashboard(); drawArchDiagram(); }
    if (sectionId === "history")  loadHistory();
    if (sectionId === "accounts") loadAccounts();
    if (sectionId === "users")    loadUsers();
    if (sectionId === "connections") populateMultiGroups();
}

function copyTrustPolicy(btn) {
    const text = document.getElementById("trust-policy-json").textContent;
    navigator.clipboard.writeText(text);
    btn.textContent = "✅ Copiado";
    setTimeout(() => { btn.textContent = "📋 Copiar"; }, 2000);
}

function copyText(text, btn) {
    navigator.clipboard.writeText(text);
    btn.textContent = "✅ Copiado";
    setTimeout(() => { btn.textContent = "📋 Copiar"; }, 2000);
}

let _archRAF = null;

function drawArchDiagram() {
    const canvas = document.getElementById("arch-diagram");
    if (!canvas || !canvas.offsetWidth) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    canvas.width  = canvas.offsetWidth  * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const R = 23;

    // Pasos en orden. El camino va 1→2→…→8 y luego 8→1 (resultado).
    const steps = [
        { label: "Ingeniero",      icon: "👤", x: 0.08, y: 0.30, color: "#0166ff" },
        { label: "CloudFront",     icon: "🌐", x: 0.30, y: 0.30, color: "#0166ff" },
        { label: "Cognito",        icon: "🔐", x: 0.52, y: 0.30, color: "#f20e70" },
        { label: "API Gateway",    icon: "⚡", x: 0.74, y: 0.30, color: "#3b82f6" },
        { label: "Lambda",         icon: "⚙️", x: 0.92, y: 0.55, color: "#f20e70" },
        { label: "Cuenta Cliente", icon: "☁️", x: 0.74, y: 0.80, color: "#0166ff" },
        { label: "Bedrock",        icon: "🤖", x: 0.52, y: 0.80, color: "#7c3aed" },
        { label: "S3 + DynamoDB",  icon: "🪣", x: 0.30, y: 0.80, color: "#10b981" },
    ];
    const labels = ["abre la app", "login · JWT", "POST /analyze", "invoke",
                    "AssumeRole · lee infra", "genera docs", "guarda", "resultado"];

    const P = s => ({ x: s.x * canvas.offsetWidth, y: s.y * canvas.offsetHeight });

    function frame(now) {
        if (!canvas.offsetParent) { _archRAF = null; return; }
        const W = canvas.offsetWidth, H = canvas.offsetHeight;
        const t = now / 1000;
        ctx.clearRect(0, 0, W, H);

        for (let i = 0; i < steps.length; i++) {
            const from = steps[i];
            const to   = steps[(i + 1) % steps.length];
            const ret  = (i === steps.length - 1);
            const a = P(from), b = P(to);
            const col = ret ? "#34d399" : from.color;
            const dx = b.x - a.x, dy = b.y - a.y;
            const ang = Math.atan2(dy, dx);

            // línea
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = col + "40"; ctx.lineWidth = 1.5; ctx.stroke();

            // flecha justo antes del nodo destino
            const ax = b.x - Math.cos(ang) * R, ay = b.y - Math.sin(ang) * R;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(ax - 8 * Math.cos(ang - 0.45), ay - 8 * Math.sin(ang - 0.45));
            ctx.lineTo(ax - 8 * Math.cos(ang + 0.45), ay - 8 * Math.sin(ang + 0.45));
            ctx.closePath(); ctx.fillStyle = col + "dd"; ctx.fill();

            // partículas (lentas)
            for (let k = 0; k < 2; k++) {
                const u = 0.1 + (((t * 0.18) + i * 0.16 + k * 0.5) % 1) * 0.8;
                const px = a.x + dx * u, py = a.y + dy * u;
                const g = ctx.createRadialGradient(px, py, 0, px, py, 5);
                g.addColorStop(0, col); g.addColorStop(1, col + "00");
                ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI*2); ctx.fillStyle = g; ctx.fill();
                ctx.beginPath(); ctx.arc(px, py, 1.8, 0, Math.PI*2); ctx.fillStyle = "#fff"; ctx.fill();
            }

            // etiqueta del paso
            ctx.font = "10px system-ui"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillStyle = "rgba(148,163,184,0.95)";
            ctx.fillText(labels[i], (a.x + b.x) / 2, (a.y + b.y) / 2 - 10);
        }

        steps.forEach((s, i) => {
            const x = s.x * W, y = s.y * H;
            const pulse = 0.5 + 0.5 * Math.sin(t * 1.8 + i);
            const halo = ctx.createRadialGradient(x, y, R*0.6, x, y, R*(1.5 + pulse*0.45));
            halo.addColorStop(0, s.color + "44"); halo.addColorStop(1, s.color + "00");
            ctx.beginPath(); ctx.arc(x, y, R*(1.5 + pulse*0.45), 0, Math.PI*2); ctx.fillStyle = halo; ctx.fill();

            ctx.beginPath(); ctx.arc(x, y, R, 0, Math.PI*2); ctx.fillStyle = "#0d1424"; ctx.fill();
            ctx.strokeStyle = s.color; ctx.lineWidth = 1.5 + pulse; ctx.stroke();

            ctx.font = "15px system-ui"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillText(s.icon, x, y);

            // número de paso
            const bx = x + R * 0.72, by = y - R * 0.72;
            ctx.beginPath(); ctx.arc(bx, by, 9, 0, Math.PI*2); ctx.fillStyle = s.color; ctx.fill();
            ctx.strokeStyle = "#0a0f1e"; ctx.lineWidth = 2; ctx.stroke();
            ctx.font = "bold 11px system-ui"; ctx.fillStyle = "#fff";
            ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillText(String(i + 1), bx, by + 0.5);

            ctx.font = "11px system-ui"; ctx.fillStyle = "#cbd5e1"; ctx.textBaseline = "top";
            ctx.fillText(s.label, x, y + R + 6);
        });

        _archRAF = requestAnimationFrame(frame);
    }

    if (_archRAF) cancelAnimationFrame(_archRAF);
    _archRAF = requestAnimationFrame(frame);
}
