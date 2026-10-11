
const API_BASE_URL = "http://127.0.0.1:8000";


let map = null;
let routeLayer = null;
let stationLayer = null;
let trainMarker = null;


const $ = (id) => document.getElementById(id);


const trainInput = $("trainInput");
const trackBtn = $("trackBtn");
const dashboard = $("dashboard");
const errorPanel = $("errorPanel");
const connectionStatus = $("connectionStatus");


function setConnection(state, text) {
  if (!connectionStatus) return;

  connectionStatus.className = `connection ${state}`;

  connectionStatus.innerHTML = `
    <span class="status-dot"></span>
    ${escapeHTML(text)}
  `;
}


function showError(message) {
  if (dashboard) {
    dashboard.classList.add("hidden");
  }

  if (errorPanel) {
    errorPanel.classList.remove("hidden");
  }

  const errorMessage = $("errorMessage");

  if (errorMessage) {
    errorMessage.textContent = message;
  }

  setConnection("error", "BACKEND ERROR");
}

function hideError() {
  if (errorPanel) {
    errorPanel.classList.add("hidden");
  }

  if (dashboard) {
    dashboard.classList.remove("hidden");
  }
}


function safe(value, fallback = "—") {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return fallback;
  }

  return value;
}


function formatNumber(value, digits = 1) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return number.toFixed(digits);
}

function escapeHTML(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function stationName(station) {
  if (!station) {
    return "—";
  }

  return (
    station.name ||
    station.station_name ||
    station.stationName ||
    station.code ||
    station.station_code ||
    station.stationCode ||
    "—"
  );
}

function weatherDescription(code) {
  const weatherCode = Number(code);

  if (!Number.isFinite(weatherCode)) {
    return "Weather data available";
  }

  const descriptions = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail"
  };

  return descriptions[weatherCode] || "Variable weather";
}

function normalizeWeather(weather) {
  if (!weather) {
    return null;
  }

  const current = weather.current || {};

  return {
    temperature:
      current.temperature_2m ??
      weather.temperature ??
      null,

    humidity:
      current.relative_humidity_2m ??
      weather.humidity ??
      null,

    precipitation:
      current.precipitation ??
      weather.precipitation ??
      null,

    rain:
      current.rain ??
      weather.rain ??
      null,

    wind_speed:
      current.wind_speed_10m ??
      weather.wind_speed ??
      null,

    visibility:
      current.visibility ??
      weather.visibility ??
      null,

    weather_code:
      current.weather_code ??
      weather.weather_code ??
      null,

    time:
      current.time ??
      weather.time ??
      null
  };
}

// ------------------------------------------------------------
// COORDINATES
// ------------------------------------------------------------

function extractCoordinates(data) {
  const location =
    data.location ||
    data.currentLocation ||
    {};

  const latitude = Number(
    location.latitude ??
    location.lat ??
    data.latitude ??
    data.lat
  );

  const longitude = Number(
    location.longitude ??
    location.lng ??
    location.lon ??
    data.longitude ??
    data.lng
  );

  return {
    lat: Number.isFinite(latitude)
      ? latitude
      : null,

    lng: Number.isFinite(longitude)
      ? longitude
      : null
  };
}

// ------------------------------------------------------------
// INITIALIZE MAP
// ------------------------------------------------------------

function initMap(lat, lng) {
  if (!window.L) {
    console.error("Leaflet library is not loaded.");
    return;
  }

  if (map) {
    return;
  }

  const mapElement = $("map");

  if (!mapElement) {
    console.error("Map element not found.");
    return;
  }

  map = L.map("map", {
    zoomControl: true,
    preferCanvas: true
  }).setView(
    [lat, lng],
    7
  );

  L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 19,
      attribution:
        "&copy; OpenStreetMap contributors"
    }
  ).addTo(map);
}

// ------------------------------------------------------------
// CLEAR MAP LAYERS
// ------------------------------------------------------------

function clearMapLayers() {
  if (routeLayer && map) {
    map.removeLayer(routeLayer);
  }

  if (stationLayer && map) {
    map.removeLayer(stationLayer);
  }

  if (trainMarker && map) {
    map.removeLayer(trainMarker);
  }

  routeLayer = null;
  stationLayer = null;
  trainMarker = null;
}

// ------------------------------------------------------------
// DRAW ROUTE
// ------------------------------------------------------------

