"""
Demo data seeder for Sport Injury Risk Prediction Portal.

IMPORTANT:
- This script does NOT create or delete user accounts.
- It updates the four existing athlete profiles to Football.
- It creates 7 days of realistic exercise history.
- It creates 7 days of assessment history.
- It creates high-risk alerts for the high-risk athletes.
- It uses DATABASE_URL when running on Render.
"""

import os
import sys
from datetime import date, datetime, timedelta

# Allow imports from the project root when this file is inside /scripts
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from models import (
    db,
    User,
    UserProfile,
    ExerciseRoutine,
    ExerciseIntensityScore,
    InjuryRiskAssessment,
    HighRiskAlert,
    Sport,
    TrainingIntensity,
    RiskLevel,
    AlertStatus,
)


# ============================================================
# ATHLETES
# ============================================================

ATHLETES = {
    "aynnradn": {
        "target_risk": RiskLevel.LOW,
        "target_percentages": [5.0, 5.5, 5.8, 5.4, 5.2, 5.6, 5.8],
        "overtraining": False,
    },

    "LuqmanHakim": {
        "target_risk": RiskLevel.MEDIUM,
        "target_percentages": [31.0, 33.0, 35.0, 37.0, 39.0, 41.0, 43.0],
        "overtraining": False,
    },

    "Hanzo": {
        "target_risk": RiskLevel.HIGH,
        "target_percentages": [55.0, 59.0, 63.0, 67.0, 70.0, 73.0, 76.0],
        "overtraining": False,
    },

    "Kaizo": {
        "target_risk": RiskLevel.HIGH,
        "target_percentages": [61.0, 66.0, 72.0, 77.0, 82.0, 87.0, 91.0],
        "overtraining": True,
    },
}


# ============================================================
# 7-DAY EXERCISE DATA
# ============================================================

EXERCISE_DATA = {
    "aynnradn": [
        (45, TrainingIntensity.LOW, 4.0, 380),
        (50, TrainingIntensity.MODERATE, 5.0, 450),
        (40, TrainingIntensity.LOW, 3.5, 330),
        None,  # Rest day
        (50, TrainingIntensity.MODERATE, 5.5, 480),
        (45, TrainingIntensity.LOW, 4.0, 360),
        (40, TrainingIntensity.LOW, 3.5, 320),
    ],

    "LuqmanHakim": [
        (75, TrainingIntensity.MODERATE, 7.0, 650),
        (80, TrainingIntensity.HIGH, 7.5, 720),
        (60, TrainingIntensity.MODERATE, 6.0, 550),
        (75, TrainingIntensity.HIGH, 7.0, 680),
        None,
        (85, TrainingIntensity.HIGH, 8.0, 780),
        (70, TrainingIntensity.MODERATE, 6.5, 620),
    ],

    "Hanzo": [
        (90, TrainingIntensity.HIGH, 9.0, 850),
        (100, TrainingIntensity.HIGH, 10.0, 950),
        (85, TrainingIntensity.HIGH, 8.5, 820),
        (95, TrainingIntensity.HIGH, 9.5, 900),
        (90, TrainingIntensity.HIGH, 9.0, 860),
        (105, TrainingIntensity.VERY_HIGH, 10.5, 1050),
        (90, TrainingIntensity.HIGH, 9.0, 880),
    ],

    "Kaizo": [
        (110, TrainingIntensity.VERY_HIGH, 11.0, 1100),
        (105, TrainingIntensity.VERY_HIGH, 10.5, 1050),
        (115, TrainingIntensity.VERY_HIGH, 11.5, 1150),
        (100, TrainingIntensity.VERY_HIGH, 10.0, 1000),
        (120, TrainingIntensity.VERY_HIGH, 12.0, 1200),
        (110, TrainingIntensity.VERY_HIGH, 11.0, 1100),
        (115, TrainingIntensity.VERY_HIGH, 11.5, 1150),
    ],
}


# ============================================================
# PROFILE VALUES
# ============================================================

