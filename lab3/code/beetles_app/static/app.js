// ======================================
// Загрузка данных
// ======================================

async function loadTeams() {
    const response = await fetch("/api/teams");
    const teams = await response.json();

    const container = document.getElementById("teams");

    let html = `
        <table>
            <tr>
                <th>ID</th>
                <th>Название</th>
            </tr>
    `;

    teams.forEach(team => {
        html += `
            <tr>
                <td>${team.team_id}</td>
                <td>${team.team_name}</td>
            </tr>
        `;
    });

    html += "</table>";

    container.innerHTML = html;


    // Заполняем select
    const select = document.getElementById("expedition-team");

    select.innerHTML =
        '<option value="">Выберите команду</option>';

    teams.forEach(team => {
        select.innerHTML += `
            <option value="${team.team_id}">
                ${team.team_name}
            </option>
        `;
    });
}


async function loadPlaces() {
    const response = await fetch("/api/places");
    const places = await response.json();

    const container = document.getElementById("places");

    let html = `
        <table>
            <tr>
                <th>ID</th>
                <th>Место</th>
            </tr>
    `;

    places.forEach(place => {
        html += `
            <tr>
                <td>${place.place_id}</td>
                <td>${place.place_name}</td>
            </tr>
        `;
    });

    html += "</table>";

    container.innerHTML = html;


    const select = document.getElementById("expedition-place");

    select.innerHTML =
        '<option value="">Выберите место</option>';

    places.forEach(place => {
        select.innerHTML += `
            <option value="${place.place_id}">
                ${place.place_name}
            </option>
        `;
    });
}


async function loadSpecies() {
    const response = await fetch("/api/species");
    const species = await response.json();

    const container = document.getElementById("species");

    let html = `
        <table>
            <tr>
                <th>ID</th>
                <th>Вид</th>
            </tr>
    `;

    species.forEach(item => {
        html += `
            <tr>
                <td>${item.species_id}</td>
                <td>${item.species_name}</td>
            </tr>
        `;
    });

    html += "</table>";

    container.innerHTML = html;


    const select = document.getElementById("catch-species");

    select.innerHTML =
        '<option value="">Выберите вид</option>';

    species.forEach(item => {
        select.innerHTML += `
            <option value="${item.species_id}">
                ${item.species_name}
            </option>
        `;
    });
}


async function loadExpeditions() {
    const response = await fetch("/api/expeditions");
    const expeditions = await response.json();

    const container = document.getElementById("expeditions");

    let html = `
        <table>
            <tr>
                <th>ID</th>
                <th>Команда</th>
                <th>Место</th>
                <th>Начало</th>
                <th>Окончание</th>
            </tr>
    `;

    expeditions.forEach(expedition => {
        html += `
            <tr>
                <td>${expedition.expedition_id}</td>
                <td>${expedition.team_name}</td>
                <td>${expedition.place_name}</td>
                <td>${expedition.start_time}</td>
                <td>${expedition.end_time}</td>
            </tr>
        `;
    });

    html += "</table>";

    container.innerHTML = html;


    const select =
        document.getElementById("catch-expedition");

    select.innerHTML =
        '<option value="">Выберите экспедицию</option>';

    expeditions.forEach(expedition => {
        select.innerHTML += `
            <option value="${expedition.expedition_id}">
                Экспедиция №${expedition.expedition_id}
                — ${expedition.team_name}
                — ${expedition.place_name}
            </option>
        `;
    });
}


async function loadCatches() {
    const response = await fetch("/api/catch");
    const catches = await response.json();

    const container = document.getElementById("catches");

    let html = `
        <table>
            <tr>
                <th>ID</th>
                <th>Экспедиция</th>
                <th>Вид</th>
                <th>Количество</th>
            </tr>
    `;

    catches.forEach(item => {
        html += `
            <tr>
                <td>${item.catch_id}</td>
                <td>${item.expedition_id}</td>
                <td>${item.species_name}</td>
                <td>${item.quantity}</td>
            </tr>
        `;
    });

    html += "</table>";

    container.innerHTML = html;
}


// ======================================
// Добавление команды
// ======================================

document
    .getElementById("team-form")
    .addEventListener("submit", async function(event) {

        event.preventDefault();

        const name =
            document.getElementById("team-name").value;

        const response = await fetch("/api/teams", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                team_name: name
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail);
            return;
        }

        document.getElementById("team-name").value = "";

        await loadTeams();
    });


