import os
import pickle
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException


app = FastAPI(
    title="Railway AI Delay Prediction System",
    description=(
        "Live railway tracking + weather intelligence + "
        "historical ML delay prediction"
    ),
    version="2.1.1"
)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "railway_delay_model.pkl"
)

ENCODER_PATH = os.path.join(
    MODEL_DIR,
    "categorical_encoder.pkl"
)

TRAIN_ENCODING_PATH = os.path.join(
    MODEL_DIR,
    "train_number_encoding.pkl"
)

GLOBAL_MEAN_PATH = os.path.join(
    MODEL_DIR,
    "global_mean.pkl"
)

TRAIN_METADATA_PATH = os.path.join(
    MODEL_DIR,
    "train_metadata.pkl"
)

LIVE_CONTEXT_PATH = os.path.join(
    MODEL_DIR,
    "live_context.pkl"
)

FEATURE_CONFIG_PATH = os.path.join(
    MODEL_DIR,
    "feature_config.pkl"
)


ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ENV_PATH)

RAILRADAR_API_KEY = os.getenv(
    "RAILRADAR_API_KEY"
)

if not RAILRADAR_API_KEY:
    raise RuntimeError(
        "RAILRADAR_API_KEY not found in .env"
    )


RAILRADAR_BASE_URL = (
    "https://api.railradar.in/v1"
)

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

def load_artifact(path):
    """
    Load joblib/pickle artifact.
    """

    if not os.path.exists(path):
        raise RuntimeError(
            f"Required model file not found: {path}"
        )

    try:
        return joblib.load(path)

    except Exception:

        with open(path, "rb") as f:
            return pickle.load(f)


model = load_artifact(
    MODEL_PATH
)

categorical_encoder = load_artifact(
    ENCODER_PATH
)

train_number_encoding = load_artifact(
    TRAIN_ENCODING_PATH
)

train_metadata = load_artifact(
    TRAIN_METADATA_PATH
)

live_context = load_artifact(
    LIVE_CONTEXT_PATH
)

feature_config = load_artifact(
    FEATURE_CONFIG_PATH
)

NUMERIC_COLS = feature_config.get(
    "numeric_features",
    feature_config.get(
        "numeric_cols",
        []
    )
)

CATEGORICAL_COLS = feature_config.get(
    "categorical_features",
    feature_config.get(
        "categorical_cols",
        []
    )
)

ENCODED_COLS = feature_config.get(
    "encoded_features",
    feature_config.get(
        "encoded_cols",
        []
    )
)

DECISION_THRESHOLD = float(
    feature_config.get(
        "threshold",
        0.18
    )
)


if not ENCODED_COLS:

    try:

        ENCODED_COLS = list(
            categorical_encoder.get_feature_names_out(
                CATEGORICAL_COLS
            )
        )

    except Exception:

        ENCODED_COLS = []



def safe_float(
    value,
    default=0.0
):

    try:

        if value is None:
            return float(default)

        if isinstance(
            value,
            str
        ) and value.strip() == "":

            return float(default)

        return float(value)

    except Exception:

        return float(default)


def safe_int(
    value,
    default=0
):

    try:

        return int(
            float(value)
        )

    except Exception:

        return int(default)


def normalize_train_number(
    train_number
):

    return str(
        train_number
    ).strip()


def get_risk_level(
    probability
):

    if probability >= 0.70:
        return "HIGH"

    if probability >= 0.30:
        return "MEDIUM"

    return "LOW"


def get_prediction(
    probability
):

    if probability >= DECISION_THRESHOLD:
        return "Likely Delayed"

    return "Likely On Time"

def encode_train_number(
    train_number
):

    train_number = normalize_train_number(
        train_number
    )

    value = train_number_encoding.get(
        train_number
    )

    if value is None:

        if train_number.isdigit():

            value = train_number_encoding.get(
                int(train_number)
            )

    if value is None:

        value = feature_config.get(
            "global_mean",
            0.718
        )

    return safe_float(
        value,
        0.718
    )


def get_train_metadata(
    train_number
):

    train_number = normalize_train_number(
        train_number
    )

    metadata = train_metadata.get(
        train_number
    )

    if metadata is not None:
        return metadata

    if train_number.isdigit():

        metadata = train_metadata.get(
            int(train_number)
        )

        if metadata is not None:
            return metadata

    return {}



