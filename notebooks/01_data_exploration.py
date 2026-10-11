# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt

# data = pd.read_csv("D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/data/raw/ir_train - Copy.csv")

# df = data.drop(columns=["journey_id","primary_delay_cause","delay_minutes","zone_abbr","is_overloaded"])


# # categorical_cols = df.select_dtypes(include="object").columns

# # for col in categorical_cols:
# #     print(f"\n{col}:")
# #     print(df[col].nunique())
# #     print(df[col].unique())

# # print(df["is_delayed"].value_counts())
# # print(df["is_delayed"].value_counts(normalize=True) * 100)

# # print(df["train_number"].nunique())
# # print(df["train_number"].value_counts().head(10))

# # categorical_cols = [
# #     "train_type",
# #     "season",
# #     "zone",
# #     "source_station_category",
# #     "destination_station_category",
# #     "traction_type"
# # ]

# # for col in categorical_cols:
# #     print("\n==========", col, "==========")
# #     print(
# #          df.groupby(col)["is_delayed"]
# #         .agg(["count", "mean"])
# #         .sort_values("mean", ascending=False)
# #     )

# # corr = df.select_dtypes(include="number").corr()["is_delayed"]
# # corr = corr.drop("is_delayed").sort_values()

# # print(corr)

# # data_dict = pd.read_csv("D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/data/raw/ir_data_dictionary - Copy.csv")

# # print(data_dict)

# # print(df[[
# #     "route_historical_ontime_pct",
# #     "late_incoming_rake",
# #     "is_delayed"
# # ]].head(20))

# # print(df[[
# #     "departure_date",
# #     "year",
# #     "route_historical_ontime_pct",
# #     "late_incoming_rake",
# #     "is_delayed"
# # ]].sort_values("departure_date").head(20))


# # year_analysis = (
# #     df.groupby("year")
# #     .agg(
# #         avg_historical_ontime=("route_historical_ontime_pct", "mean"),
# #         delay_rate=("is_delayed", "mean"),
# #         avg_late_rake=("late_incoming_rake", "mean"),
# #         total_trains=("is_delayed", "count")
# #     )
# # )

# # print(year_analysis)


# #                       test data

# test_df = pd.read_csv("railway_delay_prediction/data/raw/ir_test - Copy.csv")

# test_model_df = test_df.drop(columns=[
#     "journey_id",
#     "zone_abbr",
#     "is_overloaded"
# ])




# # print("Train shape:", df.shape)
# # print("Test shape:", test_df.shape)

# # print("\nTrain columns:", len(df.columns))
# # print("Test columns:", len(test_df.columns))

# # print("\nTrain delay-related feature means:")
# # print(df.select_dtypes(include="number").mean().head(10))

# # train_cols = set(df.columns)
# # test_cols = set(test_model_df.columns)

# # print("Test me extra columns:")
# # print(test_cols - train_cols)

# # print("\nTrain me jo test me nahi hain:")
# # print(train_cols - test_cols)






# # print("NUMERICAL COLUMNS:")
# # print(df.select_dtypes(include="number").columns.tolist())

# # print("\nCATEGORICAL COLUMNS:")
# # print(df.select_dtypes(include="object").columns.tolist())

# # categorical_cols = [
# #     "train_number",
# #     "train_type",
# #     "season",
# #     "zone",
# #     "source_station_category",
# #     "destination_station_category",
# #     "traction_type"
# # ]

# # for col in categorical_cols:
# #     print(f"\n{col}")
# #     print("Unique values:", df[col].nunique())
# #     print(df[col].unique()[:20])

# # departure_date को datetime में convert करें
# df["departure_date"] = pd.to_datetime(df["departure_date"])

# # Date के हिसाब से sort करें
# model_df = df.sort_values("departure_date").reset_index(drop=True)

# # 80% - 20% split
# split_index = int(len(model_df) * 0.80)

# train_data = df.iloc[:split_index].copy()
# valid_data = df.iloc[split_index:].copy()

# # print("Training data:", train_data.shape)
# # print("Validation data:", valid_data.shape)

# # print("\nTraining date:")
# # print(train_data["departure_date"].min(), "to", train_data["departure_date"].max())