function drawRoute(route, current) {
  if (!map) {
    return;
  }

  clearMapLayers();

  routeLayer = L.layerGroup().addTo(map);
  stationLayer = L.layerGroup().addTo(map);

  const stops = Array.isArray(route?.stops)
    ? route.stops
    : [];

  // ----------------------------------------------------------
  // ROUTE LINE
  // ----------------------------------------------------------

  const coordinates = stops
    .map((stop) => {
      const lat = Number(
        stop.lat ??
        stop.latitude
      );

      const lng = Number(
        stop.lng ??
        stop.lon ??
        stop.longitude
      );

      return [lat, lng];
    })
    .filter(
      ([lat, lng]) =>
        Number.isFinite(lat) &&
        Number.isFinite(lng)
    );

  if (coordinates.length >= 2) {
    L.polyline(
      coordinates,
      {
        color: "#36d9ff",
        weight: 4,
        opacity: 0.72,
        smoothFactor: 1.2
      }
    ).addTo(routeLayer);
  }

  // ----------------------------------------------------------
  // STATION MARKERS
  // ----------------------------------------------------------

  const stride = Math.max(
    1,
    Math.ceil(stops.length / 45)
  );

  stops.forEach(
    (stop, index) => {
      const lat = Number(
        stop.lat ??
        stop.latitude
      );

      const lng = Number(
        stop.lng ??
        stop.lon ??
        stop.longitude
      );

      if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lng)
      ) {
        return;
      }

      if (
        index % stride !== 0 &&
        index !== 0 &&
        index !== stops.length - 1
      ) {
        return;
      }

      const marker =
        L.circleMarker(
          [lat, lng],
          {
            radius: 4,
            color: "#36d9ff",
            weight: 1,
            fillColor: "#36d9ff",
            fillOpacity: 0.8
          }
        );

      const name = safe(
        stop.name ??
        stop.stationName ??
        stop.station_name,
        "Station"
      );

      const code = safe(
        stop.code ??
        stop.stationCode ??
        stop.station_code,
        ""
      );

      marker.bindTooltip(
        `${escapeHTML(name)}${
          code !== ""
            ? ` (${escapeHTML(code)})`
            : ""
        }`,
        {
          direction: "top",
          opacity: 0.9
        }
      );

      marker.addTo(stationLayer);
    }
  );

  // ----------------------------------------------------------
  // LIVE TRAIN MARKER
  // ----------------------------------------------------------

  const latitude = Number(
    current?.lat
  );

  const longitude = Number(
    current?.lng
  );

  if (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude)
  ) {
    const trainNumber =
      safe(
        $("trainNumber")?.textContent,
        ""
      );

    const trainName =
      safe(
        $("trainName")?.textContent,
        ""
      );

    const trainIcon = L.divIcon({
      className:
        "train-live-icon",

      html: `
        <div style="
          width:30px;
          height:30px;
          border-radius:50%;
          display:grid;
          place-items:center;
          background:#ff526b;
          color:white;
          border:3px solid #fff;
          box-shadow:
            0 0 0 7px rgba(255,82,107,.18),
            0 0 28px rgba(255,82,107,.55);
          font-size:15px;
        ">🚆</div>
      `,

      iconSize: [30, 30],

      iconAnchor: [15, 15]
    });

    trainMarker =
      L.marker(
        [
          latitude,
          longitude
        ],
        {
          icon: trainIcon
        }
      )
        .bindPopup(`
          <b>Current Train Position</b><br>
          ${escapeHTML(trainNumber)}
          —
          ${escapeHTML(trainName)}
        `)
        .addTo(map);

    // --------------------------------------------------------
    // MAP VIEW
    // --------------------------------------------------------

    if (coordinates.length >= 2) {
      map.fitBounds(
        L.latLngBounds(coordinates),
        {
          padding: [30, 30]
        }
      );
    } else {
      map.setView(
        [
          latitude,
          longitude
        ],
        9
      );
    }
  }
}

// ------------------------------------------------------------
// RENDER WEATHER
// ------------------------------------------------------------