def get_month_severity(
    month
):

    context = live_context

    possible_maps = [

        context.get(
            "month_severity"
        ),

        context.get(
            "month_severity_score"
        ),

        context.get(
            "season_severity"
        ),

        context.get(
            "month_mapping"
        )
    ]

    for mapping in possible_maps:

        if isinstance(
            mapping,
            dict
        ):

            value = mapping.get(
                month
            )

            if value is None:

                value = mapping.get(
                    str(month)
                )

            if value is not None:

                return safe_float(
                    value,
                    0.5
                )

    # Safe fallback.

    if month in [6, 7, 8, 9]:

        return 0.7

    if month in [12, 1, 2]:

        return 0.6

    return 0.3



def get_headers():

    return {

        "Authorization":
            f"Bearer {RAILRADAR_API_KEY}",

        "Accept":
            "application/json"
    }


def get_live_train(
    train_number
):

    url = (
        f"{RAILRADAR_BASE_URL}"
        f"/trains/{train_number}/live"
    )

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            timeout=20
        )

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=503,
            detail={
                "message":
                    "Unable to connect to RailRadar",

                "error":
                    str(exc)
            }
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=response.status_code,
            detail={
                "message":
                    "RailRadar live API failed",

                "response":
                    response.text
            }
        )

    try:

        result = response.json()

    except ValueError:

        raise HTTPException(
            status_code=502,
            detail={
                "message":
                    "RailRadar returned invalid JSON"
            }
        )

    if not result.get("success"):

        raise HTTPException(
            status_code=404,
            detail=
                "Live train data not available"
        )

    return result.get(
        "data",
        {}
    )

def get_train_route(
    train_number
):

    url = (
        f"{RAILRADAR_BASE_URL}"
        f"/trains/{train_number}/route"
        f"?format=geojson&stops=true"
    )

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            timeout=20
        )

        if response.status_code != 200:
            return {}

        return response.json()

    except (
        requests.RequestException,
        ValueError
    ):

        return {}

def get_weather(
    latitude,
    longitude
):

    if (
        latitude is None
        or longitude is None
    ):

        return None

    params = {

        "latitude":
            latitude,

        "longitude":
            longitude,

        "current":
            (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "rain,"
                "weather_code,"
                "visibility,"
                "wind_speed_10m"
            ),

        "timezone":
            "auto"
    }

    try:

        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        return response.json()

    except (
        requests.RequestException,
        ValueError
    ):

        return None


def stop_code(stop):

    return (
        stop.get("stationCode")
        or stop.get("code")
        or stop.get("station_code")
    )


def stop_name(stop):

    return (
        stop.get("stationName")
        or stop.get("name")
        or stop.get("station_name")
    )


def stop_lat(stop):

    value = (
        stop.get("lat")
        if stop.get("lat") is not None
        else stop.get("latitude")
    )

    return value


def stop_lng(stop):

    value = (
        stop.get("lng")
        if stop.get("lng") is not None
        else stop.get("longitude")
    )

    return value


def stop_sequence(stop):

    return safe_int(
        stop.get(
            "sequence"
        ),
        0
    )


def calculate_current_position(
    stops,
    current_station_code,
    segment_progress
):

    if not stops:

        return (
            None,
            None,
            None
        )

    current_stop = None

    if current_station_code:

        for stop in stops:

            if (
                stop_code(stop)
                == current_station_code
            ):

                current_stop = stop
                break

    if current_stop is None:

        return (
            None,
            None,
            None
        )

    current_lat = stop_lat(
        current_stop
    )

    current_lng = stop_lng(
        current_stop
    )

    sequence = stop_sequence(
        current_stop
    )

    # Find next route point.
    next_stop = None

    sorted_stops = sorted(
        stops,
        key=stop_sequence
    )

    for stop in sorted_stops:

        if (
            stop_sequence(stop)
            > sequence
        ):

            next_stop = stop
            break

    if next_stop is None:

        return (
            current_lat,
            current_lng,
            "station"
        )

    next_lat = stop_lat(
        next_stop
    )

    next_lng = stop_lng(
        next_stop
    )

    if segment_progress is None:

        return (
            current_lat,
            current_lng,
            "station"
        )

    if any(
        value is None
        for value in [
            current_lat,
            current_lng,
            next_lat,
            next_lng
        ]
    ):

        return (
            current_lat,
            current_lng,
            "station"
        )

    progress = max(
        0.0,
        min(
            1.0,
            safe_float(
                segment_progress
            )
        )
    )

    latitude = (
        float(current_lat)
        +
        (
            float(next_lat)
            -
            float(current_lat)
        )
        *
        progress
    )

    longitude = (
        float(current_lng)
        +
        (
            float(next_lng)
            -
            float(current_lng)
        )
        *
        progress
    )

    return (
        latitude,
        longitude,
        "segment_interpolation"
    )


