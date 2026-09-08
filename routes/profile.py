from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    User,
    UserProfile,
    UserRole,
    Sport,
    CoachAthlete,
    ConnectionStatus,
    CoachTrainingRecommendation
)


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/api/profile"
)


# =========================================================
# HELPERS
# =========================================================

def get_current_user():
    """
    Return the authenticated user.

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

    return user, None


def validate_profile_data(data):
    """
    Validate and clean athlete profile data.
    """

    if not data:
        return False, "No data provided"

    required_fields = [
        "first_name",
        "last_name",
        "height",
        "weight",
        "age",
        "sport"
    ]

    for field in required_fields:
        value = data.get(field)

        if value is None or str(value).strip() == "":
            readable_name = field.replace("_", " ").capitalize()

            return (
                False,
                f"{readable_name} is required"
            )

    first_name = str(
        data.get("first_name", "")
    ).strip()

    last_name = str(
        data.get("last_name", "")
    ).strip()

    if len(first_name) > 100:
        return (
            False,
            "First name must not exceed 100 characters"
        )

    if len(last_name) > 100:
        return (
            False,
            "Last name must not exceed 100 characters"
        )

    try:
        sport = Sport[
            str(data["sport"]).strip().upper()
        ]

    except KeyError:
        valid_sports = [
            sport_item.value
            for sport_item in Sport
        ]

        return (
            False,
            "Invalid sport. Choose from: "
            + ", ".join(valid_sports)
        )

    try:
        height = float(data["height"])
        weight = float(data["weight"])
        age = int(data["age"])

        years_of_experience = int(
            data.get("years_of_experience", 0)
        )

        training_frequency = int(
            data.get("training_frequency", 0)
        )

    except (ValueError, TypeError):
        return (
            False,
            "Invalid numeric values"
        )

    if height <= 0 or height > 300:
        return (
            False,
            "Height must be between 1 and 300 cm"
        )

    if weight <= 0 or weight > 500:
        return (
            False,
            "Weight must be between 1 and 500 kg"
        )

    if age < 1 or age > 120:
        return (
            False,
            "Age must be between 1 and 120"
        )

    if years_of_experience < 0:
        return (
            False,
            "Years of experience cannot be negative"
        )

    if years_of_experience > age:
        return (
            False,
            "Years of experience cannot exceed age"
        )

    if training_frequency < 0 or training_frequency > 7:
        return (
            False,
            "Training frequency must be between 0 and 7"
        )

    injury_history = str(
        data.get("injury_history", "")
    ).strip() or None

    return True, {
        "first_name": first_name,
        "last_name": last_name,
        "height": height,
        "weight": weight,
        "age": age,
        "sport": sport,
        "years_of_experience": years_of_experience,
        "training_frequency": training_frequency,
        "injury_history": injury_history
    }


def save_profile(user, profile_data):
    """
    Create or update an athlete profile.
    """

    profile = UserProfile.query.filter_by(
        user_id=user.id
    ).first()

    is_new_profile = profile is None

    if is_new_profile:
        profile = UserProfile(
            user_id=user.id
        )

        db.session.add(profile)

    profile.first_name = profile_data["first_name"]
    profile.last_name = profile_data["last_name"]
    profile.height = profile_data["height"]
    profile.weight = profile_data["weight"]
    profile.age = profile_data["age"]
    profile.sport = profile_data["sport"]

    profile.years_of_experience = (
        profile_data["years_of_experience"]
    )

    profile.training_frequency = (
        profile_data["training_frequency"]
    )

    profile.injury_history = (
        profile_data["injury_history"]
    )

    profile.updated_at = datetime.utcnow()

    return profile, is_new_profile


def handle_profile_save():
    """
    Shared logic for profile creation and updates.
    """

    user, error_response = get_current_user()

    if error_response:
        return error_response

    if user.role != UserRole.ATHLETE:
        return jsonify({
            "error": (
                "Only athletes can create or update "
                "an athlete profile"
            )
        }), 403

    data = request.get_json(silent=True)

    valid, profile_result = validate_profile_data(data)

    if not valid:
        return jsonify({
            "error": profile_result
        }), 400

    try:
        profile, is_new_profile = save_profile(
            user,
            profile_result
        )

        db.session.commit()

        return jsonify({
            "message": (
                "Profile created successfully"
                if is_new_profile
                else "Profile updated successfully"
            ),
            "profile": profile.to_dict()
        }), 201 if is_new_profile else 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Profile save failed"
        )

        return jsonify({
            "error": "Could not save profile"
        }), 500


# =========================================================
# CREATE PROFILE
# =========================================================

@profile_bp.route("/create", methods=["POST"])
@jwt_required()
def create_profile():
    """
    Create or update the authenticated athlete's profile.
    """

    return handle_profile_save()


# =========================================================
# GET CURRENT PROFILE
# =========================================================

@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profile():
    """
    Return the authenticated athlete's profile.
    """

    user, error_response = get_current_user()

    if error_response:
        return error_response

    if user.role != UserRole.ATHLETE:
        return jsonify({
            "error": "Only athletes have athlete profiles"
        }), 403

    if not user.profile:
        return jsonify({
            "error": (
                "Profile not found. "
                "Please complete your profile first."
            )
        }), 404

    return jsonify({
        "profile": user.profile.to_dict()
    }), 200


# =========================================================
# UPDATE CURRENT PROFILE
# =========================================================

@profile_bp.route("", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update the authenticated athlete's profile.
    """

    return handle_profile_save()


