const API_URL = "https://gdz678r5rl.execute-api.eu-west-1.amazonaws.com";

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
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id: accountId, region: region }),
        });

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
            const response = await fetch(`${API_URL}/status/${analysisId}`);
            const data = await response.json();

            if (data.status === "completed") {
                showResults(data);
                return;
            } else if (data.status === "error") {
                throw new Error(data.error || "Error durante el análisis");
            }
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

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
