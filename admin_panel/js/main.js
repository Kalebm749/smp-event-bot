const CALENDAR_FILE = "/events/events_calendar/event_calendar.json";
const EVENTS_DIR = "/events/events_json/";
const LOG_FILE = "/logs/event_logs.txt"; // single log
const LOGS_DIR = "/logs/";
const POLL_INTERVAL = 5000;

let selectedEventFile = null;
let selectedLogFile = null;

// --- COLLAPSIBLE ---
document.querySelectorAll('section h2').forEach(h => {
  h.onclick = () => {
    const content = h.nextElementSibling;
    content.style.display = (content.style.display === "none") ? "block" : "none";
    h.textContent = h.textContent.endsWith("▼") ?
      h.textContent.replace("▼","▲") : h.textContent.replace("▲","▼");
  };
});

// --- CALENDAR ---
async function loadCalendar() {
  try {
    const res = await fetch(CALENDAR_FILE);
    const data = await res.json();
    const tbody = document.getElementById("calendar-body");
    tbody.innerHTML = "";

    const now = new Date();

    data.forEach(e => {
      const tr = document.createElement("tr");
      const start = new Date(e.start);
      const end = new Date(e.end);

      let status = "";
      let rowClass = "";
      if (now < start) { status = "Future"; rowClass = "future"; }
      else if (now >= start && now <= end) { status = "Happening Now"; rowClass = "inprogress"; }
      else { status = "Over"; rowClass = "over"; }

      tr.className = rowClass;
      tr.innerHTML = `<td>${e.name}</td><td>${start.toLocaleString()}</td><td>${end.toLocaleString()}</td><td>${status}</td>`;
      tbody.appendChild(tr);
    });
  } catch(e) {
    console.error("Failed to load calendar", e);
  }
}
setInterval(loadCalendar, POLL_INTERVAL);
loadCalendar();

// --- EVENT JSON FILES ---
async function loadEventFiles() {
  try {
    const res = await fetch(EVENTS_DIR);
    const text = await res.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(text,"text/html");
    const links = Array.from(doc.querySelectorAll("a"))
      .map(a => a.getAttribute("href"))
      .filter(href => href.endsWith(".json"));

    const list = document.getElementById("event-list");
    list.innerHTML = "";
    links.forEach(file => {
      const li = document.createElement("li");
      li.textContent = file;
      li.onclick = () => {
        selectedEventFile = file;
        loadEvent(file);
      };
      list.appendChild(li);
    });

  } catch(e) {
    console.error("Failed to load event files", e);
  }
}

async function loadEvent(file) {
  try {
    const res = await fetch(EVENTS_DIR + file);
    const data = await res.json();
    document.getElementById("event-details").textContent = JSON.stringify(data, null, 2);
  } catch(e) {
    document.getElementById("event-details").textContent = "Failed to load event";
  }
}
setInterval(()=>{ if(selectedEventFile) loadEvent(selectedEventFile); }, POLL_INTERVAL);
loadEventFiles();

// --- LOGS ---
async function loadLogs() {
  try {
    const logList = document.getElementById("log-list");
    logList.innerHTML = "";
    const li = document.createElement("li");
    li.textContent = LOG_FILE.split("/").pop();
    li.onclick = () => { selectedLogFile = LOG_FILE; loadLog(LOG_FILE); };
    logList.appendChild(li);
  } catch(e) {
    console.error("Failed to load logs", e);
  }
}

async function loadLog(file) {
  try {
    const res = await fetch(file);
    const text = await res.text();
    document.getElementById("log-data").textContent = text;
  } catch(e) {
    document.getElementById("log-data").textContent = "Failed to load log";
  }
}
setInterval(()=>{ if(selectedLogFile) loadLog(selectedLogFile); }, POLL_INTERVAL);
loadLogs();

// --- EVENT WINNERS ---
async function loadWinners() {
  try {
    const res = await fetch(LOGS_DIR);
    const text = await res.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(text,"text/html");
    const files = Array.from(doc.querySelectorAll("a"))
      .map(a => a.getAttribute("href"))
      .filter(f => f.endsWith(".json") && f !== "event_logs.txt");

    const tbody = document.getElementById("winners-body");
    tbody.innerHTML = "";

    for (const file of files) {
      try {
        const r = await fetch(LOGS_DIR + file);
        const data = await r.json();
        const leaders = data.Leaders.join(", ");
        tbody.innerHTML += `<tr>
          <td>${data.Event}</td>
          <td>${data.Date}</td>
          <td>${leaders}</td>
          <td>${data.FinalScore}</td>
        </tr>`;
      } catch(e) { console.error("Failed to load winner file", file, e); }
    }
  } catch(e) {
    console.error("Failed to list winner files", e);
  }
}
setInterval(loadWinners, POLL_INTERVAL);
loadWinners();