function renderWeather(weatherResponse) {
  const weather =
    normalizeWeather(
      weatherResponse
    );

  if (!weather) {
    return;
  }

  const temperature = $("temperature");
  const humidity = $("humidity");
  const rain = $("rain");
  const wind = $("wind");
  const visibility = $("visibility");
  const condition = $("weatherCondition");

  // ----------------------------------------------------------
  // TEMPERATURE
  // ----------------------------------------------------------

  if (temperature) {
    temperature.textContent =
      weather.temperature !== null
        ? `${formatNumber(
            weather.temperature,
            1
          )}°C`
        : "—";
  }

  // ----------------------------------------------------------
  // HUMIDITY
  // ----------------------------------------------------------

  if (humidity) {
    humidity.textContent =
      weather.humidity !== null
        ? `${formatNumber(
            weather.humidity,
            0
          )}%`
        : "—";
  }

  // ----------------------------------------------------------
  // RAIN
  // ----------------------------------------------------------

  const precipitation =
    Number(
      weather.precipitation ??
      weather.rain ??
      0
    );

  if (rain) {
    rain.textContent =
      precipitation > 0
        ? `${formatNumber(
            precipitation,
            1
          )} mm`
        : "No Rain";
  }

  // ----------------------------------------------------------
  // WIND
  // ----------------------------------------------------------

  if (wind) {
    wind.textContent =
      weather.wind_speed !== null
        ? `${formatNumber(
            weather.wind_speed,
            1
          )} km/h`
        : "—";
  }

  // ----------------------------------------------------------
  // VISIBILITY
  // ----------------------------------------------------------

  if (visibility) {
    const visibilityKm =
      weather.visibility !== null
        ? Number(
            weather.visibility
          ) / 1000
        : null;

    visibility.textContent =
      Number.isFinite(
        visibilityKm
      )
        ? `${visibilityKm.toFixed(1)} km`
        : "—";
  }

  // ----------------------------------------------------------
  // CONDITION
  // ----------------------------------------------------------

  if (condition) {
    if (
      weather.weather_code !== null
    ) {
      condition.textContent =
        weatherDescription(
          weather.weather_code
        );
    } else if (
      precipitation > 0
    ) {
      condition.textContent =
        "Rain / precipitation";
    } else {
      condition.textContent =
        "Clear / dry";
    }
  }
}

// ------------------------------------------------------------
// RENDER REASONS
// ------------------------------------------------------------

function renderReasons(
  suppliedReasons,
  delayMinutes,
  probability
) {
  const container =
    $("reasons");

  if (!container) {
    return;
  }

  container.innerHTML = "";

  const reasons = [];

  // ----------------------------------------------------------
  // CURRENT DELAY
  // ----------------------------------------------------------

  const delay =
    Number(delayMinutes);

  if (
    Number.isFinite(delay) &&
    delay > 0
  ) {
    reasons.push(
      `Train is already ${Math.round(
        delay
      )} minutes late.`
    );
  }

  // ----------------------------------------------------------
  // BACKEND REASONS
  // ----------------------------------------------------------

  if (
    Array.isArray(
      suppliedReasons
    )
  ) {
    suppliedReasons.forEach(
      (reason) => {
        if (
          reason !== null &&
          reason !== undefined &&
          String(reason).trim()
        ) {
          reasons.push(
            String(reason)
          );
        }
      }
    );
  }

  // ----------------------------------------------------------
  // FALLBACK
  // ----------------------------------------------------------

  if (!reasons.length) {
    if (
      Number(probability) >= 70
    ) {
      reasons.push(
        "AI model indicates elevated delay risk."
      );
    } else {
      reasons.push(
        "No major live disruption signal detected."
      );
    }
  }

  // ----------------------------------------------------------
  // REMOVE DUPLICATES
  // ----------------------------------------------------------

  const uniqueReasons = [
    ...new Set(reasons)
  ];

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  uniqueReasons
    .slice(0, 4)
    .forEach((reason) => {
      const item =
        document.createElement(
          "div"
        );

      item.className =
        "reason";

      item.innerHTML = `
        <span class="reason-icon">⚠</span>
        <span>${escapeHTML(
          reason
        )}</span>
      `;

      container.appendChild(
        item
      );
    });
}

// ------------------------------------------------------------
// RENDER AI PREDICTION
// ------------------------------------------------------------