# =========================================================
# SCHEDULED DEPARTURE
# =========================================================

def parse_datetime(value):
    if value is None:
        return None

    try:

        parsed = pd.to_datetime(value,errors="coerce")

        if pd.isna(parsed):
            return None

        return parsed

    except Exception:
        return None


def get_scheduled_departure(stops):
    if not stops:
        return None

    sorted_stops = sorted(stops,key=stop_sequence)

    first_stop = sorted_stops[0]

    possible_fields = [
        "scheduledDeparture",
        "scheduled_departure",
        "departureTime",
        "scheduledDepartureTime",
        "std",
        "departure"
    ]

    for field in possible_fields:

        value = first_stop.get(field)
        parsed = parse_datetime(value)
        if parsed is not None:
            return parsed

    for stop in sorted_stops:

        for field in possible_fields:

            value = stop.get(field)

            parsed = parse_datetime(value)

            if parsed is not None:
                return parsed

    return None


def serialize_route_stop(stop):
    """Preserve schedule and live timing fields from RailRadar."""
    return {
        "sequence": stop.get("sequence"),
        "code": (
            stop.get("stationCode")
            or stop.get("code")
            or stop.get("station_code")
        ),
        "name": (
            stop.get("stationName")
            or stop.get("name")
            or stop.get("station_name")
        ),
        "lat": (
            stop.get("lat")
            if stop.get("lat") is not None
            else stop.get("latitude")
        ),
        "lng": (
            stop.get("lng")
            if stop.get("lng") is not None
            else stop.get("longitude")
        ),
        "scheduled_arrival": (
            stop.get("scheduledArrival")
            or stop.get("scheduled_arrival")
        ),
        "scheduled_departure": (
            stop.get("scheduledDeparture")
            or stop.get("scheduled_departure")
        ),
        "actual_arrival": (
            stop.get("actualArrival")
            or stop.get("actual_arrival")
        ),
        "actual_departure": (
            stop.get("actualDeparture")
            or stop.get("actual_departure")
        ),
        "delay_arrival": (
            stop.get("delayArrival")
            if stop.get("delayArrival") is not None
            else stop.get("delay_arrival")
        ),
        "delay_departure": (
            stop.get("delayDeparture")
            if stop.get("delayDeparture") is not None
            else stop.get("delay_departure")
        )
    }

def build_weather_features(
    weather,
    month
):

    current = {}

    if weather:

        current = weather.get(
            "current",
            {}
        )

    rain = safe_float(
        current.get(
            "rain"
        ),
        0
    )

    visibility = safe_float(
        current.get(
            "visibility"
        ),
        10000
    )

    wind = safe_float(
        current.get(
            "wind_speed_10m"
        ),
        0
    )

    weather_code = safe_int(
        current.get(
            "weather_code"
        ),
        0
    )

    is_monsoon = int(
        month in [6, 7, 8, 9]
    )

    fog_weather = weather_code in [
        45,
        48
    ]

    fog_visibility = (
        visibility < 5000
    )

    is_fog_risk = int(
        fog_weather
        or fog_visibility
    )

    fog_risk_score = max(
        0.0,
        min(
            1.0,
            1.0 - (
                visibility / 10000
            )
        )
    )

    return {

        "is_monsoon_season":
            is_monsoon,

        "is_fog_risk":
            is_fog_risk,

        "fog_risk_score":
            fog_risk_score,

        "zone_fog_index":
            fog_risk_score,

        "weather_rain":
            rain,

        "weather_visibility":
            visibility,

        "weather_wind":
            wind,

        "weather_code":
            weather_code
    }



