import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# 1. LOAD DATASET
# ============================================================

DATASET_PATH = "dataset/High_Accuracy_Sport_Injury_Dataset.xlsx"

print("Loading dataset...")

df = pd.read_excel(DATASET_PATH)

print("Dataset loaded successfully!")
print("Dataset shape:", df.shape)


# ============================================================
# 2. PREPARE INPUTS AND TARGET
# ============================================================

X = df.drop(columns=["Injury_Risk"])
y = df["Injury_Risk"]

print("\nInjury Risk Distribution:")
print(y.value_counts())


# ============================================================
# 3. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining data:", X_train.shape)
print("Testing data:", X_test.shape)


# ============================================================
# 4. CREATE RANDOM FOREST
# ============================================================

base_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced"
)


# ============================================================
# 5. CALIBRATE AND TRAIN MODEL
# ============================================================

model = CalibratedClassifierCV(
    estimator=base_model,
    method="sigmoid",
    cv=5
)

print("\nTraining calibrated Random Forest...")

model.fit(X_train, y_train)

print("Training completed successfully!")


# ============================================================
# 6. EVALUATE MODEL
# ============================================================

y_pred = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n========================================")
print("MODEL PERFORMANCE")
print("========================================")

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred
    )
)


# ============================================================
# 7. FEATURE IMPORTANCE
# ============================================================

feature_importances = []

for calibrated_classifier in model.calibrated_classifiers_:

    rf_model = calibrated_classifier.estimator

    feature_importances.append(
        rf_model.feature_importances_
    )


average_importance = (
    sum(feature_importances)
    / len(feature_importances)
)


importance_df = pd.DataFrame({
    "Feature": X.columns,
    "Importance": average_importance
}).sort_values(
    "Importance",
    ascending=False
)


print("\n========================================")
print("FEATURE IMPORTANCE")
print("========================================")

print(
    importance_df.to_string(
        index=False
    )
)


# ============================================================
# 8. SAVE TRAINED MODEL
# ============================================================

MODEL_PATH = "models/random_forest_injury_model.pkl"

os.makedirs(
    "models",
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_PATH
)

print("\nModel saved successfully!")
print("Saved to:", MODEL_PATH)


# ============================================================
# 9. HYBRID 3-STAGE ASSESSMENT LAYER
# ============================================================

def hybrid_risk_level(row, ml_probability):
    """
    Hybrid 3-stage injury risk assessment.

    Random Forest probability is the MAIN signal.
    Warning factors can only influence borderline cases.

    Final levels:
        Low
        Medium
        High
    """

    probability = ml_probability * 100
    warning_points = 0

    # Previous injury - strongest warning factor
    if row["Injury_History"] >= 1:
        warning_points += 2

    # High training intensity
    if row["Training_Intensity"] >= 7:
        warning_points += 1

    # Insufficient sleep
    if row["Sleep_Hours"] < 7:
        warning_points += 1

    # Short recovery
    if row["Recovery_Time"] < 52:
        warning_points += 1

    # High stress
    if row["Stress_Level"] >= 8:
        warning_points += 1

    # Higher muscle asymmetry
    if row["Muscle_Asymmetry"] >= 7:
        warning_points += 1


    # ========================================================
    # FINAL DECISION
    # ========================================================

    # HIGH:
    # Very strong ML evidence
    if probability >= 70:
        return "High"

    # HIGH:
    # Moderately high ML probability + several warnings
    if probability >= 50 and warning_points >= 2:
        return "High"

    # MEDIUM:
    # ML model itself is in the middle
    if probability >= 30:
        return "Medium"

    # MEDIUM:
    # Borderline-low ML probability + strong warning combination
    if probability >= 15 and warning_points >= 4:
        return "Medium"

    # LOW:
    # ML probability is strongly low
    return "Low"

# ============================================================
# 10. TEST HYBRID SYSTEM ON ALL 600 RECORDS
# ============================================================

all_probabilities = model.predict_proba(X)[:, 1]

hybrid_results = []


for position, (_, row) in enumerate(df.iterrows()):

    probability = all_probabilities[position]

    final_level = hybrid_risk_level(
        row,
        probability
    )

    hybrid_results.append({
        "Original_Injury_Risk": int(
            row["Injury_Risk"]
        ),
        "ML_Probability": round(
            probability * 100,
            2
        ),
        "Final_Level": final_level
    })


hybrid_df = pd.DataFrame(
    hybrid_results
)


# ============================================================
# 11. DISPLAY HYBRID DISTRIBUTION
# ============================================================

print("\n========================================")
print("HYBRID 3-STAGE ASSESSMENT")
print("========================================")


distribution = hybrid_df[
    "Final_Level"
].value_counts()


for level in [
    "Low",
    "Medium",
    "High"
]:

    count = distribution.get(
        level,
        0
    )

    percentage = (
        count / len(hybrid_df)
    ) * 100

    print(
        f"{level}: "
        f"{count} athletes "
        f"({percentage:.2f}%)"
    )


# ============================================================
# 12. COMPARE AGAINST ORIGINAL DATASET
# ============================================================

print("\n========================================")
print("ORIGINAL TARGET VS FINAL LEVEL")
print("========================================")


comparison = pd.crosstab(
    hybrid_df["Original_Injury_Risk"],
    hybrid_df["Final_Level"]
)

print(comparison)


# ============================================================
# 13. SHOW MEDIUM EXAMPLES
# ============================================================

print("\n========================================")
print("EXAMPLE MEDIUM ASSESSMENTS")
print("========================================")


medium_examples = hybrid_df[
    hybrid_df["Final_Level"] == "Medium"
].head(10)


if medium_examples.empty:

    print("No Medium assessments produced.")

else:

    print(
        medium_examples.to_string(
            index=False
        )
    )


# ============================================================
# 14. COMPLETE
# ============================================================

print("\n========================================")
print("TRAINING AND HYBRID TEST COMPLETE")
print("========================================")

# ============================================================
# SHOW FULL DATA FOR REAL MEDIUM EXAMPLES
# ============================================================

medium_indexes = hybrid_df[
    hybrid_df["Final_Level"] == "Medium"
].index

print("\n========================================")
print("FULL MEDIUM TEST EXAMPLES")
print("========================================")

medium_test_data = df.loc[
    medium_indexes,
    [
        "Age",
        "Gender",
        "Height_cm",
        "Weight_kg",
        "Training_Frequency",
        "Training_Duration",
        "Warmup_Time",
        "Sleep_Hours",
        "Flexibility_Score",
        "Muscle_Asymmetry",
        "Recovery_Time",
        "Injury_History",
        "Stress_Level",
        "Training_Intensity"
    ]
].head(5)

print(medium_test_data.to_string(index=False))