# =========================================================
# GET ANOTHER USER PROFILE
# =========================================================

@profile_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_profile(user_id):
    """
    Return another user's profile.

    Athletes may view only their own profile.
    Coaches may view only accepted athletes.
    """

    current_user, error_response = get_current_user()

    if error_response:
        return error_response

    target_user = db.session.get(
        User,
        user_id
    )

    if not target_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if target_user.role != UserRole.ATHLETE:
        return jsonify({
            "error": "Selected user is not an athlete"
        }), 400

    if not target_user.profile:
        return jsonify({
            "error": "Profile not found"
        }), 404

    if current_user.role == UserRole.COACH:
        accepted_connection = (
            CoachAthlete.query.filter_by(
                coach_id=current_user.id,
                athlete_id=target_user.id,
                status=ConnectionStatus.ACCEPTED
            ).first()
        )

        if not accepted_connection:
            return jsonify({
                "error": (
                    "You do not have an accepted "
                    "connection with this athlete"
                )
            }), 403

    elif (
        current_user.role == UserRole.ATHLETE
        and current_user.id != target_user.id
    ):
        return jsonify({
            "error": (
                "You can only view your own profile"
            )
        }), 403

    else:
        return jsonify({
            "error": "You do not have access to this profile"
        }), 403

    return jsonify({
        "profile": target_user.profile.to_dict()
    }), 200

# =========================================================
# ATHLETE: COACH TRAINING RECOMMENDATIONS
# =========================================================

@profile_bp.route(
    "/coach-recommendations",
    methods=["GET"]
)
@jwt_required()
def get_coach_training_recommendations():
    """
    Return active training recommendations sent to the
    authenticated athlete by their currently accepted coach.
    """

    athlete, error_response = get_current_user()

    if error_response:
        return error_response

    if athlete.role != UserRole.ATHLETE:
        return jsonify({
            "error": "Only athletes can access coach recommendations"
        }), 403

    connection = CoachAthlete.query.filter_by(
        athlete_id=athlete.id,
        status=ConnectionStatus.ACCEPTED
    ).first()

    if not connection:
        return jsonify({
            "recommendations": [],
            "total": 0
        }), 200

    recommendations = CoachTrainingRecommendation.query.filter_by(
        athlete_id=athlete.id,
        coach_id=connection.coach_id,
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