function renderPrediction(
  prediction,
  delayMinutes,
  reasons
) {
  const probabilityRaw =
    Number(
      prediction?.delay_probability ??
      prediction?.probability ??
      0
    );

  const probability =
    Number.isFinite(
      probabilityRaw
    )
      ? probabilityRaw
      : 0;

  const clamped =
    Math.max(
      0,
      Math.min(
        100,
        probability
      )
    );

  // ----------------------------------------------------------
  // PROBABILITY NUMBER
  // ----------------------------------------------------------

  const probabilityElement =
    $("probability");

  if (probabilityElement) {
    probabilityElement.textContent =
      `${clamped.toFixed(2)}%`;
  }

  // ----------------------------------------------------------
  // PROBABILITY RING
  // ----------------------------------------------------------

  const probabilityRing =
    $("probabilityRing");

  if (probabilityRing) {
    const degrees =
      clamped * 3.6;

    probabilityRing.style.background =
      `
      conic-gradient(
        var(--red) 0deg,
        var(--red) ${degrees}deg,
        rgba(255,255,255,.06)
        ${degrees}deg
      )
      `;
  }

  // ----------------------------------------------------------
  // PREDICTION HEADLINE
  // ----------------------------------------------------------

  const predictionHeadline =
    $("predictionHeadline");

  if (predictionHeadline) {
    predictionHeadline.textContent =
      safe(
        prediction?.prediction,
        clamped >= 50
          ? "Likely Delayed"
          : "Likely On Time"
      );
  }

  // ----------------------------------------------------------
  // PREDICTION SUBTEXT
  // ----------------------------------------------------------

  const predictionSubtext =
    $("predictionSubtext");

  if (predictionSubtext) {
    predictionSubtext.textContent =
      "AI risk is calculated from the live train state, route context, weather and historical patterns.";
  }

  // ----------------------------------------------------------
  // RISK LEVEL
  // ----------------------------------------------------------

  const risk =
    String(
      prediction?.risk_level ??
      ""
    ).toUpperCase();

  const riskLevel =
    $("riskLevel");

  if (riskLevel) {
    riskLevel.textContent =
      safe(
        prediction?.risk_level,
        "UNKNOWN"
      );
  }

  // ----------------------------------------------------------
  // PREDICTION TEXT
  // ----------------------------------------------------------

  const predictionText =
    $("predictionText");

  if (predictionText) {
    predictionText.textContent =
      safe(
        prediction?.prediction,
        "—"
      );
  }

  // ----------------------------------------------------------
  // RISK BADGE
  // ----------------------------------------------------------

  const riskBadge =
    $("riskBadge");

  if (riskBadge) {
    riskBadge.className =
      "risk-badge";

    if (risk === "LOW") {
      riskBadge.style.borderColor =
        "rgba(50,229,154,.25)";

      riskBadge.style.background =
        "rgba(50,229,154,.08)";

      if (riskLevel) {
        riskLevel.style.color =
          "var(--green)";
      }
    }

    else if (
      risk === "MEDIUM"
    ) {
      riskBadge.style.borderColor =
        "rgba(255,191,90,.25)";

      riskBadge.style.background =
        "rgba(255,191,90,.08)";

      if (riskLevel) {
        riskLevel.style.color =
          "var(--amber)";
      }
    }

    else if (
      risk === "HIGH"
    ) {
      riskBadge.classList.add(
        "high"
      );

      if (riskLevel) {
        riskLevel.style.color =
          "var(--red)";
      }
    }

    else {
      if (riskLevel) {
        riskLevel.style.color =
          "var(--red)";
      }
    }
  }

  // ----------------------------------------------------------
  // REASONS
  // ----------------------------------------------------------

  renderReasons(
    reasons,
    delayMinutes,
    clamped
  );
}

// ------------------------------------------------------------
// RENDER TRAIN DATA
// ------------------------------------------------------------

