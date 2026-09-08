from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    User,
    UserRole,
    InjuryRiskAssessment,
    CoachAthlete,
    ExerciseRoutine,
    ConnectionStatus,
    HighRiskAlert,
    AlertStatus,
    CoachTrainingRecommendation,
    RecommendationType
)


coach_bp = Blueprint(
    "coach",
    __name__,
    url_prefix="/api/coach"
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_current_coach():
    """
    Return the currently authenticated coach.

    Returns:
        (coach, error_response)
    """

    try:
        coach_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, (
            jsonify({"error": "Invalid authentication identity"}),
            401
        )

    coach = db.session.get(User, coach_id)

    if not coach:
        return None, (
            jsonify({"error": "User not found"}),
            404
        )

    if coach.role != UserRole.COACH:
        return None, (
            jsonify({
                "error": "Only coaches can access this endpoint"
            }),
            403
        )

    if not coach.is_active:
        return None, (
            jsonify({"error": "Coach account is inactive"}),
            403
        )

    return coach, None


def get_accepted_connection(coach_id, athlete_id):
    """
    Return an accepted coach-athlete connection.
    """

    return CoachAthlete.query.filter_by(
        coach_id=coach_id,
        athlete_id=athlete_id,
        status=ConnectionStatus.ACCEPTED
    ).first()


def get_latest_assessment(athlete_id):
    """
    Return an athlete's latest injury-risk assessment.
    """

    return InjuryRiskAssessment.query.filter_by(
        user_id=athlete_id
    ).order_by(
        InjuryRiskAssessment.assessment_date.desc()
    ).first()


# =========================================================
# PENDING CONNECTION REQUESTS
# =========================================================

@coach_bp.route("/requests", methods=["GET"])
@jwt_required()
def get_pending_requests():
    """
    Return pending athlete connection requests for the coach.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    requests_list = CoachAthlete.query.filter_by(
        coach_id=coach.id,
        status=ConnectionStatus.PENDING
    ).order_by(
        CoachAthlete.assigned_date.desc()
    ).all()

    pending_requests = []

    for connection in requests_list:
        athlete = connection.athlete

        if not athlete:
            continue

        profile = athlete.profile

        pending_requests.append({
            "connection_id": connection.id,
            "athlete": {
                "user_id": athlete.id,
                "username": athlete.username,
                "email": athlete.email,
                "profile": (
                    profile.to_dict()
                    if profile
                    else None
                )
            },
            "status": connection.status.value,
            "requested_at": (
                connection.assigned_date.isoformat()
                if connection.assigned_date
                else None
            )
        })

    return jsonify({
        "requests": pending_requests,
        "total": len(pending_requests)
    }), 200


@coach_bp.route(
    "/requests/<int:connection_id>/accept",
    methods=["PATCH"]
)
@jwt_required()
def accept_connection_request(connection_id):
    """
    Accept a pending athlete connection request.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = CoachAthlete.query.filter_by(
        id=connection_id,
        coach_id=coach.id
    ).first()

    if not connection:
        return jsonify({
            "error": "Connection request not found"
        }), 404

    if connection.status == ConnectionStatus.ACCEPTED:
        return jsonify({
            "error": "This request has already been accepted"
        }), 409

    if connection.status == ConnectionStatus.REJECTED:
        return jsonify({
            "error": "A rejected request cannot be accepted"
        }), 409

    connection.status = ConnectionStatus.ACCEPTED
    connection.responded_at = datetime.utcnow()

    try:
        db.session.commit()

        return jsonify({
            "message": "Athlete connection accepted",
            "connection": connection.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to accept coach-athlete request"
        )

        return jsonify({
            "error": "Could not accept the request"
        }), 500


@coach_bp.route(
    "/requests/<int:connection_id>/reject",
    methods=["PATCH"]
)
@jwt_required()
def reject_connection_request(connection_id):
    """
    Reject a pending athlete connection request.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = CoachAthlete.query.filter_by(
        id=connection_id,
        coach_id=coach.id
    ).first()

    if not connection:
        return jsonify({
            "error": "Connection request not found"
        }), 404

    if connection.status == ConnectionStatus.REJECTED:
        return jsonify({
            "error": "This request has already been rejected"
        }), 409

    if connection.status == ConnectionStatus.ACCEPTED:
        return jsonify({
            "error": (
                "An accepted athlete must be removed "
                "instead of rejected"
            )
        }), 409

    connection.status = ConnectionStatus.REJECTED
    connection.responded_at = datetime.utcnow()

    try:
        db.session.commit()

        return jsonify({
            "message": "Athlete connection rejected",
            "connection": connection.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to reject coach-athlete request"
        )

        return jsonify({
            "error": "Could not reject the request"
        }), 500


# =========================================================
# ACCEPTED ATHLETES
# =========================================================

@coach_bp.route("/athletes", methods=["GET"])
@jwt_required()
def get_coached_athletes():
    """
    Return athletes accepted and managed by the coach.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    coach_athletes = CoachAthlete.query.filter_by(
        coach_id=coach.id,
        status=ConnectionStatus.ACCEPTED
    ).order_by(
        CoachAthlete.responded_at.desc()
    ).all()

    athletes_data = []

    for connection in coach_athletes:
        athlete = connection.athlete

        if not athlete:
            continue

        profile = athlete.profile
        latest_assessment = get_latest_assessment(athlete.id)

        athletes_data.append({
            "user_id": athlete.id,
            "username": athlete.username,
            "email": athlete.email,
            "profile": (
                profile.to_dict()
                if profile
                else None
            ),
            "latest_assessment": (
                latest_assessment.to_dict()
                if latest_assessment
                else None
            ),
            "connection_id": connection.id,
            "status": connection.status.value,
            "assigned_date": (
                connection.assigned_date.isoformat()
                if connection.assigned_date
                else None
            ),
            "accepted_date": (
                connection.responded_at.isoformat()
                if connection.responded_at
                else None
            )
        })

    return jsonify({
        "athletes": athletes_data,
        "total": len(athletes_data)
    }), 200


# =========================================================
# ATHLETE DETAILS
# =========================================================

@coach_bp.route(
    "/athlete/<int:athlete_id>",
    methods=["GET"]
)
@jwt_required()
def get_athlete_details(athlete_id):
    """
    Return detailed information for an accepted athlete.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = get_accepted_connection(
        coach.id,
        athlete_id
    )

    if not connection:
        return jsonify({
            "error": (
                "You do not have an accepted connection "
                "with this athlete"
            )
        }), 403

    athlete = db.session.get(User, athlete_id)

    if not athlete:
        return jsonify({
            "error": "Athlete not found"
        }), 404

    if athlete.role != UserRole.ATHLETE:
        return jsonify({
            "error": "Selected user is not an athlete"
        }), 400

    profile = athlete.profile

    if not profile:
        return jsonify({
            "error": "Athlete profile not found"
        }), 404

    assessments = InjuryRiskAssessment.query.filter_by(
        user_id=athlete_id
    ).order_by(
        InjuryRiskAssessment.assessment_date.desc()
    ).limit(10).all()

    last_7_days = (
        datetime.utcnow().date()
        - timedelta(days=6)
    )

    recent_exercises = ExerciseRoutine.query.filter(
        ExerciseRoutine.user_id == athlete_id,
        ExerciseRoutine.date >= last_7_days
    ).order_by(
        ExerciseRoutine.date.desc()
    ).all()

    intensity_map = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "VERY_HIGH": 4
    }

    if recent_exercises:
        intensities = [
            intensity_map.get(
                exercise.intensity.name,
                2
            )
            for exercise in recent_exercises
        ]

        average_intensity = (
            sum(intensities)
            / len(intensities)
        )

        total_duration = sum(
            exercise.duration_minutes
            for exercise in recent_exercises
        )

        total_distance = sum(
            exercise.distance or 0
            for exercise in recent_exercises
        )

    else:
        average_intensity = 0
        total_duration = 0
        total_distance = 0

    latest_assessment = (
        assessments[0]
        if assessments
        else None
    )

    return jsonify({
        "athlete": {
            "user_id": athlete.id,
            "username": athlete.username,
            "email": athlete.email,
            "profile": profile.to_dict(),
            "connection": connection.to_dict(),
            "latest_assessment": (
                latest_assessment.to_dict()
                if latest_assessment
                else None
            ),
            "assessments": [
                assessment.to_dict()
                for assessment in assessments
            ],
            "recent_exercises": [
                exercise.to_dict()
                for exercise in recent_exercises
            ],
            "statistics": {
                "last_7_days": {
                    "total_sessions": len(
                        recent_exercises
                    ),
                    "total_duration_minutes": (
                        total_duration
                    ),
                    "total_distance_km": round(
                        total_distance,
                        2
                    ),
                    "average_intensity": round(
                        average_intensity,
                        2
                    )
                }
            }
        }
    }), 200


# =========================================================
# ATHLETE ASSESSMENT HISTORY
# =========================================================

@coach_bp.route(
    "/athlete/<int:athlete_id>/assessments",
    methods=["GET"]
)
@jwt_required()
def get_athlete_assessments(athlete_id):
    """
    Return assessment history for an accepted athlete.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = get_accepted_connection(
        coach.id,
        athlete_id
    )

    if not connection:
        return jsonify({
            "error": (
                "You do not have an accepted connection "
                "with this athlete"
            )
        }), 403

    try:
        days = int(
            request.args.get("days", 90)
        )

        limit = int(
            request.args.get("limit", 50)
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

    start_date = (
        datetime.utcnow()
        - timedelta(days=days)
    )

    assessments = InjuryRiskAssessment.query.filter(
        InjuryRiskAssessment.user_id == athlete_id,
        InjuryRiskAssessment.assessment_date >= start_date
    ).order_by(
        InjuryRiskAssessment.assessment_date.desc()
    ).limit(limit).all()

    return jsonify({
        "assessments": [
            assessment.to_dict()
            for assessment in assessments
        ],
        "total": len(assessments)
    }), 200


# =========================================================
# COACH DASHBOARD
# =========================================================

@coach_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """
    Return coach dashboard statistics.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    accepted_connections = CoachAthlete.query.filter_by(
        coach_id=coach.id,
        status=ConnectionStatus.ACCEPTED
    ).all()

    pending_requests = CoachAthlete.query.filter_by(
        coach_id=coach.id,
        status=ConnectionStatus.PENDING
    ).count()

    athlete_ids = [
        connection.athlete_id
        for connection in accepted_connections
    ]

    total_athletes = len(athlete_ids)
    high_risk_athletes = 0
    overtraining_athletes = 0
    low_risk_athletes = 0
    medium_risk_athletes = 0
    not_assessed = 0

    for athlete_id in athlete_ids:
        latest = get_latest_assessment(athlete_id)

        if not latest:
            not_assessed += 1
            continue

        risk_value = latest.risk_level.value

        if risk_value == "low":
            low_risk_athletes += 1

        elif risk_value == "medium":
            medium_risk_athletes += 1

        elif risk_value == "high":
            high_risk_athletes += 1

        # Backward compatibility:
        # old saved Critical assessments are treated as High
        # after moving the portal to the 3-stage system.
        elif risk_value == "critical":
            high_risk_athletes += 1

        if latest.overtraining_detected:
            overtraining_athletes += 1

    today = datetime.utcnow().date()

    if athlete_ids:
        assessments_today = (
            InjuryRiskAssessment.query.filter(
                InjuryRiskAssessment.user_id.in_(
                    athlete_ids
                ),
                db.func.date(
                    InjuryRiskAssessment.assessment_date
                ) == today
            ).count()
        )
    else:
        assessments_today = 0

    return jsonify({
        "dashboard": {
            "total_athletes": total_athletes,
            "pending_requests": pending_requests,
            "low_risk_athletes": low_risk_athletes,
            "medium_risk_athletes": medium_risk_athletes,
            "high_risk_athletes": high_risk_athletes,
            "athletes_with_overtraining": (
                overtraining_athletes
            ),
            "assessments_today": assessments_today,
            "not_assessed": not_assessed,
            "summary": {
                "low": low_risk_athletes,
                "medium": medium_risk_athletes,
                "high": high_risk_athletes,
                "not_assessed": not_assessed
            }
        }
    }), 200



# =========================================================
# HIGH-RISK COACH ALERTS
# =========================================================

@coach_bp.route("/alerts", methods=["GET"])
@jwt_required()
def get_high_risk_alerts():
    """
    Return High-Risk alerts belonging to the current coach.

    Optional query:
        ?status=new
        ?status=reviewed
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    status_filter = request.args.get(
        "status",
        ""
    ).strip().lower()

    query = HighRiskAlert.query.filter_by(
        coach_id=coach.id
    )

    if status_filter:
        if status_filter == "new":
            query = query.filter(
                HighRiskAlert.status == AlertStatus.NEW
            )

        elif status_filter == "reviewed":
            query = query.filter(
                HighRiskAlert.status == AlertStatus.REVIEWED
            )

        else:
            return jsonify({
                "error": "Status must be 'new' or 'reviewed'"
            }), 400

    alerts = query.order_by(
        HighRiskAlert.created_at.desc()
    ).all()

    return jsonify({
        "alerts": [
            alert.to_dict()
            for alert in alerts
        ],
        "total": len(alerts),
        "new_count": sum(
            1
            for alert in alerts
            if alert.status == AlertStatus.NEW
        )
    }), 200


@coach_bp.route(
    "/alerts/<int:alert_id>/review",
    methods=["PATCH"]
)
@jwt_required()
def review_high_risk_alert(alert_id):
    """
    Mark one High-Risk alert as Reviewed.

    A coach may only review an alert that belongs to them.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    alert = HighRiskAlert.query.filter_by(
        id=alert_id,
        coach_id=coach.id
    ).first()

    if not alert:
        return jsonify({
            "error": "High-Risk alert not found"
        }), 404

    if alert.status == AlertStatus.REVIEWED:
        return jsonify({
            "message": "Alert is already reviewed",
            "alert": alert.to_dict()
        }), 200

    # The coach must still have an accepted connection with
    # the athlete before reviewing the alert.
    connection = get_accepted_connection(
        coach.id,
        alert.athlete_id
    )

    if not connection:
        return jsonify({
            "error": (
                "You are no longer connected "
                "to this athlete"
            )
        }), 403

    try:
        alert.mark_reviewed()
        db.session.commit()

        return jsonify({
            "message": "High-Risk alert marked as reviewed",
            "alert": alert.to_dict()
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to mark High-Risk alert as reviewed"
        )

        return jsonify({
            "error": "Could not update the alert"
        }), 500


# =========================================================
# COACH TRAINING RECOMMENDATIONS
# =========================================================

@coach_bp.route(
    "/athlete/<int:athlete_id>/recommendations",
    methods=["POST"]
)
@jwt_required()
def create_training_recommendation(athlete_id):
    """
    Create a training-plan recommendation for an accepted athlete.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = get_accepted_connection(
        coach.id,
        athlete_id
    )

    if not connection:
        return jsonify({
            "error": (
                "You do not have an accepted connection "
                "with this athlete"
            )
        }), 403

    athlete = db.session.get(User, athlete_id)

    if not athlete or athlete.role != UserRole.ATHLETE:
        return jsonify({
            "error": "Athlete not found"
        }), 404

    data = request.get_json(silent=True) or {}

    type_value = str(
        data.get("recommendation_type", "")
    ).strip().lower()

    message = str(
        data.get("message", "")
    ).strip()

    type_map = {
        "reduce_intensity": RecommendationType.REDUCE_INTENSITY,
        "increase_recovery": RecommendationType.INCREASE_RECOVERY,
        "rest_day": RecommendationType.REST_DAY,
        "custom": RecommendationType.CUSTOM,
    }

    recommendation_type = type_map.get(type_value)

    if recommendation_type is None:
        return jsonify({
            "error": "Invalid recommendation type"
        }), 400

    if not message:
        return jsonify({
            "error": "Recommendation message is required"
        }), 400

    if len(message) > 1000:
        return jsonify({
            "error": "Recommendation message is too long"
        }), 400

    recommendation = CoachTrainingRecommendation(
        coach_id=coach.id,
        athlete_id=athlete_id,
        recommendation_type=recommendation_type,
        message=message,
    )

    try:
        db.session.add(recommendation)
        db.session.commit()

        return jsonify({
            "message": "Training recommendation sent",
            "recommendation": recommendation.to_dict()
        }), 201

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to create training recommendation"
        )

        return jsonify({
            "error": "Could not save recommendation"
        }), 500


@coach_bp.route(
    "/athlete/<int:athlete_id>/recommendations",
    methods=["GET"]
)
@jwt_required()
def get_athlete_training_recommendations(athlete_id):
    """
    Return recommendations the coach has sent to an accepted athlete.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = get_accepted_connection(
        coach.id,
        athlete_id
    )

    if not connection:
        return jsonify({
            "error": (
                "You do not have an accepted connection "
                "with this athlete"
            )
        }), 403

    recommendations = CoachTrainingRecommendation.query.filter_by(
        coach_id=coach.id,
        athlete_id=athlete_id,
        is_active=True
    ).order_by(
        CoachTrainingRecommendation.created_at.desc()
    ).limit(20).all()

    return jsonify({
        "recommendations": [
            recommendation.to_dict()
            for recommendation in recommendations
        ],
        "total": len(recommendations)
    }), 200


@coach_bp.route(
    "/recommendations/<int:recommendation_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_training_recommendation(recommendation_id):
    """
    Remove one recommendation created by the current coach.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    recommendation = CoachTrainingRecommendation.query.filter_by(
        id=recommendation_id,
        coach_id=coach.id
    ).first()

    if not recommendation:
        return jsonify({
            "error": "Recommendation not found"
        }), 404

    try:
        db.session.delete(recommendation)
        db.session.commit()

        return jsonify({
            "message": "Recommendation deleted"
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to delete training recommendation"
        )

        return jsonify({
            "error": "Could not delete recommendation"
        }), 500


# =========================================================
# COACH DELETE ATHLETE EXERCISE
# =========================================================

@coach_bp.route(
    "/athlete/<int:athlete_id>/exercise/<int:exercise_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_athlete_exercise(athlete_id, exercise_id):
    """
    Allow a coach to delete an incorrect exercise record
    belonging to an accepted athlete.

    Coaches may delete, but they do not edit athlete-entered
    training data.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = get_accepted_connection(
        coach.id,
        athlete_id
    )

    if not connection:
        return jsonify({
            "error": (
                "You do not have an accepted connection "
                "with this athlete"
            )
        }), 403

    exercise = ExerciseRoutine.query.filter_by(
        id=exercise_id,
        user_id=athlete_id
    ).first()

    if not exercise:
        return jsonify({
            "error": "Exercise record not found"
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
            "Coach failed to delete athlete exercise"
        )

        return jsonify({
            "error": "Could not delete exercise"
        }), 500


# =========================================================
# REMOVE ACCEPTED ATHLETE
# =========================================================

@coach_bp.route(
    "/remove-athlete/<int:athlete_id>",
    methods=["DELETE"]
)
@jwt_required()
def remove_athlete(athlete_id):
    """
    Remove an accepted athlete from the coach.

    The connection record is deleted so the athlete may later
    request another coach.
    """

    coach, error_response = get_current_coach()

    if error_response:
        return error_response

    connection = CoachAthlete.query.filter_by(
        coach_id=coach.id,
        athlete_id=athlete_id,
        status=ConnectionStatus.ACCEPTED
    ).first()

    if not connection:
        return jsonify({
            "error": (
                "This athlete is not currently "
                "connected to you"
            )
        }), 404

    try:
        db.session.delete(connection)
        db.session.commit()

        return jsonify({
            "message": "Athlete removed successfully"
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to remove athlete from coach"
        )

        return jsonify({
            "error": "Could not remove athlete"
        }), 500