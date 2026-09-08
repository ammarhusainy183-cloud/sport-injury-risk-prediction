from datetime import datetime, timedelta
import re
import secrets

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from models import (
    db,
    User,
    UserProfile,
    UserRole,
    Sport,
    PasswordResetToken,
    CoachAthlete,
    ConnectionStatus
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# =========================================================
# VALIDATION HELPERS
# =========================================================

def validate_email(email):
    """Validate email format."""
    pattern = (
        r"^[a-zA-Z0-9._%+-]+@"
        r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength."""

    if len(password) < 8:
        return (
            False,
            "Password must be at least 8 characters long"
        )

    if not any(character.isupper() for character in password):
        return (
            False,
            "Password must contain at least one uppercase letter"
        )

    if not any(character.isdigit() for character in password):
        return (
            False,
            "Password must contain at least one digit"
        )

    special_character_pattern = (
        r"[!@#$%^&*()_+\-=[\]{};"
        r"':\"\\|,.<>/?`~]"
    )

    if not re.search(
        special_character_pattern,
        password
    ):
        return (
            False,
            "Password must contain at least one special character"
        )

    return True, "Valid"


def validate_profile_data(data):
    """Validate athlete profile information."""

    if not data:
        return (
            False,
            "Profile data is required for athlete registration."
        )

    required_fields = [
        "first_name",
        "last_name",
        "height",
        "weight",
        "age",
        "sport",
        "years_of_experience",
        "training_frequency"
    ]

    for field in required_fields:
        value = data.get(field)

        if value is None or str(value).strip() == "":
            readable_name = field.replace("_", " ").capitalize()

            return (
                False,
                f"{readable_name} is required."
            )

    try:
        sport = Sport[data["sport"].upper()]
    except KeyError:
        valid_sports = [
            sport_item.value
            for sport_item in Sport
        ]

        return (
            False,
            "Invalid sport. Choose from: "
            + ", ".join(valid_sports)
            + "."
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
            "Invalid numeric values in profile data."
        )

    if height <= 0:
        return (
            False,
            "Height must be greater than zero."
        )

    if weight <= 0:
        return (
            False,
            "Weight must be greater than zero."
        )

    if age <= 0 or age > 120:
        return (
            False,
            "Age must be between 1 and 120."
        )

    if years_of_experience < 0:
        return (
            False,
            "Years of experience cannot be negative."
        )

    if training_frequency < 0 or training_frequency > 7:
        return (
            False,
            "Training frequency must be between 0 and 7."
        )

    coach_email = (
        data.get("coach_email", "")
        .strip()
        .lower()
        or None
    )

    if coach_email and not validate_email(coach_email):
        return (
            False,
            "Coach email format is invalid."
        )

    return True, {
        "first_name": data["first_name"].strip(),
        "last_name": data["last_name"].strip(),
        "height": height,
        "weight": weight,
        "age": age,
        "sport": sport,
        "years_of_experience": years_of_experience,
        "training_frequency": training_frequency,
        "injury_history": (
            data.get("injury_history", "").strip()
            or None
        ),
        "coach_email": coach_email
    }


# =========================================================
# REGISTRATION
# =========================================================

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register an athlete or coach.

    Athletes may enter a coach email.
    A valid coach email creates a pending connection request.
    """

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    username = data.get(
        "username",
        ""
    ).strip()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )

    role_string = data.get(
        "role",
        "athlete"
    ).strip().lower()

    if not username or len(username) < 3:
        return jsonify({
            "error": "Username must be at least 3 characters"
        }), 400

    if not email or not validate_email(email):
        return jsonify({
            "error": "Invalid email format"
        }), 400

    password_is_valid, password_message = (
        validate_password(password)
    )

    if not password_is_valid:
        return jsonify({
            "error": password_message
        }), 400

    try:
        role = UserRole[role_string.upper()]
    except KeyError:
        return jsonify({
            "error": (
                'Invalid role. Must be "athlete" or "coach"'
            )
        }), 400

    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:
        return jsonify({
            "error": "Username already exists"
        }), 409

    existing_email = User.query.filter_by(
        email=email
    ).first()

    if existing_email:
        return jsonify({
            "error": "Email already registered"
        }), 409

    profile_data = None
    coach_warning = None
    coach_connection = None

    if role == UserRole.ATHLETE:
        valid, profile_result = validate_profile_data(
            data.get("profile")
        )

        if not valid:
            return jsonify({
                "error": profile_result
            }), 400

        profile_data = profile_result

    try:
        user = User(
            username=username,
            email=email,
            role=role
        )

        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        if role == UserRole.ATHLETE:
            profile = UserProfile(
                user_id=user.id,
                first_name=profile_data["first_name"],
                last_name=profile_data["last_name"],
                height=profile_data["height"],
                weight=profile_data["weight"],
                age=profile_data["age"],
                sport=profile_data["sport"],
                years_of_experience=(
                    profile_data["years_of_experience"]
                ),
                training_frequency=(
                    profile_data["training_frequency"]
                ),
                injury_history=(
                    profile_data["injury_history"]
                )
            )

            db.session.add(profile)

            coach_email = profile_data.get(
                "coach_email"
            )

            if coach_email:
                coach = User.query.filter_by(
                    email=coach_email,
                    role=UserRole.COACH,
                    is_active=True
                ).first()

                if coach:
                    connection = CoachAthlete(
                        coach_id=coach.id,
                        athlete_id=user.id,
                        status=ConnectionStatus.PENDING
                    )

                    db.session.add(connection)
                    db.session.flush()

                    coach_connection = {
                        "id": connection.id,
                        "coach_id": coach.id,
                        "coach_username": coach.username,
                        "coach_email": coach.email,
                        "status": connection.status.value
                    }

                else:
                    coach_warning = (
                        "Coach email was not found, "
                        "or the selected account is not "
                        "an active coach. No request was created."
                    )

        db.session.commit()

        access_token = create_access_token(
            identity=str(user.id)
        )

        response_data = {
            "message": "User registered successfully",
            "user": user.to_dict(),
            "profile": (
                user.profile.to_dict()
                if user.profile
                else None
            ),
            "coach_connection": coach_connection,
            "access_token": access_token
        }

        if coach_warning:
            response_data["warning"] = coach_warning

        return jsonify(response_data), 201

    except Exception as error:
        db.session.rollback()

        current_app.logger.exception(
            "Registration failed"
        )

        return jsonify({
            "error": "Registration failed. Please try again."
        }), 500


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in an existing user."""

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.query.filter_by(
        email=email
    ).first()

    if not user or not user.check_password(password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not user.is_active:
        return jsonify({
            "error": "Account is inactive"
        }), 403

    access_token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token
    }), 200


# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["POST"]
)
def forgot_password():
    """Create a password-reset token."""

    data = request.get_json(silent=True)

    if not data or not data.get("email"):
        return jsonify({
            "error": "Email is required"
        }), 400

    email = data.get(
        "email",
        ""
    ).strip().lower()

    user = User.query.filter_by(
        email=email
    ).first()

    generic_message = (
        "If that email exists, "
        "a password reset link has been sent."
    )

    if not user:
        return jsonify({
            "message": generic_message
        }), 200

    reset_token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.utcnow()
        + timedelta(hours=1)
    )

    token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )

    db.session.add(token_record)
    db.session.commit()

    current_app.logger.info(
        "Password reset requested for user ID %s",
        user.id
    )

    return jsonify({
        "message": generic_message,
        "reset_token": reset_token
    }), 200


# =========================================================
# RESET PASSWORD
# =========================================================

@auth_bp.route(
    "/reset-password",
    methods=["POST"]
)
def reset_password():
    """Reset password using a valid reset token."""

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    token = data.get(
        "token",
        ""
    ).strip()

    password = data.get(
        "password",
        ""
    )

    if not token or not password:
        return jsonify({
            "error": "Token and password are required"
        }), 400

    token_record = PasswordResetToken.query.filter_by(
        token=token,
        used=False
    ).first()

    if (
        not token_record
        or not token_record.is_valid()
    ):
        return jsonify({
            "error": "Invalid or expired reset token"
        }), 400

    password_is_valid, password_message = (
        validate_password(password)
    )

    if not password_is_valid:
        return jsonify({
            "error": password_message
        }), 400

    user = db.session.get(
        User,
        token_record.user_id
    )

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    user.set_password(password)
    token_record.used = True

    try:
        db.session.commit()

        return jsonify({
            "message": (
                "Password has been reset successfully"
            )
        }), 200

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Password reset failed"
        )

        return jsonify({
            "error": (
                "Password could not be reset. "
                "Please try again."
            )
        }), 500


# =========================================================
# CURRENT USER
# =========================================================

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Return the authenticated user."""

    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    connection_data = None

    if user.role == UserRole.ATHLETE:
        connection = user.athlete_link

        if connection:
            connection_data = connection.to_dict()

    return jsonify({
        "user": user.to_dict(),
        "profile": (
            user.profile.to_dict()
            if user.profile
            else None
        ),
        "coach_connection": connection_data
    }), 200


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    JWT logout is handled on the client by deleting the token.
    """

    return jsonify({
        "message": "Logout successful"
    }), 200