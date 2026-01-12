from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# =======================
# LOAD CSV FILES
# =======================
crime_df = pd.read_csv("city_crime_rates.csv")
weights_df = pd.read_csv("risk_weights.csv")

crime_df.columns = crime_df.columns.str.strip().str.lower().str.replace(" ", "")
weights_df.columns = weights_df.columns.str.strip().str.lower().str.replace(" ", "")

# =======================
# DETECT CRIME RATE COLUMN
# =======================
crime_rate_col = None
for col in crime_df.columns:
    if "lakh" in col:
        crime_rate_col = col
        break

if crime_rate_col is None:
    raise Exception("Crime rate column not found")

MAX_CRIME_RATE = crime_df[crime_rate_col].max()

# =======================
# PRECAUTIONS
# =======================
PRECAUTIONS = {
    "theft": [
        "Keep valuables out of sight",
        "Avoid crowded places during rush hours",
        "Use secure locks for bags and vehicles"
    ],
    "robbery": [
        "Avoid isolated areas late at night",
        "Be alert while using ATMs",
        "Do not resist if threatened"
    ],
    "assault": [
        "Stay in well-lit public places",
        "Travel with companions when possible",
        "Leave immediately if a situation feels unsafe"
    ],
    "rape": [
        "Share travel details with trusted contacts",
        "Prefer verified transport options",
        "Seek help immediately if feeling unsafe"
    ],
    "murder": [
        "Avoid high-risk areas late at night",
        "Do not engage in violent disputes",
        "Report serious threats to authorities"
    ],
    "cybercrime": [
        "Do not share OTPs or passwords",
        "Verify links before clicking",
        "Use strong unique passwords"
    ]
}

# =======================
# HELPER FUNCTIONS
# =======================
def get_weight(factor, condition):
    row = weights_df[
        (weights_df["factor"] == factor) &
        (weights_df["condition"] == condition)
    ]
    return float(row["weight"].values[0]) if not row.empty else 1.0

def get_risk_level(percent):
    if percent <= 20:
        return "Low"
    elif percent <= 50:
        return "Moderate"
    elif percent <= 80:
        return "High"
    else:
        return "Very High"

# =======================
# API ENDPOINT
# =======================
@app.route("/calculate", methods=["POST"])
def calculate_risk():
    data = request.json

    city = data["city"]
    crime = data["crime"]

    gender = data["gender"].lower()          # male / female / others
    fatal_status = data["fatal_status"]      # fatal / non-fatal
    case_status = data["case_status"]        # pending / closed

    row = crime_df[
        (crime_df["city"].str.lower() == city.lower()) &
        (crime_df["crimetype"].str.lower() == crime.lower())
    ]

    if row.empty:
        return jsonify({"error": "City or crime type not found"}), 404

    base_rate = float(row[crime_rate_col].values[0])
    risk = (base_rate / MAX_CRIME_RATE) * 100

    risk *= get_weight("gender", gender)
    risk *= get_weight("fatal", fatal_status)
    risk *= get_weight("case", case_status)

    risk = round(min(risk, 100), 2)

    return jsonify({
        "city": city,
        "crime": crime,
        "exposure_risk_percent": risk,
        "risk_level": get_risk_level(risk),
        "precautions": PRECAUTIONS.get(crime.lower(), []),
        "The risk shown is an estimate derived from historical crime trends and does not guarantee future events.
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




