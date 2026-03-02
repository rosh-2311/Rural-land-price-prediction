import pandas as pd
import joblib

# Load trained model & encoder
model = joblib.load("model/land_price_model.pkl")
le = joblib.load("model/district_encoder.pkl")

# -----------------------------
# New land input (example)
# -----------------------------
input_data = {
    "District": "Madurai",
    "Year": 2027,
    "Zn_%": 0.85,
    "Fe_%": 1.20,
    "Cu_%": 0.45,
    "Mn_%": 0.90,
    "B_%": 0.30,
    "S_%": 0.75
}

# Convert to DataFrame
df_input = pd.DataFrame([input_data])

# Encode District
df_input["District"] = le.transform(df_input["District"])

# Predict price
predicted_price = model.predict(df_input)[0]

print(f"\n💰 Predicted Land Price per Acre: ₹{predicted_price:,.2f}")
