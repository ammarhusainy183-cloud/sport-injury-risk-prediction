from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    User,
    ExerciseRoutine,
    InjuryRiskAssessment,
    RiskLevel,
    CoachAthlete,
    ConnectionStatus,
    HighRiskAlert,
)


risk_bp = Blueprint("risk", __name__, url_prefix="/api/risk")


# ============================================================
# HELPERS
# ============================================================

def get_user_by_identity():
    """Return the authenticated user from the JWT identity."""
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

    return db.session.get(User, user_id)


def validate_assessment_inputs(data):
    """
    Validate the extra inputs required by the trained Random Forest model.

    Expected JSON:
        gender: 0 or 1
        warmup_time: minutes
        sleep_hours: hours
        stress_level: 1-10
        flexibility_score: 0-100
        muscle_asymmetry: >= 0
        recovery_time: hours
    """

    if not data:
        return False, "Assessment data is required"

    required_fields = [
        "gender",
        "warmup_time",
        "sleep_hours",
        "stress_level",
        "flexibility_score",
        "muscle_asymmetry",
        "recovery_time",
    ]

    for field in required_fields:
        if field not in data or data[field] in (None, ""):
            readable = field.replace("_", " ").capitalize()
            return False, f"{readable} is required"

    try:
        cleaned = {
            "gender": int(data["gender"]),
            "warmup_time": float(data["warmup_time"]),
            "sleep_hours": float(data["sleep_hours"]),
            "stress_level": float(data["stress_level"]),
            "flexibility_score": float(data["flexibility_score"]),
            "muscle_asymmetry": float(data["muscle_asymmetry"]),
            "recovery_time": float(data["recovery_time"]),
        }
    except (TypeError, ValueError):
        return False, "Assessment values must be valid numbers"

    if cleaned["gender"] not in (0, 1):
        return False, "Gender must be 0 or 1"

    if cleaned["warmup_time"] < 0:
        return False, "Warm-up time cannot be negative"

    if not 0 <= cleaned["sleep_hours"] <= 24:
        return False, "Sleep hours must be between 0 and 24"

    if not 1 <= cleaned["stress_level"] <= 10:
        return False, "Stress level must be between 1 and 10"

    if not 0 <= cleaned["flexibility_score"] <= 100:
        return False, "Flexibility score must be between 0 and 100"

    if cleaned["muscle_asymmetry"] < 0:
        return False, "Muscle asymmetry cannot be negative"

    if cleaned["recovery_time"] < 0:
        return False, "Recovery time cannot be negative"

    return True, cleaned


def get_exercise_data(user_id, days=30):
    """Return recent exercise records in predictor-friendly dictionary format."""
    start_date = datetime.utcnow().date() - timedelta(days=days)

    recent_exercises = ExerciseRoutine.query.filter(
        ExerciseRoutine.user_id == user_id,
        ExerciseRoutine.date >= start_date,
    ).order_by(
        ExerciseRoutine.date.asc()
    ).all()

    return [
        {
            "date": exercise.date,
            "exercise_type": exercise.exercise_type,
            "duration_minutes": exercise.duration_minutes,
            "intensity": exercise.intensity.value,
            "intensity_score": (
                exercise.intensity_detail.score
                if exercise.intensity_detail
                else None
            ),
            "distance": exercise.distance,
            "calories_burned": exercise.calories_burned,
            "notes": exercise.notes,
        }
        for exercise in recent_exercises
    ]


def get_athlete_data(profile):
    """Return profile data used by the injury predictor."""
    return {
        "height": profile.height,
        "weight": profile.weight,
        "age": profile.age,
        "years_of_experience": profile.years_of_experience,
        "training_frequency": profile.training_frequency,
        "injury_history": profile.injury_history,
    }


def get_assessment_history(user_id, limit=5):
    """Return recent assessment results for optional trend analysis."""
    assessments = InjuryRiskAssessment.query.filter_by(
        user_id=user_id
    ).order_by(
        InjuryRiskAssessment.assessment_date.desc()
    ).limit(limit).all()

    return [
        {
            "risk_level": assessment.risk_level.value,
            "injury_percentage": assessment.injury_percentage,
            "assessment_date": assessment.assessment_date.isoformat(),
        }
        for assessment in assessments
    ]