# # print("\nValidation date:")
# # print(valid_data["departure_date"].min(), "to", valid_data["departure_date"].max())

# # print("\nTraining delay rate:")
# # print(train_data["is_delayed"].mean())

# # print("\nValidation delay rate:")
# # print(valid_data["is_delayed"].mean())


# train_data = train_data.drop(columns=["departure_date"])
# valid_data = valid_data.drop(columns=["departure_date"])

# # print("Train shape:", train_data.shape)
# # print("Validation shape:", valid_data.shape)


# from sklearn.preprocessing import OneHotEncoder

# categorical_cols = [
#     "train_type",
#     "season",
#     "zone",
#     "source_station_category",
#     "destination_station_category",
#     "traction_type"
# ]

# encoder = OneHotEncoder(
#     handle_unknown="ignore",
#     sparse_output=True
# )

# encoder.fit(train_data[categorical_cols])

# # print("Encoding completed.")
# # print("Number of encoded features:", len(encoder.get_feature_names_out()))


# train_number_stats = (
#     train_data
#     .groupby("train_number")["is_delayed"]
#     .agg(["mean", "count"])
# )

# global_mean = train_data["is_delayed"].mean()

# # print("Global delay rate:", global_mean)

# alpha = 20

# train_number_stats["train_number_encoded"] = (
#     (train_number_stats["count"] * train_number_stats["mean"] + alpha * global_mean)
#     / (train_number_stats["count"] + alpha)
# )

# # print(train_number_stats.head())


# # train_number encoding map
# train_number_encoding = train_number_stats["train_number_encoded"]

# # Training data में encoding apply करें
# train_data["train_number_encoded"] = (
#     train_data["train_number"]
#     .map(train_number_encoding)
#     .fillna(global_mean)
# )

# # Validation data में वही training mapping apply करें
# valid_data["train_number_encoded"] = (
#     valid_data["train_number"]
#     .map(train_number_encoding)
#     .fillna(global_mean)
# )

# # Original train_number हटाएं
# train_data = train_data.drop(columns=["train_number"])
# valid_data = valid_data.drop(columns=["train_number"])

# # print("Train shape:", train_data.shape)
# # print("Validation shape:", valid_data.shape)

# # print("\nEncoded train_number sample:")
# # print(train_data["train_number_encoded"].head())

# # print("train_number" in train_data.columns)
# # print("train_number_encoded" in train_data.columns)

# # print("\nTrain columns:")
# # print(train_data.columns.tolist())


# # print("Train shape:", train_data.shape)
# # print("Validation shape:", valid_data.shape)


# # Training data encode
# train_encoded = encoder.transform(train_data[categorical_cols])

# # Validation data encode
# valid_encoded = encoder.transform(valid_data[categorical_cols])

# # print("Train encoded shape:", train_encoded.shape)
# # print("Validation encoded shape:", valid_encoded.shape)


# encoded_feature_names = encoder.get_feature_names_out(categorical_cols)

# train_encoded_df = pd.DataFrame(
#     train_encoded.toarray(),
#     columns=encoded_feature_names,
#     index=train_data.index
# )

# valid_encoded_df = pd.DataFrame(
#     valid_encoded.toarray(),
#     columns=encoded_feature_names,
#     index=valid_data.index
# )

# # print("Train encoded DataFrame:", train_encoded_df.shape)
# # print("Validation encoded DataFrame:", valid_encoded_df.shape)

# numerical_cols = train_data.select_dtypes(include="number").columns.tolist()

# numerical_cols.remove("is_delayed")

# # print("Number of numerical features:", len(numerical_cols))
# # print(numerical_cols)

# train_numeric = train_data[numerical_cols]
# valid_numeric = valid_data[numerical_cols]

# X_train = pd.concat(
#     [train_numeric, train_encoded_df],
#     axis=1
# )

# X_valid = pd.concat(
#     [valid_numeric, valid_encoded_df],
#     axis=1
# )

# y_train = train_data["is_delayed"]
# y_valid = valid_data["is_delayed"]

# # print("X_train shape:", X_train.shape)
# # print("X_valid shape:", X_valid.shape)

# # print("y_train shape:", y_train.shape)
# # print("y_valid shape:", y_valid.shape)



