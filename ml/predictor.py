from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


class InjuryRiskPredictor:
    """
    Random Forest injury-risk predictor.

    The trained model expects these 15 features in this exact order:

    Age
    Gender
    Height_cm
    Weight_kg
    BMI
    Training_Frequency
    Training_Duration
    Warmup_Time
    Sleep_Hours
    Flexibility_Score
    Muscle_Asymmetry
    Recovery_Time
    Injury_History
    Stress_Level
    Training_Intensity
    """

    FEATURE_NAMES = [
        "Age",
        "Gender",
        "Height_cm",
        "Weight_kg",
        "BMI",
        "Training_Frequency",
        "Training_Duration",
        "Warmup_Time",
        "Sleep_Hours",
        "Flexibility_Score",
        "Muscle_Asymmetry",
        "Recovery_Time",
        "Injury_History",
        "Stress_Level",
        "Training_Intensity",
    ]

    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent

        self.model_path = (
            project_root
            / "models"
            / "random_forest_injury_model.pkl"
        )

        self.model_version = "rf-hybrid-v1.0"
        self.model = None

        self._load_model()

    # ============================================================
    # MODEL LOADING
    # ============================================================

    def _load_model(self):
        """Load the trained Random Forest model from disk."""

        if not self.model_path.exists():
            raise FileNotFoundError(
                "Trained Random Forest model was not found at: "
                f"{self.model_path}"
            )

        self.model = joblib.load(self.model_path)

    # ============================================================
    # FEATURE PREPARATION
    # ============================================================

    def _calculate_bmi(self, height_cm, weight_kg):
        """Calculate BMI from height in cm and weight in kg."""

        height_m = float(height_cm) / 100.0

        if height_m <= 0:
            raise ValueError("Height must be greater than zero")

        return float(weight_kg) / (height_m ** 2)

    def _injury_history_value(self, injury_history):
        """
        Convert the website injury-history field into a numeric value.

        If the profile contains a number such as "2", that number is used.
        Otherwise:
            empty/no history -> 0
            any written injury history -> 1
        """

        if injury_history is None:
            return 0.0

        text = str(injury_history).strip()

        if not text:
            return 0.0

        try:
            value = float(text)
            return max(0.0, value)
        except ValueError:
            return 1.0

    def _recent_exercises(self, recent_exercises, days=7):
        """Return exercises from the latest requested time window."""

        cutoff = datetime.utcnow().date() - timedelta(days=days - 1)

        return [
            exercise
            for exercise in recent_exercises
            if exercise.get("date")
            and exercise["date"] >= cutoff
        ]

    def _training_duration(self, recent_exercises):
        """
        Convert recent exercise history into one training-duration value.

        The Random Forest dataset contains one Training_Duration feature,
        so the portal uses average session duration from the last 7 days.
        """

        exercises = self._recent_exercises(
            recent_exercises,
            days=7,
        )

        if not exercises:
            return 0.0

        durations = [
            float(exercise.get("duration_minutes", 0) or 0)
            for exercise in exercises
        ]

        if not durations:
            return 0.0

        return float(np.mean(durations))

    def _training_intensity(self, recent_exercises):
        """
        Return average training intensity on the dataset's 1-10 scale.

        New exercise records provide intensity_score directly.
        Older records fall back to the previous category mapping.
        """

        exercises = self._recent_exercises(
            recent_exercises,
            days=7,
        )

        if not exercises:
            return 0.0

        fallback_map = {
            "low": 2.5,
            "moderate": 5.0,
            "high": 7.5,
            "very_high": 10.0,
        }

        values = []

        for exercise in exercises:
            raw_score = exercise.get("intensity_score")

            if raw_score not in (None, ""):
                try:
                    score = float(raw_score)

                    if 1 <= score <= 10:
                        values.append(score)
                        continue

                except (TypeError, ValueError):
                    pass

            values.append(
                fallback_map.get(
                    str(exercise.get("intensity", "")).lower(),
                    5.0,
                )
            )

        return float(np.mean(values))

    def _build_feature_frame(
        self,
        athlete_data,
        recent_exercises,
        assessment_inputs,
    ):
        """Create one row with the exact feature order used for training."""

        if not assessment_inputs:
            raise ValueError(
                "Assessment inputs are required for Random Forest prediction"
            )

        height = float(athlete_data["height"])
        weight = float(athlete_data["weight"])

        bmi = self._calculate_bmi(
            height,
            weight,
        )

        feature_values = {
            "Age": float(athlete_data["age"]),
            "Gender": float(assessment_inputs["gender"]),
            "Height_cm": height,
            "Weight_kg": weight,
            "BMI": bmi,
            "Training_Frequency": float(
                athlete_data["training_frequency"]
            ),
            "Training_Duration": self._training_duration(
                recent_exercises
            ),
            "Warmup_Time": float(
                assessment_inputs["warmup_time"]
            ),
            "Sleep_Hours": float(
                assessment_inputs["sleep_hours"]
            ),
            "Flexibility_Score": float(
                assessment_inputs["flexibility_score"]
            ),
            "Muscle_Asymmetry": float(
                assessment_inputs["muscle_asymmetry"]
            ),
            "Recovery_Time": float(
                assessment_inputs["recovery_time"]
            ),
            "Injury_History": self._injury_history_value(
                athlete_data.get("injury_history")
            ),
            "Stress_Level": float(
                assessment_inputs["stress_level"]
            ),
            "Training_Intensity": self._training_intensity(
                recent_exercises
            ),
        }

        return pd.DataFrame(
            [[feature_values[name] for name in self.FEATURE_NAMES]],
            columns=self.FEATURE_NAMES,
        )

    # ============================================================
    # RISK LEVEL
    # ============================================================

    def _hybrid_risk_level(self, injury_percentage, athlete_data, recent_exercises, assessment_inputs):
        """Return the final portal level: low, medium, or high."""
        warning_points = 0

        if self._injury_history_value(athlete_data.get("injury_history")) >= 1:
            warning_points += 2

        if self._training_intensity(recent_exercises) >= 7:
            warning_points += 1

        if float(assessment_inputs["sleep_hours"]) < 7:
            warning_points += 1

        if float(assessment_inputs["recovery_time"]) < 52:
            warning_points += 1

        if float(assessment_inputs["stress_level"]) >= 8:
            warning_points += 1

        if float(assessment_inputs["muscle_asymmetry"]) >= 7:
            warning_points += 1

        # Random Forest probability remains the main signal.
        if injury_percentage >= 70:
            return "high"

        if injury_percentage >= 50 and warning_points >= 2:
            return "high"

        if injury_percentage >= 30:
            return "medium"

        if injury_percentage >= 15 and warning_points >= 4:
            return "medium"

        return "low"

    # ============================================================
    # SUPPORTING RISK INFORMATION
    # ============================================================

    def _analyze_training_patterns(
        self,
        athlete_data,
        recent_exercises,
        assessment_inputs,
    ):
        """
        Generate supporting risk-factor flags.

        These flags do NOT calculate the injury percentage.
        The injury percentage now comes only from Random Forest.
        """

        risk_factors = {
            "high_volume_training": False,
            "inadequate_recovery": False,
            "poor_form_risk": False,
            "previous_injury_risk": False,
        }

        exercises = self._recent_exercises(
            recent_exercises,
            days=7,
        )

        total_duration = sum(
            float(exercise.get("duration_minutes", 0) or 0)
            for exercise in exercises
        )

        if total_duration >= 300:
            risk_factors["high_volume_training"] = True

        unique_training_days = {
            exercise.get("date")
            for exercise in exercises
            if exercise.get("date")
        }

        if len(unique_training_days) >= 6:
            risk_factors["inadequate_recovery"] = True

        if float(assessment_inputs["recovery_time"]) < 24:
            risk_factors["inadequate_recovery"] = True

        if self._injury_history_value(
            athlete_data.get("injury_history")
        ) > 0:
            risk_factors["previous_injury_risk"] = True

        intensity_map = {
            "low": 1,
            "moderate": 2,
            "high": 3,
            "very_high": 4,
        }

        sorted_exercises = sorted(
            exercises,
            key=lambda item: item.get("date"),
        )

        if len(sorted_exercises) >= 2:
            previous_intensity = intensity_map.get(
                str(
                    sorted_exercises[-2].get(
                        "intensity",
                        "moderate",
                    )
                ).lower(),
                2,
            )

            latest_intensity = intensity_map.get(
                str(
                    sorted_exercises[-1].get(
                        "intensity",
                        "moderate",
                    )
                ).lower(),
                2,
            )

            if latest_intensity - previous_intensity >= 2:
                risk_factors["poor_form_risk"] = True

        overtraining_score = 0.0

        if risk_factors["high_volume_training"]:
            overtraining_score += 35

        if risk_factors["inadequate_recovery"]:
            overtraining_score += 35

        if float(assessment_inputs["sleep_hours"]) < 6:
            overtraining_score += 15

        if float(assessment_inputs["stress_level"]) >= 8:
            overtraining_score += 15

        overtraining_score = min(
            100.0,
            overtraining_score,
        )

        return risk_factors, overtraining_score

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    def _generate_recommendations(
        self,
        athlete_data,
        assessment_inputs,
        risk_factors,
        injury_percentage,
        risk_level,
    ):
        """Generate simple recommendations from the athlete's risk factors."""

        recommendations = []

        if risk_level == "high":
            recommendations.append(
                "Consider reducing training intensity until your risk factors improve."
            )

        if risk_factors["high_volume_training"]:
            recommendations.append(
                "Reduce weekly training volume and include additional recovery periods."
            )

        if risk_factors["inadequate_recovery"]:
            recommendations.append(
                "Increase recovery time and include at least one complete rest day."
            )

        if float(assessment_inputs["sleep_hours"]) < 7:
            recommendations.append(
                "Aim for consistent and sufficient sleep to support recovery."
            )

        if float(assessment_inputs["stress_level"]) >= 7:
            recommendations.append(
                "Your stress level is elevated. Consider lighter training and recovery activities."
            )

        if risk_factors["previous_injury_risk"]:
            recommendations.append(
                "Take extra care with previously injured areas and consider guidance from a qualified professional."
            )

        if risk_factors["poor_form_risk"]:
            recommendations.append(
                "Avoid sudden increases in training intensity and progress gradually."
            )

        if not recommendations:
            recommendations.append(
                "Maintain your current routine and continue monitoring your training and recovery."
            )

        return recommendations

    # ============================================================
    # MAIN PREDICTION
    # ============================================================

    def predict_injury_risk(
        self,
        athlete_data,
        recent_exercises,
        assessments=None,
        assessment_inputs=None,
    ):
        """
        Predict injury risk using the trained Random Forest.

        assessments is kept in the function signature so the existing
        application remains compatible, although the trained model does
        not use previous assessment results as an input feature.
        """

        if self.model is None:
            raise RuntimeError(
                "Random Forest model is not loaded"
            )

        features = self._build_feature_frame(
            athlete_data,
            recent_exercises,
            assessment_inputs,
        )

        if not hasattr(self.model, "predict_proba"):
            raise RuntimeError(
                "Loaded model does not support probability prediction"
            )

        probabilities = self.model.predict_proba(features)[0]

        classes = list(self.model.classes_)

        if 1 not in classes:
            raise RuntimeError(
                "The trained model does not contain injury class 1"
            )

        injury_class_index = classes.index(1)

        injury_probability = float(
            probabilities[injury_class_index]
        )

        injury_percentage = round(
            injury_probability * 100.0,
            2,
        )

        risk_level = self._hybrid_risk_level(
            injury_percentage,
            athlete_data,
            recent_exercises,
            assessment_inputs,
        )

        risk_factors, overtraining_score = (
            self._analyze_training_patterns(
                athlete_data,
                recent_exercises,
                assessment_inputs,
            )
        )

        recommendations = self._generate_recommendations(
            athlete_data,
            assessment_inputs,
            risk_factors,
            injury_percentage,
            risk_level,
        )

        return {
            "injury_percentage": injury_percentage,
            "risk_level": risk_level,
            "overtraining_detected": (
                overtraining_score >= 60
            ),
            "overtraining_score": overtraining_score,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "model_version": self.model_version,
        }


# Singleton predictor instance used by routes/risk.py
predictor = InjuryRiskPredictor()