function renderTrainData(data) {
  const train =
    data.train || {};

  const location =
    data.location || {};

  const prediction =
    data.prediction || {};

  const route =
    data.route || {};

  // ----------------------------------------------------------
  // TRAIN NUMBER
  // ----------------------------------------------------------

  const trainNumber =
    safe(
      train.number ??
      train.train_number ??
      train.trainNumber ??
      data.train_number,
      "—"
    );

  if ($("trainNumber")) {
    $("trainNumber").textContent =
      trainNumber;
  }

  // ----------------------------------------------------------
  // TRAIN NAME
  // ----------------------------------------------------------

  const trainName =
    safe(
      train.name ??
      train.train_name ??
      train.trainName ??
      data.train_name,
      "—"
    );

  if ($("trainName")) {
    $("trainName").textContent =
      trainName;
  }

  // ----------------------------------------------------------
  // TRAIN DELAY
  // ----------------------------------------------------------

  const delay =
    Number(
      train.delay_minutes ??
      train.delayMinutes ??
      data.delay_minutes
    );

  const delayValue =
    Number.isFinite(delay)
      ? Math.round(delay)
      : null;

  if ($("delayMinutes")) {
    $("delayMinutes").textContent =
      delayValue !== null
        ? `${delayValue} min`
        : "—";
  }

  // ----------------------------------------------------------
  // EXTRA DELAY BOX SUPPORT
  // ----------------------------------------------------------

  if ($("delayValue")) {
    $("delayValue").textContent =
      delayValue !== null
        ? `${delayValue} min`
        : "—";
  }

  // ----------------------------------------------------------
  // TRAIN STATUS
  // ----------------------------------------------------------

  const status =
    safe(
      train.status,
      "UNKNOWN"
    );

  const statusElement =
    $("trainStatus");

  if (statusElement) {
    statusElement.textContent =
      String(status)
        .replace(
          /_/g,
          " "
        )
        .toUpperCase();
  }

  // ----------------------------------------------------------
  // PREVIOUS STATION
  // ----------------------------------------------------------

  const previous =
    data.previous_station ??
    data.previousHalt ??
    null;

  const previousText =
    stationName(previous);

  if ($("previousStation")) {
    $("previousStation").textContent =
      previousText;
  }

  if ($("previousStationCard")) {
    $("previousStationCard").textContent =
      previousText;
  }

  // Extra ID support
  if ($("previousStop")) {
    $("previousStop").textContent =
      previousText;
  }

  // ----------------------------------------------------------
  // NEXT STATION
  // ----------------------------------------------------------

  const next =
    data.next_station ??
    data.nextHalt ??
    null;

  const nextText =
    stationName(next);

  if ($("nextStation")) {
    $("nextStation").textContent =
      nextText;
  }

  if ($("nextStationCard")) {
    $("nextStationCard").textContent =
      nextText;
  }

  // Extra ID support
  if ($("nextStop")) {
    $("nextStop").textContent =
      nextText;
  }

  // ----------------------------------------------------------
  // CURRENT STATION
  // ----------------------------------------------------------

  const currentStation =
    safe(
      location.current_station_code,
      "Live segment"
    );

  if ($("currentLocation")) {
    $("currentLocation").textContent =
      currentStation;
  }

  // ----------------------------------------------------------
  // TRACKING MODE
  // ----------------------------------------------------------

  const trackingMode =
    safe(
      train.tracking_mode ??
      train.trackingMode,
      "Real-time"
    );

  if ($("trackingMode")) {
    $("trackingMode").textContent =
      String(
        trackingMode
      ).replace(
        /_/g,
        " "
      );
  }

  // ----------------------------------------------------------
  // AI PREDICTION
  // ----------------------------------------------------------

  renderPrediction(
    prediction,
    delayValue ?? 0,
    data.why_this_prediction
  );

  // ----------------------------------------------------------
  // RISK VALUE
  // ----------------------------------------------------------

  const riskValue =
    safe(
      prediction.risk_level,
      "—"
    );

  if ($("riskValue")) {
    $("riskValue").textContent =
      riskValue;
  }

  if ($("risk")) {
    $("risk").textContent =
      riskValue;
  }

  // ----------------------------------------------------------
  // WEATHER
  // ----------------------------------------------------------

  renderWeather(
    data.weather
  );

  // ----------------------------------------------------------
  // COORDINATES
  // ----------------------------------------------------------

  const coords =
    extractCoordinates(
      data
    );

  if ($("coordinates")) {
    if (
      coords.lat !== null &&
      coords.lng !== null
    ) {
      $("coordinates").textContent =
        `Coordinates: ${coords.lat.toFixed(
          5
        )}, ${coords.lng.toFixed(
          5
        )}`;
    } else {
      $("coordinates").textContent =
        "Coordinates: —";
    }
  }

  // ----------------------------------------------------------
  // LAST UPDATED
  // ----------------------------------------------------------

  const lastUpdated =
    train.last_updated ??
    train.lastUpdatedAt ??
    data.last_updated ??
    data.lastUpdatedAt;

  if ($("lastUpdated")) {
    $("lastUpdated").textContent =
      `Last updated: ${safe(
        lastUpdated
      )}`;
  }

  // ----------------------------------------------------------
  // ROUTE SUMMARY
  // ----------------------------------------------------------

  if ($("routeSummary")) {
    if (
      route.total_stops !==
      undefined &&
      route.total_stops !==
      null
    ) {
      $("routeSummary").textContent =
        `${route.total_stops} route stops • Live train position`;
    } else {
      $("routeSummary").textContent =
        "Live railway route • Current train position";
    }
  }

  // ----------------------------------------------------------
  // MAP
  // ----------------------------------------------------------

  if (
    coords.lat !== null &&
    coords.lng !== null
  ) {
    initMap(
      coords.lat,
      coords.lng
    );

    setTimeout(
      () => {
        drawRoute(
          route,
          {
            lat: coords.lat,
            lng: coords.lng
          }
        );
      },
      100
    );
  }

  // ----------------------------------------------------------
  // SPEED
  // ----------------------------------------------------------

  const speed =
    location.speed_kmph;

  const speedElement =
    $("speed");

  if (speedElement) {
    speedElement.textContent =
      speed !== null &&
      speed !== undefined
        ? `${formatNumber(
            speed,
            1
          )} km/h`
        : "—";
  }

  // ----------------------------------------------------------
  // BEARING
  // ----------------------------------------------------------

  const bearing =
    location.bearing_degrees;

  const bearingElement =
    $("bearing");

  if (bearingElement) {
    bearingElement.textContent =
      bearing !== null &&
      bearing !== undefined
        ? `${formatNumber(
            bearing,
            0
          )}°`
        : "—";
  }

  // ----------------------------------------------------------
  // SEGMENT PROGRESS
  // ----------------------------------------------------------

  const progress =
    Number(
      location.segment_progress
    );

  const progressElement =
    $("segmentProgress");

  if (
    progressElement &&
    Number.isFinite(progress)
  ) {
    progressElement.textContent =
      `${Math.round(
        progress * 100
      )}%`;
  }
}