#                                     # model traning

# from sklearn.ensemble import HistGradientBoostingClassifier
# from sklearn.metrics import roc_auc_score

# model = HistGradientBoostingClassifier(
#     max_iter=300,
#     learning_rate=0.08,
#     max_leaf_nodes=31,
#     random_state=42
# )

# model.fit(X_train, y_train)

# # Probability prediction
# y_valid_proba = model.predict_proba(X_valid)[:, 1]

# # ROC-AUC
# auc = roc_auc_score(y_valid, y_valid_proba)

# # print("Validation ROC-AUC:", auc)







# from sklearn.inspection import permutation_importance

# # X_valid_sample = X_valid.iloc[:50000]
# # y_valid_sample = y_valid.iloc[:50000]

# # perm = permutation_importance(
# #     model,
# #     X_valid_sample,
# #     y_valid_sample,
# #     scoring="roc_auc",
# #     n_repeats=3,
# #     random_state=42,
# #     n_jobs=-1
# # )

# # feature_importance = (
# #     pd.DataFrame({
# #         "feature": X_train.columns,
# #         "importance": perm.importances_mean
# #     })
# #     .sort_values("importance", ascending=False)
# # )

# # print(feature_importance.head(20))


# # print(
# #     train_data.groupby("late_incoming_rake")["is_delayed"]
# #     .agg(["count", "mean"])
# # )

# from sklearn.metrics import average_precision_score

# # pr_auc = average_precision_score(y_valid, y_valid_proba)

# # # print("Validation ROC-AUC:", auc)
# # # print("Validation PR-AUC:", pr_auc)

# # print(train_data[[
# #     "late_incoming_rake",
# #     "route_historical_ontime_pct"
# # ]].describe())

# # print(
# #     train_data.groupby("late_incoming_rake")["is_delayed"]
# #     .agg(["count", "mean"])
# # )

# # valid_result = pd.DataFrame({
# #     "actual": y_valid.values,
# #     "predicted_probability": y_valid_proba
# # })

# # valid_result["probability_bucket"] = pd.cut(
# #     valid_result["predicted_probability"],
# #     bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
# #     include_lowest=True
# # )

# # print(
# #     valid_result.groupby("probability_bucket", observed=True)["actual"]
# #     .agg(["count", "mean"])
# # )


# test_model_df["train_number_encoded"] = (
#     test_model_df["train_number"]
#     .map(train_number_encoding)
#     .fillna(global_mean)
# )

# test_encoded = encoder.transform(
#     test_model_df[categorical_cols]
# )

# test_encoded_df = pd.DataFrame(
#     test_encoded.toarray(),
#     columns=encoded_feature_names,
#     index=test_model_df.index
# )





# test_model_df = test_model_df.drop(
#     columns=["departure_date", "train_number"]
# )

# test_numeric = test_model_df[numerical_cols]

# X_test = pd.concat(
#     [test_numeric, test_encoded_df],
#     axis=1
# )





# test_proba = model.predict_proba(X_test)[:, 1]

# # print("Test predictions:", len(test_proba))
# # print(test_proba[:10])


# # print("Min probability:", test_proba.min())
# # print("Max probability:", test_proba.max())
# # print("Mean probability:", test_proba.mean())


# from sklearn.metrics import (
#     accuracy_score,
#     precision_score,
#     recall_score,
#     f1_score,
#     fbeta_score,
#     confusion_matrix
# )

# # 0.3 threshold
# # y_valid_pred = (y_valid_proba >= 0.3).astype(int)

# # print("Accuracy :", accuracy_score(y_valid, y_valid_pred))
# # print("Precision:", precision_score(y_valid, y_valid_pred))
# # print("Recall   :", recall_score(y_valid, y_valid_pred))
# # print("F1 Score :", f1_score(y_valid, y_valid_pred))
# # print("F2 Score :", fbeta_score(y_valid, y_valid_pred, beta=2))

# # print("\nConfusion Matrix:")
# # print(confusion_matrix(y_valid, y_valid_pred))


# import joblib
# import os

# # model_path = "D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/model"

# # os.makedirs(model_path, exist_ok=True)

# # # Model
# # joblib.dump(model, f"{model_path}/railway_delay_model.pkl")