def create_high_risk_alert(athlete_id, assessment):
    """
    Create one persistent High-Risk alert for the athlete's
    accepted coach.

    No alert is created when:
        - the result is not High
        - the athlete has no accepted coach
        - an alert already exists for this assessment
    """

    if assessment.risk_level != RiskLevel.HIGH:
        return None

    connection = CoachAthlete.query.filter_by(
        athlete_id=athlete_id,
        status=ConnectionStatus.ACCEPTED,
    ).first()

    if not connection:
        return None

    existing_alert = HighRiskAlert.query.filter_by(
        assessment_id=assessment.id
    ).first()

    if existing_alert:
        return existing_alert

    athlete = db.session.get(User, athlete_id)

    if athlete and athlete.profile:
        athlete_name = athlete.profile.first_name
    elif athlete:
        athlete_name = athlete.username
    else:
        athlete_name = f"Athlete {athlete_id}"

    alert = HighRiskAlert(
        athlete_id=athlete_id,
        coach_id=connection.coach_id,
        assessment_id=assessment.id,
        message=(
            f"{athlete_name} has been classified as High Risk "
            f"with an injury probability of "
            f"{assessment.injury_percentage:.1f}%. "
            "Review the athlete's recent training and recovery plan."
        ),
    )

    db.session.add(alert)
    db.session.commit()

    return alert


def save_prediction(user_id, prediction):
    """Save one completed prediction and return the database record."""
    risk_level_map = {
    "low": RiskLevel.LOW,
    "medium": RiskLevel.MEDIUM,
    "high": RiskLevel.HIGH,
}

    risk_level = risk_level_map.get(
        prediction.get("risk_level"),
        RiskLevel.MEDIUM,
    )

    risk_factors = prediction.get("risk_factors", {})

    recommendations = prediction.get("recommendations", [])

    assessment = InjuryRiskAssessment(
        user_id=user_id,
        risk_level=risk_level,
        injury_percentage=float(prediction.get("injury_percentage", 0)),
        overtraining_detected=bool(
            prediction.get("overtraining_detected", False)
        ),
        overtraining_score=float(
            prediction.get("overtraining_score", 0)
        ),
        recommendations="\n".join(recommendations),
        model_version=prediction.get("model_version", "rf-v1.0"),
        high_volume_training=bool(
            risk_factors.get("high_volume_training", False)
        ),
        inadequate_recovery=bool(
            risk_factors.get("inadequate_recovery", False)
        ),
        poor_form_risk=bool(
            risk_factors.get("poor_form_risk", False)
        ),
        previous_injury_risk=bool(
            risk_factors.get("previous_injury_risk", False)
        ),
    )

    db.session.add(assessment)
    db.session.commit()

    return assessment


# ============================================================
# ATHLETE: RUN OWN ASSESSMENT
# ============================================================

@risk_bp.route("/assess", methods=["POST"])
@jwt_required()
def assess_injury_risk():
    """Run a Random Forest injury-risk assessment for the current athlete."""

    user = get_user_by_identity()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role.value != "athlete":
        return jsonify({
            "error": "Only athletes can run this assessment"
        }), 403

    profile = user.profile

    if not profile:
        return jsonify({
            "error": "Please complete your profile first"
        }), 400

    request_data = request.get_json(silent=True)

    valid, result = validate_assessment_inputs(request_data)

    if not valid:
        return jsonify({"error": result}), 400

    assessment_inputs = result

    recent_exercise_data = get_exercise_data(
        user.id,
        days=7
    )

    if not recent_exercise_data:
        return jsonify({
            "error": (
                "Please log at least one exercise session "
                "from the last 7 days before running an assessment."
            ),
            "code": "RECENT_EXERCISE_REQUIRED"
        }), 400

    exercise_data = get_exercise_data(
        user.id,
        days=30
    )

    athlete_data = get_athlete_data(profile)
    assessment_history = get_assessment_history(user.id, limit=5)

    try:
        from ml.predictor import predictor
    except Exception as error:
        return jsonify({
            "error": f"Predictor unavailable: {error}"
        }), 503

    try:
        prediction = predictor.predict_injury_risk(
            athlete_data,
            exercise_data,
            assessment_history,
            assessment_inputs,
        )
    except Exception as error:
        return jsonify({
            "error": f"Prediction failed: {error}"
        }), 500

    try:
        assessment = save_prediction(user.id, prediction)
    except Exception as error:
        db.session.rollback()
        return jsonify({
            "error": f"Could not save assessment: {error}"
        }), 500

    alert_created = False

    try:
        alert = create_high_risk_alert(
            user.id,
            assessment,
        )
        alert_created = alert is not None

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Assessment saved, but High-Risk alert creation failed"
        )

    return jsonify({
        "message": "Assessment completed",
        "assessment": assessment.to_dict(),
        "coach_alert_created": alert_created,
    }), 201