def build_live_features(
    train_number,
    live_data,
    weather,
    stops
):

    train_number = normalize_train_number(
        train_number
    )

    metadata = get_train_metadata(
        train_number
    )

    scheduled_departure = (
        get_scheduled_departure(
            stops
        )
    )

    if scheduled_departure is None:

        scheduled_departure = pd.Timestamp(
            datetime.now()
        )


    year = int(
        scheduled_departure.year
    )

    month = int(
        scheduled_departure.month
    )

    day_of_week = int(
        scheduled_departure.dayofweek
    )

    departure_hour = int(
        scheduled_departure.hour
    )

    features = {

        "year":
            year,

        "month":
            month,

        "day_of_week":
            day_of_week,

        "departure_hour":
            departure_hour,

        "is_weekend":
            int(
                day_of_week >= 5
            ),

        "is_night_departure":
            int(
                departure_hour < 6
                or departure_hour >= 22
            ),

        "is_peak_hour":
            int(
                departure_hour
                in [
                    7,
                    8,
                    9,
                    17,
                    18,
                    19,
                    20
                ]
            )
    }

    # -----------------------------------------------------
    # Weather
    # -----------------------------------------------------

    weather_features = (
        build_weather_features(
            weather,
            month
        )
    )

    features.update(
        weather_features
    )

    for column in NUMERIC_COLS:

        if column in features:
            continue

        if column in metadata:

            features[column] = (
                metadata[column]
            )

  
    route_distance = None

    if stops:

        distances = []

        for stop in stops:

            distance = stop.get(
                "distance"
            )

            if distance is not None:

                distances.append(
                    safe_float(
                        distance
                    )
                )

        if distances:

            route_distance = max(
                distances
            )

    if route_distance is not None:

        if "distance_km" in NUMERIC_COLS:

            features[
                "distance_km"
            ] = route_distance

    # Number of scheduled stops.

    if "num_scheduled_stops" in NUMERIC_COLS:

        features[
            "num_scheduled_stops"
        ] = len(stops)

   
    if (
        "season_severity_score"
        in NUMERIC_COLS
    ):

        features[
            "season_severity_score"
        ] = get_month_severity(
            month
        )


    for column in NUMERIC_COLS:

        if column not in features:

            if column in metadata:

                features[column] = (
                    metadata[column]
                )

            else:

                features[column] = 0.0

    return (
        features,
        scheduled_departure
    )


def build_categorical_features(
    train_number,
    metadata,
    month
):

    values = []

    for column in CATEGORICAL_COLS:

        value = metadata.get(
            column
        )

        if value is None:

            if column == "season":

                if month in [6, 7, 8, 9]:

                    value = "monsoon"

                elif month in [12, 1, 2]:

                    value = "winter"

                elif month in [3, 4, 5]:

                    value = "summer"

                else:

                    value = "normal"

            else:

                value = "unknown"

        values.append(
            value
        )

    return [
        values
    ]



def predict_live_delay(
    train_number,
    live_data,
    weather,
    stops
):

    features, scheduled_departure = (
        build_live_features(
            train_number,
            live_data,
            weather,
            stops
        )
    )

    metadata = get_train_metadata(
        train_number
    )

    month = int(
        features.get(
            "month",
            datetime.now().month
        )
    )

    numeric_values = []

    for column in NUMERIC_COLS:

        value = features.get(
            column,
            0
        )

        numeric_values.append(
            safe_float(
                value
            )
        )

    train_number_encoded = (
        encode_train_number(
            train_number
        )
    )

    numeric_values.append(
        safe_float(
            train_number_encoded
        )
    )

    numeric_array = np.array(
        [numeric_values],
        dtype=np.float32
    )



    categorical_values = (
        build_categorical_features(
            train_number,
            metadata,
            month
        )
    )

    try:

        # Encoder was trained with column names.
        categorical_df = pd.DataFrame(
            categorical_values,
            columns=CATEGORICAL_COLS
        )

        encoded = (
            categorical_encoder.transform(
                categorical_df
            )
        )

        if hasattr(
            encoded,
            "toarray"
        ):

            encoded = encoded.toarray()

        # Get actual encoder feature names.

        encoder_feature_names = list(
            categorical_encoder.get_feature_names_out(
                CATEGORICAL_COLS
            )
        )

        encoded_df = pd.DataFrame(
            encoded,
            columns=encoder_feature_names
        )

        # Align exactly with saved training order.

        if ENCODED_COLS:

            encoded_df = encoded_df.reindex(
                columns=ENCODED_COLS,
                fill_value=0.0
            )

        categorical_array = (
            encoded_df.to_numpy(
                dtype=np.float32
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Categorical encoding failed",

                "error":
                    str(exc)
            }
        )

 
    X = np.hstack(
        [
            numeric_array,
            categorical_array
        ]
    )


    expected_features = getattr(
        model,
        "n_features_in_",
        None
    )

    if (
        expected_features is not None
        and X.shape[1] != expected_features
    ):

        raise HTTPException(
            status_code=500,
            detail={

                "message":
                    "Feature count mismatch between "
                    "API and trained model",

                "api_features":
                    int(X.shape[1]),

                "model_features":
                    int(expected_features),

                "numeric_features":
                    int(
                        numeric_array.shape[1]
                    ),

                "categorical_features":
                    int(
                        categorical_array.shape[1]
                    )
            }
        )

   
    try:

        probability = float(
            model.predict_proba(
                X
            )[0][1]
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "ML prediction failed",

                "error":
                    str(exc),

                "feature_count":
                    int(X.shape[1])
            }
        )

    prediction = get_prediction(
        probability
    )

    risk = get_risk_level(
        probability
    )

    return {

        "delay_probability":
            round(
                probability * 100,
                2
            ),

        "risk_level":
            risk,

        "prediction":
            prediction,

        "decision_threshold":
            round(
                DECISION_THRESHOLD * 100,
                2
            ),

        "scheduled_departure":
            (
                scheduled_departure.isoformat()
                if scheduled_departure is not None
                else None
            ),

        "features_used":
            features,

        "feature_count":
            int(X.shape[1])
    }