PROFILE_DATA = {
    "aynnradn": {
        "first_name": "Ayn",
        "last_name": "Nur",
        "height": 165,
        "weight": 58,
        "age": 21,
        "years_of_experience": 3,
        "training_frequency": 4,
        "injury_history": "No significant previous injury.",
    },

    "LuqmanHakim": {
        "first_name": "Luqman",
        "last_name": "Hakim",
        "height": 172,
        "weight": 68,
        "age": 22,
        "years_of_experience": 4,
        "training_frequency": 5,
        "injury_history": "Previous minor muscle strain.",
    },

    "Hanzo": {
        "first_name": "Hanzo",
        "last_name": "Super",
        "height": 175,
        "weight": 72,
        "age": 23,
        "years_of_experience": 5,
        "training_frequency": 6,
        "injury_history": "Previous ankle and muscle strain history.",
    },

    "Kaizo": {
        "first_name": "Kaizo",
        "last_name": "Super",
        "height": 178,
        "weight": 76,
        "age": 23,
        "years_of_experience": 6,
        "training_frequency": 7,
        "injury_history": "Previous lower-limb injury history.",
    },
}


# ============================================================
# MAIN SEED FUNCTION
# ============================================================

def seed_demo_data():

    # Make sure DATABASE_URL is present when running against Render.
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        print("DATABASE_URL detected.")
        print("The script will use the configured database.")
    else:
        print("WARNING: DATABASE_URL is NOT set.")
        print("The script would use the local development database.")

    app = create_app()

    with app.app_context():

        print("\n==========================================")
        print(" SPORT INJURY PORTAL - DEMO DATA SETUP")
        print("==========================================\n")

        today = date.today()
        start_date = today - timedelta(days=6)

        for username, settings in ATHLETES.items():

            print(f"\nProcessing athlete: {username}")

            # ------------------------------------------------
            # Find existing user
            # ------------------------------------------------

            athlete = User.query.filter_by(username=username).first()

            if not athlete:
                print(f"ERROR: User '{username}' was not found.")
                continue

            print(f"  User ID: {athlete.id}")

            # ------------------------------------------------
            # Find/create profile
            # ------------------------------------------------

            profile = UserProfile.query.filter_by(
                user_id=athlete.id
            ).first()

            profile_values = PROFILE_DATA[username]

            if not profile:
                profile = UserProfile(
                    user_id=athlete.id,
                    first_name=profile_values["first_name"],
                    last_name=profile_values["last_name"],
                    height=profile_values["height"],
                    weight=profile_values["weight"],
                    age=profile_values["age"],
                    sport=Sport.FOOTBALL,
                    years_of_experience=profile_values["years_of_experience"],
                    training_frequency=profile_values["training_frequency"],
                    injury_history=profile_values["injury_history"],
                )

                db.session.add(profile)

            else:
                profile.sport = Sport.FOOTBALL
                profile.first_name = profile_values["first_name"]
                profile.last_name = profile_values["last_name"]
                profile.height = profile_values["height"]
                profile.weight = profile_values["weight"]
                profile.age = profile_values["age"]
                profile.years_of_experience = profile_values[
                    "years_of_experience"
                ]
                profile.training_frequency = profile_values[
                    "training_frequency"
                ]
                profile.injury_history = profile_values[
                    "injury_history"
                ]

            # ------------------------------------------------
            # Remove only previous records created by THIS
            # seeder.
            # ------------------------------------------------

            marker = "DEMO_SEED_2026"

            old_exercises = ExerciseRoutine.query.filter(
                ExerciseRoutine.user_id == athlete.id,
                ExerciseRoutine.notes.like(f"{marker}%")
            ).all()

            for exercise in old_exercises:
                db.session.delete(exercise)

            old_assessments = InjuryRiskAssessment.query.filter(
                InjuryRiskAssessment.user_id == athlete.id,
                InjuryRiskAssessment.model_version == marker
            ).all()

            for assessment in old_assessments:
                alert = HighRiskAlert.query.filter_by(
                    assessment_id=assessment.id
                ).first()

                if alert:
                    db.session.delete(alert)

                db.session.delete(assessment)

            db.session.flush()

            # ------------------------------------------------
            # Create 7 days of exercise history
            # ------------------------------------------------

            exercises = EXERCISE_DATA[username]

            for day_index, exercise_data in enumerate(exercises):

                if exercise_data is None:
                    continue

                duration, intensity, distance, calories = exercise_data

                exercise_date = start_date + timedelta(days=day_index)

                exercise = ExerciseRoutine(
                    user_id=athlete.id,
                    date=exercise_date,
                    exercise_type="Football Training",
                    duration_minutes=duration,
                    intensity=intensity,
                    distance=distance,
                    calories_burned=calories,
                    notes=(
                        f"{marker} - "
                        f"Football training session"
                    ),
                )

                db.session.add(exercise)
                db.session.flush()

                intensity_score = {
                    TrainingIntensity.LOW: 3.0,
                    TrainingIntensity.MODERATE: 5.5,
                    TrainingIntensity.HIGH: 8.0,
                    TrainingIntensity.VERY_HIGH: 9.5,
                }[intensity]

                score = ExerciseIntensityScore(
                    exercise_id=exercise.id,
                    score=intensity_score,
                )

                db.session.add(score)

            # ------------------------------------------------
            # Create 7 days of assessment history
            # ------------------------------------------------

            percentages = settings["target_percentages"]

            for day_index, percentage in enumerate(percentages):

                assessment_date = datetime.combine(
                    start_date + timedelta(days=day_index),
                    datetime.min.time()
                ) + timedelta(hours=12)

                is_overtraining = (
                    settings["overtraining"]
                    and day_index >= 4
                )

                overtraining_score = (
                    min(95.0, 55.0 + (day_index * 6.0))
                    if is_overtraining
                    else 0.0
                )

                assessment = InjuryRiskAssessment(
                    user_id=athlete.id,
                    assessment_date=assessment_date,
                    risk_level=settings["target_risk"],
                    injury_percentage=percentage,
                    overtraining_detected=is_overtraining,
                    overtraining_score=overtraining_score,
                    recommendations=(
                        "Maintain regular recovery and hydration.\n"
                        "Continue monitoring training intensity.\n"
                        "Complete adequate warm-up before training."
                    )
                    if settings["target_risk"] == RiskLevel.LOW
                    else (
                        "Reduce training intensity.\n"
                        "Increase recovery time between sessions.\n"
                        "Monitor fatigue and muscle soreness."
                    )
                    if settings["target_risk"] == RiskLevel.MEDIUM
                    else (
                        "Reduce high-intensity training immediately.\n"
                        "Schedule adequate recovery and rest.\n"
                        "Monitor for pain or signs of injury."
                    ),
                    model_version=marker,
                    high_volume_training=(
                        settings["target_risk"]
                        in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                    ),
                    inadequate_recovery=(
                        settings["target_risk"]
                        in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                    ),
                    poor_form_risk=(
                        settings["target_risk"]
                        in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                    ),
                    previous_injury_risk=(
                        username in ["LuqmanHakim", "Hanzo", "Kaizo"]
                    ),
                )

                db.session.add(assessment)
                db.session.flush()

                # ------------------------------------------------
                # Create coach alert for high-risk athletes
                # ------------------------------------------------

                if (
                    settings["target_risk"]
                    in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                    and day_index == len(percentages) - 1
                ):

                    coach = User.query.filter_by(
                        role="coach"
                    ).first()

                    if coach:
                        alert = HighRiskAlert(
                            athlete_id=athlete.id,
                            coach_id=coach.id,
                            assessment_id=assessment.id,
                            status=AlertStatus.NEW,
                            message=(
                                f"High injury risk detected for "
                                f"{username}. "
                                f"Risk score: {percentage:.1f}%."
                            ),
                        )

                        db.session.add(alert)

            db.session.commit()

            print("  Profile: Football")
            print("  Exercise history: 7 days")
            print("  Assessment history: 7 days")
            print(
                f"  Target result: "
                f"{settings['target_risk'].value.upper()}"
            )

            if settings["overtraining"]:
                print("  Overtraining: YES")

        print("\n==========================================")
        print(" DEMO DATA SETUP COMPLETE")
        print("==========================================")
        print("\nAthletes:")
        print("  aynnradn     -> LOW")
        print("  LuqmanHakim  -> MEDIUM")
        print("  Hanzo        -> HIGH")
        print("  Kaizo        -> HIGH + OVERTRAINING")
        print("\nAll athletes are configured as FOOTBALL.")


if __name__ == "__main__":
    seed_demo_data()