# # # One-Hot Encoder
# # joblib.dump(encoder, f"{model_path}/categorical_encoder.pkl")

# # # Train number target encoding
# # joblib.dump(train_number_encoding, f"{model_path}/train_number_encoding.pkl")

# # # Global mean
# # joblib.dump(global_mean, f"{model_path}/global_mean.pkl")

# # # Feature configuration
# # feature_config = {
# #     "categorical_cols": categorical_cols,
# #     "numerical_cols": numerical_cols,
# #     "encoded_feature_names": encoded_feature_names,
# #     "threshold": 0.30
# # }

# # joblib.dump(feature_config, f"{model_path}/feature_config.pkl")

# # print("Final model pipeline saved successfully.")



# import joblib

# model = joblib.load(
#     "D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/model/railway_delay_model.pkl"
# )

# encoder = joblib.load(
#     "D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/model/categorical_encoder.pkl"
# )

# train_number_encoding = joblib.load(
#     "D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/model/train_number_encoding.pkl"
# )

# global_mean = joblib.load(
#     "D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/model/global_mean.pkl"
# )

# feature_config = joblib.load(
#     "D:/programing files/python/projects/SIH - project 2026/railway_delay_prediction/model/feature_config.pkl"
# )

# # print("Model loaded successfully.")
# # print("Threshold:", feature_config["threshold"])
# # print("Features:", len(feature_config["numerical_cols"]) + len(feature_config["encoded_feature_names"]))

# print(test_df.iloc[0].to_dict())




















import os
import warnings
import joblib
import numpy as np
import pandas as pd

from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    confusion_matrix,
)

warnings.filterwarnings("ignore")

BASE_DIR = (
    "D:/programing files/python/projects/"
    "SIH - project 2026/railway_delay_prediction"
)

TRAIN_FILE = os.path.join(
    BASE_DIR,
    "data/raw/ir_train - Copy.csv"
)

