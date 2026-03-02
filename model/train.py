import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
import os
import matplotlib.pyplot as plt

# -----------------------------
# 1. Load dataset
# -----------------------------
DATA_PATH = r"C:\Users\ROSHINI\Downloads\Project files\LandPriceML\data\agricultural_land_price_past_2021_2025.csv.csv"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"File not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# -----------------------------
# 4. Data Cleaning & Processing
# -----------------------------

print("\nChecking missing values:")
print(df.isnull().sum())

# Fill missing numeric values with column mean
numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

# Fill missing categorical values (if any)
if "District" in df.columns:
    df["District"] = df["District"].fillna(df["District"].mode()[0])

print("\nMissing values handled successfully")

# Ensure correct data types
df[numeric_cols] = df[numeric_cols].astype(float)

print("\nData types after processing:")
print(df.dtypes)


print("\nColumns in dataset:")
print(df.columns)

# -----------------------------
# 2. Identify target column
# -----------------------------
# Automatically pick the LAST numeric column as target
numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns

if len(numeric_cols) == 0:
    raise ValueError("No numeric column found for prediction")

target_col = numeric_cols[-1]
print(f"\nTarget column selected: {target_col}")

# -----------------------------
# 3. Encode District (if exists)
# -----------------------------
if "District" in df.columns:
    le = LabelEncoder()
    df["District"] = le.fit_transform(df["District"])
    joblib.dump(le, "district_encoder.pkl")
else:
    print("⚠️ 'District' column not found — skipping encoding")

# -----------------------------
# 4. Split features & target
# -----------------------------
X = df.drop(columns=[target_col])
y = df[target_col]

# -----------------------------
# 5. Train-test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# 6. Train XGBoost model
# -----------------------------
model = XGBRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=5,
    random_state=42
)

model.fit(X_train, y_train)

# -----------------------------
# 7. Evaluation
# -----------------------------
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\nModel Performance:")
print(f"MAE : {mae:.2f}")
print(f"R²  : {r2:.4f}")

# -----------------------------
# 8. Save model
# -----------------------------
joblib.dump(model, "land_price_model.pkl")

print("\n✅ Model trained and saved successfully")
print(df.describe())
plt.barh(X.columns, model.feature_importances_)
plt.title("Feature Importance")
plt.show()
print("Train R²:", model.score(X_train, y_train))
print("Test R² :", model.score(X_test, y_test))