def generate_live_reasons(
    delay_minutes,
    weather,
    probability
):

    reasons = []

    if delay_minutes >= 60:

        reasons.append(
            f"Current train is already "
            f"{int(delay_minutes)} minutes late."
        )

    elif delay_minutes >= 30:

        reasons.append(
            f"Current train delay is "
            f"{int(delay_minutes)} minutes."
        )

    elif delay_minutes >= 15:

        reasons.append(
            f"Train is currently "
            f"{int(delay_minutes)} minutes late."
        )

    if weather:

        current = weather.get(
            "current",
            {}
        )

        rain = safe_float(
            current.get(
                "rain"
            ),
            0
        )

        visibility = safe_float(
            current.get(
                "visibility"
            ),
            99999
        )

        wind = safe_float(
            current.get(
                "wind_speed_10m"
            ),
            0
        )

        weather_code = safe_int(
            current.get(
                "weather_code"
            ),
            0
        )

        if rain > 2:

            reasons.append(
                f"Rain detected: "
                f"{rain:.1f} mm."
            )

        if visibility < 5000:

            reasons.append(
                "Low visibility detected."
            )

        if wind >= 30:

            reasons.append(
                f"High wind speed: "
                f"{wind:.1f} km/h."
            )

        if weather_code in [
            45,
            48
        ]:

            reasons.append(
                "Fog-related weather condition "
                "detected."
            )

        if weather_code in [
            51,
            53,
            55,
            61,
            63,
            65,
            80,
            81,
            82
        ]:

            reasons.append(
                "Rain-related weather condition "
                "detected."
            )

    if not reasons:

        if probability >= DECISION_THRESHOLD:

            reasons.append(
                "Historical route and train "
                "patterns indicate elevated "
                "delay risk."
            )

        else:

            reasons.append(
                "No major live disruption signal "
                "detected."
            )

    return reasons[:4]


@app.get("/")
def home():

    return {

        "project":
            "Railway AI Delay Prediction System",

        "status":
            "running",

        "version":
            "2.1.0",

        "services": [

            "RailRadar live train tracking",

            "RailRadar route and station data",

            "Open-Meteo weather intelligence",

            "Historical railway ML model",

            "Train-specific historical metadata",

            "Live delay risk prediction"
        ],

        "model": {

            "algorithm":
                "HistGradientBoostingClassifier",

            "features":
                getattr(
                    model,
                    "n_features_in_",
                    None
                ),

            "decision_threshold":
                DECISION_THRESHOLD
        }
    }


@app.get("/health")
def health():

    return {

        "api":
            "healthy",

        "model_loaded":
            model is not None,

        "encoder_loaded":
            categorical_encoder is not None,

        "train_metadata_loaded":
            train_metadata is not None,

        "live_context_loaded":
            live_context is not None,

        "model_features":
            getattr(
                model,
                "n_features_in_",
                None
            ),

        "numeric_features":
            len(NUMERIC_COLS),

        "categorical_features":
            len(CATEGORICAL_COLS),

        "encoded_features":
            len(ENCODED_COLS),

        "decision_threshold":
            DECISION_THRESHOLD
    }