TEST_FILE = os.path.join(
    BASE_DIR,
    "data/raw/ir_test - Copy.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)

os.makedirs(MODEL_DIR, exist_ok=True)


TARGET = "is_delayed"
TRAIN_NUMBER = "train_number"



TIME_FEATURES = [
    "year",
    "month",
    "day_of_week",
    "departure_hour",
    "is_weekend",
    "is_night_departure",
    "is_peak_hour",
]



# LIVE / DERIVABLE WEATHER FEATURES


WEATHER_FEATURES = [
    "is_monsoon_season",
    "is_fog_risk",
    "fog_risk_score",
    "season_severity_score",
]


# TRAIN / ROUTE FEATURES


ROUTE_FEATURES = [
    "distance_km",
    "num_scheduled_stops",
    "scheduled_travel_hours",
    "track_doubled",
    "is_hdn_route",
    "is_electrified",
    "psr_count",
    "is_circular_route",
]



ROLLING_STOCK_FEATURES = [
    "loco_age_years",
    "coach_age_years",
    "has_lhb_coaches",
    "is_rake_shared",
    "maintenance_score",
]



HISTORICAL_FEATURES = [
    "zone_congestion_index",
    "zone_fog_index",
    "route_historical_ontime_pct",
]


CATEGORICAL_FEATURES = [
    "train_type",
    "season",
    "zone",
    "source_station_category",
    "destination_station_category",
    "traction_type",
]


NUMERIC_FEATURES = (
    TIME_FEATURES
    + WEATHER_FEATURES
    + ROUTE_FEATURES
    + ROLLING_STOCK_FEATURES
    + HISTORICAL_FEATURES
)

REQUIRED_COLUMNS = (
    [TRAIN_NUMBER, TARGET, "departure_date"]
    + NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

print("\n================================================")
print(" RAILWAY AI DELAY MODEL")
print("================================================\n")

if not os.path.exists(TRAIN_FILE):
    raise FileNotFoundError(
        f"Training CSV not found:\n{TRAIN_FILE}"
    )

if not os.path.exists(TEST_FILE):
    raise FileNotFoundError(
        f"Test CSV not found:\n{TEST_FILE}"
    )

print("Reading training dataset...")
print("This may take some time because the dataset is large.\n")

train_df = pd.read_csv(
    TRAIN_FILE,
    usecols=REQUIRED_COLUMNS,
    low_memory=False
)

print("Training rows:", len(train_df))
print("Training columns:", len(train_df.columns))


print("\nCleaning training data...")

train_df[TRAIN_NUMBER] = (
    train_df[TRAIN_NUMBER]
    .astype(str)
    .str.strip()
)

train_df[TARGET] = pd.to_numeric(
    train_df[TARGET],
    errors="coerce"
)

train_df["departure_date"] = pd.to_datetime(
    train_df["departure_date"],
    errors="coerce"
)

train_df = train_df.dropna(
    subset=[
        TARGET,
        TRAIN_NUMBER,
        "departure_date"
    ]
)

train_df[TARGET] = train_df[TARGET].astype(int)


# ============================================================
# 8. SORT CHRONOLOGICALLY
#
# IMPORTANT:
# This fixes the bug in your old code.
# ============================================================

train_df = (
    train_df
    .sort_values("departure_date")
    .reset_index(drop=True)
)


# ============================================================
# 9. CHRONOLOGICAL 80/20 SPLIT
# ============================================================

split_index = int(
    len(train_df) * 0.80
)

model_train = train_df.iloc[
    :split_index
].copy()

model_valid = train_df.iloc[
    split_index:
].copy()


print("\n================================================")
print(" CHRONOLOGICAL SPLIT")
print("================================================")

print(
    "Training:",
    model_train.shape
)

print(
    "Validation:",
    model_valid.shape
)

print(
    "\nTraining period:",
    model_train["departure_date"].min(),
    "to",
    model_train["departure_date"].max()
)

print(
    "Validation period:",
    model_valid["departure_date"].min(),
    "to",
    model_valid["departure_date"].max()
)

print(
    "\nTraining delay rate:",
    round(
        model_train[TARGET].mean() * 100,
        3
    ),
    "%"
)

print(
    "Validation delay rate:",
    round(
        model_valid[TARGET].mean() * 100,
        3
    ),
    "%"
)


# ============================================================
# 10. TRAIN-NUMBER TARGET ENCODING
#
# FIT ONLY ON TRAINING DATA
# ============================================================

print("\nCreating train-number historical encoding...")

global_mean = float(
    model_train[TARGET].mean()
)

train_number_stats = (
    model_train
    .groupby(TRAIN_NUMBER)[TARGET]
    .agg(["mean", "count"])
)

ALPHA = 20

train_number_stats[
    "train_number_encoded"
] = (
    (
        train_number_stats["mean"]
        * train_number_stats["count"]
    )
    +
    (
        ALPHA
        * global_mean
    )
) / (
    train_number_stats["count"]
    + ALPHA
)

train_number_encoding = (
    train_number_stats[
        "train_number_encoded"
    ]
    .to_dict()
)

model_train[
    "train_number_encoded"
] = (
    model_train[TRAIN_NUMBER]
    .map(train_number_encoding)
    .fillna(global_mean)
)

model_valid[
    "train_number_encoded"
] = (
    model_valid[TRAIN_NUMBER]
    .map(train_number_encoding)
    .fillna(global_mean)
)


# ============================================================
# 11. CREATE TRAIN-SPECIFIC METADATA
#
# This is extremely important for LIVE prediction.
#
# For example:
#
# distance
# track doubled
# electrification
# loco age
# coach age
# zone
# traction
# route punctuality
#
# are historically learned for each train number.
# ============================================================

print("\nCreating train-specific historical metadata...")

metadata_numeric = (
    ROUTE_FEATURES
    + ROLLING_STOCK_FEATURES
    + HISTORICAL_FEATURES
)

train_metadata_numeric = (
    model_train
    .groupby(TRAIN_NUMBER)[metadata_numeric]
    .median()
)


# ============================================================
# 12. TRAIN-SPECIFIC CATEGORICAL METADATA
# ============================================================

def get_mode(series):

    values = (
        series
        .dropna()
        .astype(str)
    )

    if len(values) == 0:
        return "UNKNOWN"

    mode = values.mode()

    if len(mode) == 0:
        return "UNKNOWN"

    return mode.iloc[0]


train_metadata_categorical = (
    model_train
    .groupby(TRAIN_NUMBER)[CATEGORICAL_FEATURES]
    .agg(get_mode)
)


# ============================================================
# 13. COMBINE TRAIN METADATA
# ============================================================

train_metadata = (
    train_metadata_numeric
    .join(train_metadata_categorical)
)


# ============================================================
# 14. MONTH-BASED HISTORICAL WEATHER / SEASON INFORMATION
#
# Used for live feature generation.
# ============================================================

month_severity = (
    model_train
    .groupby("month")[
        "season_severity_score"
    ]
    .mean()
    .to_dict()
)

month_festival = (
    model_train
    .groupby("month")[
        "is_festival_season"
    ]
    .mean()
    .to_dict()
    if "is_festival_season" in model_train.columns
    else {}
)


# ============================================================
# 15. NUMERIC FILL VALUES
# ============================================================

numeric_fill_values = {}

for col in NUMERIC_FEATURES:

    if col in model_train.columns:

        value = model_train[col].median()

        if pd.isna(value):
            value = 0

        numeric_fill_values[col] = float(
            value
        )


# ============================================================
# 16. CLEAN CATEGORICAL DATA
# ============================================================

for col in CATEGORICAL_FEATURES:

    model_train[col] = (
        model_train[col]
        .astype(str)
        .replace("nan", "UNKNOWN")
    )

    model_valid[col] = (
        model_valid[col]
        .astype(str)
        .replace("nan", "UNKNOWN")
    )


# ============================================================
# 17. ONE-HOT ENCODER
# ============================================================

print("\nEncoding categorical features...")

try:

    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

except TypeError:

    # compatibility with older scikit-learn
    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse=False
    )


encoder.fit(
    model_train[CATEGORICAL_FEATURES]
)


train_cat = encoder.transform(
    model_train[CATEGORICAL_FEATURES]
)

valid_cat = encoder.transform(
    model_valid[CATEGORICAL_FEATURES]
)


encoded_feature_names = (
    encoder
    .get_feature_names_out(
        CATEGORICAL_FEATURES
    )
)


# ============================================================
# 18. NUMERIC MATRICES
# ============================================================

train_numeric = (
    model_train[
        NUMERIC_FEATURES
        + ["train_number_encoded"]
    ]
    .copy()
)

valid_numeric = (
    model_valid[
        NUMERIC_FEATURES
        + ["train_number_encoded"]
    ]
    .copy()
)


for col in NUMERIC_FEATURES:

    fill_value = (
        numeric_fill_values[col]
    )

    train_numeric[col] = (
        pd.to_numeric(
            train_numeric[col],
            errors="coerce"
        )
        .fillna(fill_value)
    )

    valid_numeric[col] = (
        pd.to_numeric(
            valid_numeric[col],
            errors="coerce"
        )
        .fillna(fill_value)
    )


# ============================================================
# 19. FINAL MATRICES
# ============================================================

X_train = np.hstack(
    [
        train_numeric.to_numpy(
            dtype=np.float32
        ),
        train_cat.astype(
            np.float32
        ),
    ]
)

X_valid = np.hstack(
    [
        valid_numeric.to_numpy(
            dtype=np.float32
        ),
        valid_cat.astype(
            np.float32
        ),
    ]
)

y_train = model_train[
    TARGET
].to_numpy()

y_valid = model_valid[
    TARGET
].to_numpy()


print("\nFinal feature matrix:")
print(
    "X_train:",
    X_train.shape
)

print(
    "X_valid:",
    X_valid.shape
)


# ============================================================
# 20. TRAIN MODEL
# ============================================================

print("\n================================================")
print(" TRAINING HIST GRADIENT BOOSTING")
print("================================================\n")

model = HistGradientBoostingClassifier(
    max_iter=350,
    learning_rate=0.06,
    max_leaf_nodes=31,
    min_samples_leaf=30,
    l2_regularization=0.5,
    random_state=42
)

model.fit(
    X_train,
    y_train
)

print("Training completed.")


# ============================================================
# 21. VALIDATION PROBABILITY
# ============================================================

y_valid_proba = (
    model
    .predict_proba(X_valid)[:, 1]
)


# ============================================================
# 22. ROC-AUC
# ============================================================

roc_auc = roc_auc_score(
    y_valid,
    y_valid_proba
)

pr_auc = average_precision_score(
    y_valid,
    y_valid_proba
)


# ============================================================
# 23. AUTOMATIC THRESHOLD SEARCH
#
# F2 gives more importance to recall.
# ============================================================

best_threshold = 0.30
best_f2 = -1

for threshold in np.arange(
    0.10,
    0.91,
    0.01
):

    prediction = (
        y_valid_proba >= threshold
    ).astype(int)

    score = fbeta_score(
        y_valid,
        prediction,
        beta=2,
        zero_division=0
    )

    if score > best_f2:

        best_f2 = score
        best_threshold = float(
            threshold
        )


# ============================================================
# 24. FINAL METRICS
# ============================================================

y_valid_pred = (
    y_valid_proba
    >= best_threshold
).astype(int)


accuracy = accuracy_score(
    y_valid,
    y_valid_pred
)

precision = precision_score(
    y_valid,
    y_valid_pred,
    zero_division=0
)

recall = recall_score(
    y_valid,
    y_valid_pred,
    zero_division=0
)

f1 = f1_score(
    y_valid,
    y_valid_pred,
    zero_division=0
)

f2 = fbeta_score(
    y_valid,
    y_valid_pred,
    beta=2,
    zero_division=0
)

cm = confusion_matrix(
    y_valid,
    y_valid_pred
)


# ============================================================
# 25. PRINT RESULTS
# ============================================================

print("\n================================================")
print(" FINAL VALIDATION RESULTS")
print("================================================")

print(
    f"\nROC-AUC : {roc_auc:.6f}"
)

print(
    f"PR-AUC  : {pr_auc:.6f}"
)

print(
    f"\nBest Threshold: {best_threshold:.2f}"
)

print(
    f"Accuracy : {accuracy:.4f}"
)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall   : {recall:.4f}"
)