# ============================================================
# ATHLETE: LATEST ASSESSMENT
# ============================================================

@risk_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_assessment():
    """Return the current user's latest injury-risk assessment."""

    user = get_user_by_identity()

    if not user:
        return jsonify({"error": "User not found"}), 404

    assessment = InjuryRiskAssessment.query.filter_by(
        user_id=user.id
    ).order_by(
        InjuryRiskAssessment.assessment_date.desc()
    ).first()

    if not assessment:
        return jsonify({"error": "No assessment found"}), 404

    return jsonify({
        "assessment": assessment.to_dict()
    }), 200


# ============================================================
# ATHLETE: ASSESSMENT HISTORY
# ============================================================

@risk_bp.route("/history", methods=["GET"])
@jwt_required()
def get_assessment_history_route():
    """Return injury-risk assessment history for the current user."""

    user = get_user_by_identity()

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        days = int(request.args.get("days", 90))
        limit = int(request.args.get("limit", 50))
    except (TypeError, ValueError):
        return jsonify({
            "error": "Invalid query parameters"
        }), 400

    if days < 1 or days > 3650:
        return jsonify({
            "error": "Days must be between 1 and 3650"
        }), 400

    if limit < 1 or limit > 200:
        return jsonify({
            "error": "Limit must be between 1 and 200"
        }), 400

    start_date = datetime.utcnow() - timedelta(days=days)

    assessments = InjuryRiskAssessment.query.filter(
        InjuryRiskAssessment.user_id == user.id,
        InjuryRiskAssessment.assessment_date >= start_date,
    ).order_by(
        InjuryRiskAssessment.assessment_date.desc()
    ).limit(limit).all()

    return jsonify({
        "assessments": [
            assessment.to_dict()
            for assessment in assessments
        ],
        "total": len(assessments),
    }), 200


# ============================================================
# COACH: ASSESS AN ACCEPTED ATHLETE
# ============================================================

@risk_bp.route("/<int:user_id>/assess", methods=["POST"])
@jwt_required()
def assess_athlete_risk(user_id):
    """
    Allow a coach to assess an accepted athlete.

    The coach must provide the same current-condition fields used
    by the athlete assessment form.
    """

    coach = get_user_by_identity()

    if not coach or coach.role.value != "coach":
        return jsonify({
            "error": "Only coaches can assess athletes"
        }), 403

    connection = CoachAthlete.query.filter_by(
        coach_id=coach.id,
        athlete_id=user_id,
        status=ConnectionStatus.ACCEPTED,
    ).first()

    if not connection:
        return jsonify({
            "error": "You do not have an accepted connection with this athlete"
        }), 403

    athlete = db.session.get(User, user_id)

    if not athlete or athlete.role.value != "athlete":
        return jsonify({
            "error": "Athlete not found"
        }), 404

    profile = athlete.profile

    if not profile:
        return jsonify({
            "error": "Athlete profile not found"
        }), 404

    request_data = request.get_json(silent=True)

    valid, result = validate_assessment_inputs(request_data)

    if not valid:
        return jsonify({"error": result}), 400

    assessment_inputs = result

    recent_exercise_data = get_exercise_data(
        athlete.id,
        days=7
    )

    if not recent_exercise_data:
        return jsonify({
            "error": (
                "This athlete must have at least one exercise "
                "session from the last 7 days before an assessment."
            ),
            "code": "RECENT_EXERCISE_REQUIRED"
        }), 400

    exercise_data = get_exercise_data(
        athlete.id,
        days=30
    )

    athlete_data = get_athlete_data(profile)
    assessment_history = get_assessment_history(
        athlete.id,
        limit=5,
    )

    try:
        from ml.predictor import predictor

        prediction = predictor.predict_injury_risk(
            athlete_data,
            exercise_data,
            assessment_history,
            assessment_inputs,
        )

        assessment = save_prediction(
            athlete.id,
            prediction,
        )

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "error": f"Assessment failed: {error}"
        }), 500

    alert_created = False

    try:
        alert = create_high_risk_alert(
            athlete.id,
            assessment,
        )
        alert_created = alert is not None

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Coach assessment saved, but High-Risk alert creation failed"
        )

    return jsonify({
        "message": "Athlete assessment completed",
        "assessment": assessment.to_dict(),
        "coach_alert_created": alert_created,
    }), 201