@app.get("/track/{train_number}")
def track_train(
    train_number: str
):

    train_number = normalize_train_number(
        train_number
    )

    live_data = get_live_train(
        train_number
    )

    train = live_data.get(
        "train",
        {}
    )


    current_location = (
        live_data.get(
            "currentLocation",
            {}
        )
    )

    current_station_code = (
        current_location.get(
            "stationCode"
        )
        or
        current_location.get(
            "currentStationCode"
        )
    )

    segment_progress = (
        current_location.get(
            "segmentProgress"
        )
    )

    speed = current_location.get(
        "speed"
    )

    bearing = current_location.get(
        "bearing"
    )

    latitude = current_location.get(
        "lat"
    )

    longitude = current_location.get(
        "lng"
    )

    location_source = None

    if (
        latitude is not None
        and longitude is not None
    ):

        location_source = (
            "railradar_live"
        )


    route_data = get_train_route(
        train_number
    )

    route = route_data.get(
        "data",
        {}
    )

    if not isinstance(
        route,
        dict
    ):

        route = {}

    stops = route.get(
        "stops",
        []
    )

    if not isinstance(
        stops,
        list
    ):

        stops = []


    if (
        latitude is None
        or longitude is None
    ):

        (
            latitude,
            longitude,
            location_source
        ) = calculate_current_position(
            stops,
            current_station_code,
            segment_progress
        )

    previous_station = live_data.get(
        "previousHalt"
    )

    next_station = live_data.get(
        "nextHalt"
    )

    weather = get_weather(
        latitude,
        longitude
    )


    ml_result = predict_live_delay(
        train_number,
        live_data,
        weather,
        stops
    )

 
    delay_minutes = safe_float(
        live_data.get(
            "delayMinutes"
        ),
        0
    )

    reasons = generate_live_reasons(
        delay_minutes,
        weather,
        ml_result[
            "delay_probability"
        ] / 100
    )

    geometry_available = False

    if route_data:

        if route_data.get(
            "geometry"
        ):

            geometry_available = True

        elif route.get(
            "geometry"
        ):

            geometry_available = True

        elif route_data.get(
            "data",
            {}
        ).get(
            "geometry"
        ):

            geometry_available = True


    return {

        "train": {

            "number":
                train.get(
                    "number",
                    train_number
                ),

            "name":
                train.get(
                    "name"
                ),

            "status":
                live_data.get(
                    "status"
                ),

            "delay_minutes":
                delay_minutes,

            "is_live":
                live_data.get(
                    "isLive"
                ),

            "tracking_mode":
                live_data.get(
                    "trackingMode"
                ),

            "last_updated":
                live_data.get(
                    "lastUpdatedAt"
                )
        },

        "location": {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "speed_kmph":
                speed,

            "bearing_degrees":
                bearing,

            "current_station_code":
                current_station_code,

            "segment_progress":
                segment_progress,

            "location_source":
                location_source
        },

        "previous_station": {

            "code":
                (
                    previous_station.get(
                        "stationCode"
                    )
                    if isinstance(
                        previous_station,
                        dict
                    )
                    else None
                ),

            "name":
                (
                    previous_station.get(
                        "stationName"
                    )
                    if isinstance(
                        previous_station,
                        dict
                    )
                    else None
                )
        },

        "next_station": {

            "code":
                (
                    next_station.get(
                        "stationCode"
                    )
                    if isinstance(
                        next_station,
                        dict
                    )
                    else None
                ),

            "name":
                (
                    next_station.get(
                        "stationName"
                    )
                    if isinstance(
                        next_station,
                        dict
                    )
                    else None
                )
        },

        "weather":
            weather,

        "prediction": {

            "delay_probability":
                ml_result[
                    "delay_probability"
                ],

            "risk_level":
                ml_result[
                    "risk_level"
                ],

            "prediction":
                ml_result[
                    "prediction"
                ],

            "decision_threshold":
                ml_result[
                    "decision_threshold"
                ],

            "scheduled_departure":
                ml_result[
                    "scheduled_departure"
                ]
        },

        "why_this_prediction":
            reasons,

        "route_available":
            bool(stops),

        "geometry_available":
            geometry_available,

        "route": {

            "total_stops":
                len(stops),

            "stops": [
                serialize_route_stop(stop)
                for stop in stops
            ]
        },

        "model": {

            "name":
                "HistGradientBoostingClassifier",

            "validation_roc_auc":
                0.884872,

            "validation_pr_auc":
                0.951927,

            "recall_at_selected_threshold":
                0.9897,

            "f2_score":
                0.9344,

            "feature_count":
                getattr(
                    model,
                    "n_features_in_",
                    None
                ),

            "note":
                "Prediction combines live train "
                "tracking, weather information, "
                "train-specific historical metadata "
                "and the trained railway delay model."
        }
    }