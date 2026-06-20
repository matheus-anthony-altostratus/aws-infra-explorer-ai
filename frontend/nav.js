function navigate(sectionId) {
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    document.querySelectorAll(".sidebar-item").forEach(i => i.classList.remove("active"));

    document.getElementById("section-" + sectionId).classList.add("active");
    document.getElementById("nav-" + sectionId).classList.add("active");

    if (sectionId === "home")     { loadDashboard(); drawArchDiagram(); }
    if (sectionId === "history")  loadHistory();
    if (sectionId === "accounts") loadAccounts();
    if (sectionId === "users")    loadUsers();
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

function drawArchDiagram() {
    const canvas = document.getElementById("arch-diagram");
    if (!canvas || !canvas.offsetWidth) return;

    const ctx = canvas.getContext("2d");
    canvas.width = canvas.offsetWidth;
    canvas.height = 320;

    const W = canvas.width;
    const H = canvas.height;

    const nodes = [
        { id: "browser", label: "Ingeniero",     icon: "👤", x: 0.05, y: 0.5,  color: "#0166ff" },
        { id: "cf",      label: "CloudFront",     icon: "⬡",  x: 0.18, y: 0.5,  color: "#0166ff" },
        { id: "cognito", label: "Cognito",         icon: "🔐", x: 0.18, y: 0.18, color: "#f20e70" },
        { id: "apigw",   label: "API Gateway",    icon: "⚡", x: 0.35, y: 0.5,  color: "#141d5e" },
        { id: "lambda",  label: "Lambda",          icon: "λ",  x: 0.52, y: 0.5,  color: "#f20e70" },
        { id: "bedrock", label: "Bedrock",         icon: "🤖", x: 0.70, y: 0.2,  color: "#7c3aed" },
        { id: "s3",      label: "S3 Outputs",      icon: "🪣", x: 0.70, y: 0.5,  color: "#059669" },
        { id: "dynamo",  label: "DynamoDB",        icon: "🗄️", x: 0.70, y: 0.8,  color: "#b45309" },
        { id: "client",  label: "Cuenta Cliente",  icon: "☁️", x: 0.88, y: 0.5,  color: "#0166ff" },
    ];

    const edges = [
        { from: "browser", to: "cf",      label: "HTTPS"       },
        { from: "browser", to: "cognito", label: "login"        },
        { from: "cf",      to: "apigw",   label: "/analyze"    },
        { from: "apigw",   to: "lambda",  label: "invoke"      },
        { from: "lambda",  to: "bedrock", label: "InvokeModel" },
        { from: "lambda",  to: "s3",      label: "PutObject"   },
        { from: "lambda",  to: "dynamo",  label: "PutItem"     },
        { from: "lambda",  to: "client",  label: "AssumeRole"  },
    ];

    function getPos(node) { return { x: node.x * W, y: node.y * H }; }

    function drawArrow(x1, y1, x2, y2, label, color) {
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const nodeR = 30;
        const sx = x1 + Math.cos(angle) * nodeR;
        const sy = y1 + Math.sin(angle) * nodeR;
        const ex = x2 - Math.cos(angle) * nodeR;
        const ey = y2 - Math.sin(angle) * nodeR;

        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(ex, ey);
        ctx.strokeStyle = color || "rgba(1,102,255,0.4)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.beginPath();
        ctx.moveTo(ex, ey);
        ctx.lineTo(ex - 8 * Math.cos(angle - 0.4), ey - 8 * Math.sin(angle - 0.4));
        ctx.lineTo(ex - 8 * Math.cos(angle + 0.4), ey - 8 * Math.sin(angle + 0.4));
        ctx.closePath();
        ctx.fillStyle = color || "rgba(1,102,255,0.6)";
        ctx.fill();

        const mx = (sx + ex) / 2;
        const my = (sy + ey) / 2 - 8;
        ctx.font = "10px system-ui";
        ctx.fillStyle = "rgba(148,163,184,0.8)";
        ctx.textAlign = "center";
        ctx.fillText(label, mx, my);
    }

    function drawNode(node) {
        const { x, y } = getPos(node);
        const r = 30;

        const grd = ctx.createRadialGradient(x, y, 0, x, y, r * 1.5);
        grd.addColorStop(0, node.color + "33");
        grd.addColorStop(1, "transparent");
        ctx.beginPath();
        ctx.arc(x, y, r * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = "#0d1424";
        ctx.fill();
        ctx.strokeStyle = node.color;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.font = "18px system-ui";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(node.icon, x, y - 2);

        ctx.font = "11px system-ui";
        ctx.fillStyle = "#94a3b8";
        ctx.textBaseline = "top";
        ctx.fillText(node.label, x, y + r + 6);
    }

    edges.forEach(e => {
        const from = nodes.find(n => n.id === e.from);
        const to   = nodes.find(n => n.id === e.to);
        const p1   = getPos(from);
        const p2   = getPos(to);
        drawArrow(p1.x, p1.y, p2.x, p2.y, e.label, from.color + "88");
    });

    nodes.forEach(drawNode);
}