print(
    f"F1       : {f1:.4f}"
)

print(
    f"F2       : {f2:.4f}"
)

print(
    "\nConfusion Matrix:"
)

print(cm)


# ============================================================
# 26. SAVE MODEL
# ============================================================

print("\n================================================")
print(" SAVING MODEL")
print("================================================")


joblib.dump(
    model,
    os.path.join(
        MODEL_DIR,
        "railway_delay_model.pkl"
    )
)


joblib.dump(
    encoder,
    os.path.join(
        MODEL_DIR,
        "categorical_encoder.pkl"
    )
)


joblib.dump(
    train_number_encoding,
    os.path.join(
        MODEL_DIR,
        "train_number_encoding.pkl"
    )
)


joblib.dump(
    global_mean,
    os.path.join(
        MODEL_DIR,
        "global_mean.pkl"
    )
)


# ============================================================
# 27. SAVE TRAIN METADATA
# ============================================================

train_metadata_dict = (
    train_metadata
    .to_dict(
        orient="index"
    )
)


joblib.dump(
    train_metadata_dict,
    os.path.join(
        MODEL_DIR,
        "train_metadata.pkl"
    )
)


# ============================================================
# 28. SAVE MONTH METADATA
# ============================================================

live_context = {

    "month_severity":
        month_severity,

    "month_festival":
        month_festival,

    "numeric_fill_values":
        numeric_fill_values,

    "global_mean":
        global_mean,

    "threshold":
        best_threshold,

    "train_metadata":
        train_metadata_dict,
}