// ------------------------------------------------------------
// ERROR MESSAGE EXTRACTION
// ------------------------------------------------------------

function getBackendError(
  data,
  status
) {
  if (!data) {
    return `Backend returned HTTP ${status}`;
  }

  if (
    typeof data.detail ===
    "string"
  ) {
    return data.detail;
  }

  if (
    data.detail &&
    typeof data.detail ===
    "object"
  ) {
    if (data.detail.message) {
      return data.detail.message;
    }

    if (data.detail.error) {
      return data.detail.error;
    }

    return JSON.stringify(
      data.detail
    );
  }

  if (data.message) {
    return data.message;
  }

  return `Backend returned HTTP ${status}`;
}

// ------------------------------------------------------------
// TRACK TRAIN
// ------------------------------------------------------------

async function trackTrain() {
  if (!trainInput) {
    console.error(
      "trainInput element not found."
    );
    return;
  }

  const trainNumber =
    trainInput.value.trim();

  if (!trainNumber) {
    showError(
      "Please enter a train number."
    );
    return;
  }

  // ----------------------------------------------------------
  // LOADING STATE
  // ----------------------------------------------------------

  setConnection(
    "loading",
    "FETCHING LIVE INTELLIGENCE..."
  );

  if (trackBtn) {
    trackBtn.disabled = true;
    trackBtn.textContent =
      "LOADING...";
  }

  try {
    const response =
      await fetch(
        `${API_BASE_URL}/track/${encodeURIComponent(
          trainNumber
        )}`,
        {
          method: "GET",

          headers: {
            Accept:
              "application/json"
          }
        }
      );

    let data = null;

    try {
      data =
        await response.json();
    } catch {
      throw new Error(
        "Backend returned invalid JSON."
      );
    }

    if (!response.ok) {
      throw new Error(
        getBackendError(
          data,
          response.status
        )
      );
    }

    // --------------------------------------------------------
    // RENDER
    // --------------------------------------------------------

    hideError();

    renderTrainData(
      data
    );

    setConnection(
      "ready",
      "LIVE DATA CONNECTED"
    );

  } catch (error) {
    console.error(
      "RailGuard API Error:",
      error
    );

    showError(
      `${error.message}. Make sure FastAPI is running at ${API_BASE_URL} and CORS is enabled.`
    );
  } finally {
    if (trackBtn) {
      trackBtn.disabled = false;
      trackBtn.textContent =
        "TRACK TRAIN";
    }
  }
}

// ------------------------------------------------------------
// BUTTON CLICK
// ------------------------------------------------------------

if (trackBtn) {
  trackBtn.addEventListener(
    "click",
    trackTrain
  );
}

// ------------------------------------------------------------
// ENTER KEY
// ------------------------------------------------------------

if (trainInput) {
  trainInput.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Enter"
      ) {
        trackTrain();
      }
    }
  );
}

// ------------------------------------------------------------
// PAGE LOAD
// ------------------------------------------------------------

// IMPORTANT:
// No train is automatically loaded.
// User must enter a train number manually.
window.addEventListener(
  "load",
  () => {
    if (trainInput) {
      trainInput.value = "";
      trainInput.focus();
    }
  }
);