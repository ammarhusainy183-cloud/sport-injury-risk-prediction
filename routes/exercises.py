from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    User,
    UserRole,
    ExerciseRoutine,
    TrainingIntensity,
    ExerciseIntensityScore
)


exercise_bp = Blueprint(
    "exercise",
    __name__,
    url_prefix="/api/exercises"
)


# =========================================================
# HELPERS
# =========================================================

def get_current_athlete():
    """
    Return the currently authenticated athlete.

    Returns:
        (user, error_response)
    """

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, (
            jsonify({
                "error": "Invalid authentication identity"
            }),
            401
        )

    user = db.session.get(User, user_id)

    if not user:
        return None, (
            jsonify({
                "error": "User not found"
            }),
            404
        )

    if not user.is_active:
        return None, (
            jsonify({
                "error": "Account is inactive"
            }),
            403
        )

    if user.role != UserRole.ATHLETE:
        return None, (
            jsonify({
                "error": "Only athletes can access exercise records"
            }),
            403
        )

    return user, None


def parse_intensity(value):
    """
    Convert an intensity string into TrainingIntensity.
    """

    try:
        return TrainingIntensity[
            str(value).strip().upper()
        ]
    except (KeyError, AttributeError):
        return None


def parse_intensity_score(value):
    """
    Validate a numeric training-intensity score from 1 to 10.

    Category mapping for compatibility:
        1-3   -> low
        4-6   -> moderate
        7-8   -> high
        9-10  -> very_high
    """

    try:
        score = float(value)
    except (TypeError, ValueError):
        return None, None

    if score < 1 or score > 10:
        return None, None

    if score <= 3:
        category = TrainingIntensity.LOW
    elif score <= 6:
        category = TrainingIntensity.MODERATE
    elif score <= 8:
        category = TrainingIntensity.HIGH
    else:
        category = TrainingIntensity.VERY_HIGH

    return score, category


def parse_exercise_date(value):
    """
    Parse a YYYY-MM-DD exercise date.
    """

    try:
        exercise_date = datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        return None, "Invalid date format. Use YYYY-MM-DD"

    if exercise_date > datetime.utcnow().date():
        return None, "Cannot log exercise for a future date"

    return exercise_date, None


def validate_exercise_payload(data, partial=False):
    """
    Validate exercise data.

    partial=False:
        Used when creating a record.

    partial=True:
        Used when updating selected fields.
    """

    if not data:
        return False, "No data provided"

    required_fields = [
        "date",
        "exercise_type",
        "duration_minutes",
        "intensity_score"
    ]

    if not partial:
        for field in required_fields:
            value = data.get(field)

            if value is None or str(value).strip() == "":
                readable_name = field.replace("_", " ").capitalize()

                return False, f"{readable_name} is required"

    cleaned = {}

    if "date" in data:
        exercise_date, date_error = parse_exercise_date(
            data.get("date")
        )

        if date_error:
            return False, date_error

        cleaned["date"] = exercise_date

    if "exercise_type" in data:
        exercise_type = str(
            data.get("exercise_type", "")
        ).strip()

        if not exercise_type:
            return False, "Exercise type cannot be empty"

        if len(exercise_type) > 100:
            return (
                False,
                "Exercise type must not exceed 100 characters"
            )

        cleaned["exercise_type"] = exercise_type

    if "duration_minutes" in data:
        try:
            duration = int(data["duration_minutes"])
        except (ValueError, TypeError):
            return False, "Invalid duration"

        if duration <= 0:
            return False, "Duration must be greater than zero"

        if duration > 1440:
            return (
                False,
                "Duration cannot exceed 1440 minutes"
            )

        cleaned["duration_minutes"] = duration

    if "intensity_score" in data:
        score, intensity = parse_intensity_score(
            data.get("intensity_score")
        )

        if score is None or intensity is None:
            return (
                False,
                "Training intensity must be a number from 1 to 10"
            )

        cleaned["intensity_score"] = score
        cleaned["intensity"] = intensity

    elif "intensity" in data:
        intensity = parse_intensity(
            data.get("intensity")
        )

        if intensity is None:
            return False, "Invalid intensity"

        fallback_score = {
            TrainingIntensity.LOW: 2.5,
            TrainingIntensity.MODERATE: 5.0,
            TrainingIntensity.HIGH: 7.5,
            TrainingIntensity.VERY_HIGH: 10.0,
        }[intensity]

        cleaned["intensity_score"] = fallback_score
        cleaned["intensity"] = intensity

    if "distance" in data:
        value = data.get("distance")

        if value in (None, ""):
            cleaned["distance"] = None
        else:
            try:
                distance = float(value)
            except (ValueError, TypeError):
                return False, "Invalid distance"

            if distance < 0:
                return False, "Distance cannot be negative"

            cleaned["distance"] = distance

    if "calories_burned" in data:
        value = data.get("calories_burned")

        if value in (None, ""):
            cleaned["calories_burned"] = None
        else:
            try:
                calories = int(value)
            except (ValueError, TypeError):
                return False, "Invalid calories burned"

            if calories < 0:
                return (
                    False,
                    "Calories burned cannot be negative"
                )

            cleaned["calories_burned"] = calories

    if "notes" in data:
        notes = str(
            data.get("notes") or ""
        ).strip()

        cleaned["notes"] = notes or None

    return True, cleaned