// ======================================
// Добавление места
// ======================================

document
    .getElementById("place-form")
    .addEventListener("submit", async function(event) {

        event.preventDefault();

        const name =
            document.getElementById("place-name").value;

        const response = await fetch("/api/places", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                place_name: name
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail);
            return;
        }

        document.getElementById("place-name").value = "";

        await loadPlaces();
    });


// ======================================
// Добавление вида жука
// ======================================

document
    .getElementById("species-form")
    .addEventListener("submit", async function(event) {

        event.preventDefault();

        const name =
            document.getElementById("species-name").value;

        const response = await fetch("/api/species", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                species_name: name
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail);
            return;
        }

        document.getElementById("species-name").value = "";

        await loadSpecies();
    });


// ======================================
// Добавление экспедиции
// ======================================

document
    .getElementById("expedition-form")
    .addEventListener("submit", async function(event) {

        event.preventDefault();

        const teamId =
            document.getElementById("expedition-team").value;

        const placeId =
            document.getElementById("expedition-place").value;

        const startTime =
            document.getElementById("start-time").value;

        const endTime =
            document.getElementById("end-time").value;


        const response = await fetch("/api/expeditions", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                team_id: Number(teamId),
                place_id: Number(placeId),
                start_time: startTime,
                end_time: endTime
            })
        });


        const data = await response.json();


        if (!response.ok) {
            alert(data.detail);
            return;
        }


        alert("Экспедиция создана");

        document.getElementById("expedition-form").reset();

        await loadExpeditions();
    });


// ======================================
// Добавление улова
// ======================================

document
    .getElementById("catch-form")
    .addEventListener("submit", async function(event) {

        event.preventDefault();


        const expeditionId =
            document.getElementById("catch-expedition").value;

        const speciesId =
            document.getElementById("catch-species").value;

        const quantity =
            document.getElementById("quantity").value;


        const response = await fetch("/api/catch", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                expedition_id: Number(expeditionId),
                species_id: Number(speciesId),
                quantity: Number(quantity)
            })
        });


        const data = await response.json();


        if (!response.ok) {
            alert(data.detail);
            return;
        }


        alert("Улов добавлен");

        document.getElementById("catch-form").reset();

        await loadCatches();
        await loadReport();
    });


// ======================================
// Отчёт
// ======================================

async function loadReport() {

    const response =
        await fetch("/api/catch/report");

    const report =
        await response.json();


    const container =
        document.getElementById("report");


    let html = `
        <table>
            <tr>
                <th>Вид жука</th>
                <th>Количество</th>
            </tr>
    `;


    report.forEach(item => {

        html += `
            <tr>
                <td>${item.species_name}</td>
                <td>${item.total_quantity}</td>
            </tr>
        `;

    });


    html += "</table>";

    container.innerHTML = html;
}


// ======================================
// Первоначальная загрузка
// ======================================

async function loadAll() {

    await loadTeams();

    await loadPlaces();

    await loadSpecies();

    await loadExpeditions();

    await loadCatches();

    await loadReport();
}


// ======================================
// статистики улова за выбранный период
// ======================================
async function loadCatchReport() {
    const dateFrom = document.getElementById("report-date-from").value;
    const dateTo = document.getElementById("report-date-to").value;

    let url = "/api/catch/report";

    const params = new URLSearchParams();

    if (dateFrom) {
        params.append("date_from", dateFrom);
    }

    if (dateTo) {
        params.append("date_to", dateTo);
    }

    if (params.toString()) {
        url += "?" + params.toString();
    }

    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Ошибка получения отчёта");
        }

        const data = await response.json();

        console.log("Отчёт:", data);

        const table = document.getElementById("catch-report-table");
        table.innerHTML = "";

        data.forEach(row => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${row.species_name}</td>
                <td>${row.total_quantity}</td>
            `;

            table.appendChild(tr);
        });

    } catch (error) {
        console.error("Ошибка:", error);
        alert("Не удалось получить отчёт");
    }
}

loadAll();

// ======================================
// Выход из системы
// ======================================

document
    .getElementById("logout-button")
    .addEventListener("click", async function() {

        const response = await fetch("/api/logout", {
            method: "POST"
        });

        if (response.ok) {
            window.location.href = "/auth";
        }

    });