joblib.dump(
    live_context,
    os.path.join(
        MODEL_DIR,
        "live_context.pkl"
    )
)


# ============================================================
# 29. FEATURE CONFIG
# ============================================================

feature_config = {

    "numeric_features":
        NUMERIC_FEATURES,

    "categorical_features":
        CATEGORICAL_FEATURES,

    "encoded_feature_names":
        encoded_feature_names.tolist(),

    "threshold":
        best_threshold,

    "global_mean":
        global_mean,

    "roc_auc":
        float(roc_auc),

    "pr_auc":
        float(pr_auc),

    "precision":
        float(precision),

    "recall":
        float(recall),

    "f1":
        float(f1),

    "f2":
        float(f2),

    "total_features":
        int(X_train.shape[1]),

    "excluded_features": [
        "journey_id",
        "primary_delay_cause",
        "delay_minutes",
        "zone_abbr",
        "is_overloaded",
        "late_incoming_rake",
        "seat_utilisation_pct",
        "is_special_train",
    ],

    "model_type":
        "HistGradientBoostingClassifier",

    "training_split":
        "chronological_80_20",

    "live_compatible":
        True,
}


joblib.dump(
    feature_config,
    os.path.join(
        MODEL_DIR,
        "feature_config.pkl"
    )
)


# ============================================================
# 30. TEST DATA
# ============================================================