# =========================================================
# CREATE EXERCISE
# =========================================================

@exercise_bp.route("", methods=["POST"])
@jwt_required()
def log_exercise():
    """
    Log a new exercise session for the authenticated athlete.
    """

    athlete, error_response = get_current_athlete()

    if error_response:
        return error_response

    if not athlete.profile:
        return jsonify({
            "error": (
                "Please complete your profile before "
                "logging exercise sessions"
            )
        }), 400

    data = request.get_json(silent=True)

    valid, exercise_result = validate_exercise_payload(
        data,
        partial=False
    )

    if not valid:
        return jsonify({
            "error": exercise_result
        }), 400

    try:
        intensity_score = exercise_result.pop(
            "intensity_score"
        )

        exercise = ExerciseRoutine(
            user_id=athlete.id,
            date=exercise_result["date"],
            exercise_type=exercise_result["exercise_type"],
            duration_minutes=exercise_result[
                "duration_minutes"
            ],
            intensity=exercise_result["intensity"],
            distance=exercise_result.get("distance"),
            calories_burned=exercise_result.get(
                "calories_burned"
            ),
            notes=exercise_result.get("notes")
        )

        db.session.add(exercise)
        db.session.flush()

        db.session.add(
            ExerciseIntensityScore(
                exercise_id=exercise.id,
                score=intensity_score
            )
        )

        db.session.commit()

        return jsonify({
            "message": "Exercise logged successfully",
            "exercise": exercise.to_dict()
        }), 201

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Exercise creation failed"
        )

        return jsonify({
            "error": "Could not save exercise"
        }), 500


# =========================================================
# GET EXERCISE HISTORY
# =========================================================

@exercise_bp.route("", methods=["GET"])
@jwt_required()
def get_exercises():
    """
    Return exercise history for the authenticated athlete.
    """

    athlete, error_response = get_current_athlete()

    if error_response:
        return error_response

    try:
        days = int(
            request.args.get("days", 30)
        )

        limit = int(
            request.args.get("limit", 100)
        )

        offset = int(
            request.args.get("offset", 0)
        )

    except (ValueError, TypeError):
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

    if offset < 0:
        return jsonify({
            "error": "Offset cannot be negative"
        }), 400

    start_date = (
        datetime.utcnow().date()
        - timedelta(days=days - 1)
    )

    base_query = ExerciseRoutine.query.filter(
        ExerciseRoutine.user_id == athlete.id,
        ExerciseRoutine.date >= start_date
    )

    total = base_query.count()

    exercises = base_query.order_by(
        ExerciseRoutine.date.desc(),
        ExerciseRoutine.id.desc()
    ).offset(
        offset
    ).limit(
        limit
    ).all()

    return jsonify({
        "exercises": [
            exercise.to_dict()
            for exercise in exercises
        ],
        "pagination": {
            "total": total,
            "offset": offset,
            "limit": limit
        }
    }), 200


# =========================================================
# GET ONE EXERCISE
# =========================================================

@exercise_bp.route(
    "/<int:exercise_id>",
    methods=["GET"]
)
@jwt_required()
def get_exercise(exercise_id):
    """
    Return one exercise owned by the authenticated athlete.
    """

    athlete, error_response = get_current_athlete()

    if error_response:
        return error_response

    exercise = ExerciseRoutine.query.filter_by(
        id=exercise_id,
        user_id=athlete.id
    ).first()

    if not exercise:
        return jsonify({
            "error": "Exercise not found"
        }), 404

    return jsonify({
        "exercise": exercise.to_dict()
    }), 200


# =========================================================
# UPDATE EXERCISE
# =========================================================

@exercise_bp.route(
    "/<int:exercise_id>",
    methods=["PUT"]
)
@jwt_required()
def update_exercise(exercise_id):
    """
    Update an exercise owned by the authenticated athlete.
    """

    athlete, error_response = get_current_athlete()

    if error_response:
        return error_response

    exercise = ExerciseRoutine.query.filter_by(
        id=exercise_id,
        user_id=athlete.id
    ).first()

    if not exercise:
        return jsonify({
            "error": "Exercise not found"
        }), 404

    data = request.get_json(silent=True)

    valid, exercise_result = validate_exercise_payload(
        data,
        partial=True
    )

    if not valid:
        return jsonify({
            "error": exercise_result
        }), 400

    if not exercise_result:
        return jsonify({
            "error": "No supported fields were provided"
        }), 400

    intensity_score = exercise_result.pop(
        "intensity_score",
        None
    )

    for field, value in exercise_result.items():
        setattr(exercise, field, value)

    if intensity_score is not None:
        if exercise.intensity_detail:
            exercise.intensity_detail.score = intensity_score
        else:
            exercise.intensity_detail = ExerciseIntensityScore(
                score=intensity_score
            )

    try:
        db.session.commit()

        return jsonify({
            "message": "Exercise updated successfully",
            "exercise": exercise.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Exercise update failed"
        )

        return jsonify({
            "error": "Could not update exercise"
        }), 500


# =========================================================
# DELETE EXERCISE
# =========================================================

@exercise_bp.route(
    "/<int:exercise_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_exercise(exercise_id):
    """
    Delete an exercise owned by the authenticated athlete.
    """

    athlete, error_response = get_current_athlete()

    if error_response:
        return error_response

    exercise = ExerciseRoutine.query.filter_by(
        id=exercise_id,
        user_id=athlete.id
    ).first()

    if not exercise:
        return jsonify({
            "error": "Exercise not found"
        }), 404

    try:
        db.session.delete(exercise)
        db.session.commit()

        return jsonify({
            "message": "Exercise deleted successfully"
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Exercise deletion failed"
        )

        return jsonify({
            "error": "Could not delete exercise"
        }), 500


# =========================================================
# EXERCISE STATISTICS
# =========================================================

@exercise_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_exercise_stats():
    """
    Return exercise statistics for the authenticated athlete.
    """

    athlete, error_response = get_current_athlete()

    if error_response:
        return error_response

    try:
        days = int(
            request.args.get("days", 7)
        )
    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid days parameter"
        }), 400

    if days < 1 or days > 3650:
        return jsonify({
            "error": "Days must be between 1 and 3650"
        }), 400

    start_date = (
        datetime.utcnow().date()
        - timedelta(days=days - 1)
    )

    exercises = ExerciseRoutine.query.filter(
        ExerciseRoutine.user_id == athlete.id,
        ExerciseRoutine.date >= start_date
    ).all()

    if not exercises:
        return jsonify({
            "stats": {
                "total_sessions": 0,
                "total_duration_minutes": 0,
                "average_duration": 0,
                "total_calories": 0,
                "total_distance_km": 0,
                "exercises_by_type": {},
                "days_trained": 0,
                "most_common_intensity": None,
                "days_analyzed": days
            }
        }), 200

    total_duration = sum(
        exercise.duration_minutes
        for exercise in exercises
    )

    total_calories = sum(
        exercise.calories_burned or 0
        for exercise in exercises
    )

    total_distance = sum(
        exercise.distance or 0
        for exercise in exercises
    )

    days_trained = len({
        exercise.date
        for exercise in exercises
    })

    exercises_by_type = {}

    for exercise in exercises:
        exercise_name = exercise.exercise_type

        exercises_by_type[exercise_name] = (
            exercises_by_type.get(exercise_name, 0) + 1
        )

    intensities = [
        exercise.intensity.value
        for exercise in exercises
    ]

    most_common_intensity = max(
        set(intensities),
        key=intensities.count
    )

    return jsonify({
        "stats": {
            "total_sessions": len(exercises),
            "total_duration_minutes": total_duration,
            "average_duration": round(
                total_duration / len(exercises),
                1
            ),
            "total_calories": total_calories,
            "total_distance_km": round(
                total_distance,
                2
            ),
            "exercises_by_type": exercises_by_type,
            "days_trained": days_trained,
            "most_common_intensity": (
                most_common_intensity
            ),
            "days_analyzed": days
        }
    }), 200