print("\n================================================")
print(" PROCESSING TEST DATA")
print("================================================")

test_df = pd.read_csv(
    TEST_FILE,
    usecols=[
        c
        for c in REQUIRED_COLUMNS
        if c != TARGET
    ],
    low_memory=False
)

print(
    "Test rows:",
    len(test_df)
)


# ============================================================
# 31. TEST CLEANING
# ============================================================

test_df[TRAIN_NUMBER] = (
    test_df[TRAIN_NUMBER]
    .astype(str)
    .str.strip()
)

test_df["departure_date"] = (
    pd.to_datetime(
        test_df["departure_date"],
        errors="coerce"
    )
)


# ============================================================
# 32. TEST TRAIN NUMBER ENCODING
# ============================================================

test_df[
    "train_number_encoded"
] = (
    test_df[TRAIN_NUMBER]
    .map(train_number_encoding)
    .fillna(global_mean)
)


# ============================================================
# 33. TEST CATEGORICAL
# ============================================================

for col in CATEGORICAL_FEATURES:

    test_df[col] = (
        test_df[col]
        .astype(str)
        .replace(
            "nan",
            "UNKNOWN"
        )
    )


test_cat = encoder.transform(
    test_df[CATEGORICAL_FEATURES]
)


# ============================================================
# 34. TEST NUMERIC
# ============================================================

test_numeric = (
    test_df[
        NUMERIC_FEATURES
        + ["train_number_encoded"]
    ]
    .copy()
)


for col in NUMERIC_FEATURES:

    test_numeric[col] = (
        pd.to_numeric(
            test_numeric[col],
            errors="coerce"
        )
        .fillna(
            numeric_fill_values[col]
        )
    )


X_test = np.hstack(
    [
        test_numeric.to_numpy(
            dtype=np.float32
        ),
        test_cat.astype(
            np.float32
        ),
    ]
)


# ============================================================
# 35. TEST PREDICTIONS
# ============================================================

print("\nGenerating test probabilities...")

test_probability = (
    model
    .predict_proba(X_test)[:, 1]
)


# ============================================================
# 36. KAGGLE-STYLE TEST OUTPUT
# ============================================================

submission = pd.DataFrame({
    "is_delayed": test_probability
})

submission_path = os.path.join(
    MODEL_DIR,
    "railway_delay_test_predictions.csv"
)

submission.to_csv(
    submission_path,
    index=False
)

submission_path = os.path.join(
    MODEL_DIR,
    "railway_delay_test_predictions.csv"
)


submission.to_csv(
    submission_path,
    index=False
)


# ============================================================
# 37. FINAL SUMMARY
# ============================================================

print("\n================================================")
print(" EVERYTHING SAVED")
print("================================================")

print(
    "\nModel:",
    os.path.join(
        MODEL_DIR,
        "railway_delay_model.pkl"
    )
)

print(
    "Encoder:",
    os.path.join(
        MODEL_DIR,
        "categorical_encoder.pkl"
    )
)

print(
    "Train encoding:",
    os.path.join(
        MODEL_DIR,
        "train_number_encoding.pkl"
    )
)

print(
    "Train metadata:",
    os.path.join(
        MODEL_DIR,
        "train_metadata.pkl"
    )
)

print(
    "Live context:",
    os.path.join(
        MODEL_DIR,
        "live_context.pkl"
    )
)

print(
    "Feature config:",
    os.path.join(
        MODEL_DIR,
        "feature_config.pkl"
    )
)

print(
    "Test predictions:",
    submission_path
)

print("\n================================================")
print(" MODEL BUILD COMPLETE")
print("================================================")