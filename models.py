from datetime import datetime
import enum

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


# =========================================================
# ENUMS
# =========================================================

class UserRole(enum.Enum):
    ATHLETE = "athlete"
    COACH = "coach"


class Sport(enum.Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    RUNNING = "running"
    TENNIS = "tennis"
    VOLLEYBALL = "volleyball"
    SWIMMING = "swimming"
    GYMNASTICS = "gymnastics"
    CYCLING = "cycling"
    OTHER = "other"


class TrainingIntensity(enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConnectionStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AlertStatus(enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"


class RecommendationType(enum.Enum):
    REDUCE_INTENSITY = "reduce_intensity"
    INCREASE_RECOVERY = "increase_recovery"
    REST_DAY = "rest_day"
    CUSTOM = "custom"


# =========================================================
# USER
# =========================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.Enum(UserRole),
        default=UserRole.ATHLETE,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # One user has one athlete profile.
    profile = db.relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Athlete exercise records.
    exercise_routines = db.relationship(
        "ExerciseRoutine",
        back_populates="athlete",
        cascade="all, delete-orphan"
    )

    # Athlete injury-risk assessments.
    risk_assessments = db.relationship(
        "InjuryRiskAssessment",
        back_populates="athlete",
        cascade="all, delete-orphan"
    )

    # For a coach: all connection records with athletes.
    coach_links = db.relationship(
        "CoachAthlete",
        foreign_keys="CoachAthlete.coach_id",
        back_populates="coach",
        cascade="all, delete-orphan"
    )

    # For an athlete: one coach connection record.
    athlete_link = db.relationship(
        "CoachAthlete",
        foreign_keys="CoachAthlete.athlete_id",
        back_populates="athlete",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Password-reset records.
    password_reset_tokens = db.relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    coach_risk_alerts = db.relationship(
        "HighRiskAlert",
        foreign_keys="HighRiskAlert.coach_id",
        back_populates="coach",
        cascade="all, delete-orphan"
    )

    athlete_risk_alerts = db.relationship(
        "HighRiskAlert",
        foreign_keys="HighRiskAlert.athlete_id",
        back_populates="athlete",
        cascade="all, delete-orphan"
    )

    coach_training_recommendations = db.relationship(
        "CoachTrainingRecommendation",
        foreign_keys="CoachTrainingRecommendation.coach_id",
        back_populates="coach",
        cascade="all, delete-orphan"
    )

    athlete_training_recommendations = db.relationship(
        "CoachTrainingRecommendation",
        foreign_keys="CoachTrainingRecommendation.athlete_id",
        back_populates="athlete",
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
            "is_active": self.is_active
        }


# =========================================================
# PASSWORD RESET TOKEN
# =========================================================

class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    token = db.Column(
        db.String(128),
        unique=True,
        nullable=False,
        index=True
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    used = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="password_reset_tokens"
    )

    def is_valid(self):
        return (
            not self.used
            and self.expires_at >= datetime.utcnow()
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat(),
            "used": self.used,
            "created_at": self.created_at.isoformat()
        }


# =========================================================
# USER PROFILE
# =========================================================

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    height = db.Column(
        db.Float,
        nullable=False
    )

    weight = db.Column(
        db.Float,
        nullable=False
    )

    age = db.Column(
        db.Integer,
        nullable=False
    )

    sport = db.Column(
        db.Enum(Sport),
        nullable=False
    )

    years_of_experience = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    training_frequency = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    injury_history = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="profile"
    )

    @property
    def bmi(self):
        if not self.height or self.height <= 0:
            return None

        height_m = self.height / 100

        return round(
            self.weight / (height_m ** 2),
            2
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "height": self.height,
            "weight": self.weight,
            "age": self.age,
            "sport": self.sport.value,
            "years_of_experience": self.years_of_experience,
            "training_frequency": self.training_frequency,
            "bmi": self.bmi,
            "injury_history": self.injury_history,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            )
        }


# =========================================================
# EXERCISE ROUTINE
# =========================================================

class ExerciseRoutine(db.Model):
    __tablename__ = "exercise_routines"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )

    exercise_type = db.Column(
        db.String(100),
        nullable=False
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    intensity = db.Column(
        db.Enum(TrainingIntensity),
        nullable=False
    )

    distance = db.Column(
        db.Float,
        nullable=True
    )

    calories_burned = db.Column(
        db.Integer,
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    athlete = db.relationship(
        "User",
        back_populates="exercise_routines"
    )

    intensity_detail = db.relationship(
        "ExerciseIntensityScore",
        back_populates="exercise",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "exercise_type": self.exercise_type,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity.value,
            "intensity_score": (
                self.intensity_detail.score
                if self.intensity_detail
                else None
            ),
            "distance": self.distance,
            "calories_burned": self.calories_burned,
            "notes": self.notes,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }


# =========================================================
# EXERCISE INTENSITY SCORE
# =========================================================

class ExerciseIntensityScore(db.Model):
    __tablename__ = "exercise_intensity_scores"

    id = db.Column(db.Integer, primary_key=True)

    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercise_routines.id"),
        nullable=False,
        unique=True,
        index=True
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    exercise = db.relationship(
        "ExerciseRoutine",
        back_populates="intensity_detail"
    )

    __table_args__ = (
        db.CheckConstraint(
            "score >= 1 AND score <= 10",
            name="exercise_intensity_score_range"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "score": self.score,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            )
        }


# =========================================================
# INJURY RISK ASSESSMENT
# =========================================================

class InjuryRiskAssessment(db.Model):
    __tablename__ = "injury_risk_assessments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    assessment_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    risk_level = db.Column(
        db.Enum(RiskLevel),
        nullable=False
    )

    injury_percentage = db.Column(
        db.Float,
        nullable=False
    )

    overtraining_detected = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    overtraining_score = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    recommendations = db.Column(
        db.Text,
        nullable=True
    )

    model_version = db.Column(
        db.String(50),
        default="v1.0",
        nullable=False
    )

    high_volume_training = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    inadequate_recovery = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    poor_form_risk = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    previous_injury_risk = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    athlete = db.relationship(
        "User",
        back_populates="risk_assessments"
    )

    high_risk_alert = db.relationship(
        "HighRiskAlert",
        back_populates="assessment",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "assessment_date": (
                self.assessment_date.isoformat()
                if self.assessment_date
                else None
            ),
            "risk_level": self.risk_level.value,
            "injury_percentage": self.injury_percentage,
            "overtraining_detected": self.overtraining_detected,
            "overtraining_score": self.overtraining_score,
            "recommendations": (
                self.recommendations.split("\n")
                if self.recommendations
                else []
            ),
            "model_version": self.model_version,
            "risk_factors": {
                "high_volume_training":
                    self.high_volume_training,

                "inadequate_recovery":
                    self.inadequate_recovery,

                "poor_form_risk":
                    self.poor_form_risk,

                "previous_injury_risk":
                    self.previous_injury_risk
            },
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }


# =========================================================
# HIGH-RISK COACH ALERT
# =========================================================

class HighRiskAlert(db.Model):
    __tablename__ = "high_risk_alerts"

    id = db.Column(db.Integer, primary_key=True)

    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey("injury_risk_assessments.id"),
        nullable=False,
        unique=True,
        index=True
    )

    status = db.Column(
        db.Enum(AlertStatus),
        default=AlertStatus.NEW,
        nullable=False,
        index=True
    )

    message = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    reviewed_at = db.Column(db.DateTime, nullable=True)

    athlete = db.relationship(
        "User",
        foreign_keys=[athlete_id],
        back_populates="athlete_risk_alerts"
    )

    coach = db.relationship(
        "User",
        foreign_keys=[coach_id],
        back_populates="coach_risk_alerts"
    )

    assessment = db.relationship(
        "InjuryRiskAssessment",
        back_populates="high_risk_alert"
    )

    __table_args__ = (
        db.CheckConstraint(
            "coach_id != athlete_id",
            name="alert_coach_cannot_be_athlete"
        ),
    )

    def mark_reviewed(self):
        self.status = AlertStatus.REVIEWED
        self.reviewed_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "coach_id": self.coach_id,
            "assessment_id": self.assessment_id,
            "status": self.status.value,
            "message": self.message,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "reviewed_at": (
                self.reviewed_at.isoformat()
                if self.reviewed_at
                else None
            ),
            "athlete": (
                {
                    "id": self.athlete.id,
                    "username": self.athlete.username,
                    "email": self.athlete.email
                }
                if self.athlete
                else None
            ),
            "coach": (
                {
                    "id": self.coach.id,
                    "username": self.coach.username,
                    "email": self.coach.email
                }
                if self.coach
                else None
            ),
            "assessment": (
                self.assessment.to_dict()
                if self.assessment
                else None
            )
        }


# =========================================================
# COACH TRAINING RECOMMENDATION
# =========================================================

class CoachTrainingRecommendation(db.Model):
    __tablename__ = "coach_training_recommendations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    recommendation_type = db.Column(
        db.Enum(RecommendationType),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    coach = db.relationship(
        "User",
        foreign_keys=[coach_id],
        back_populates="coach_training_recommendations"
    )

    athlete = db.relationship(
        "User",
        foreign_keys=[athlete_id],
        back_populates="athlete_training_recommendations"
    )

    __table_args__ = (
        db.CheckConstraint(
            "coach_id != athlete_id",
            name="recommendation_coach_cannot_be_athlete"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "athlete_id": self.athlete_id,
            "recommendation_type": self.recommendation_type.value,
            "message": self.message,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "is_active": self.is_active,
            "coach": (
                {
                    "id": self.coach.id,
                    "username": self.coach.username,
                    "email": self.coach.email
                }
                if self.coach
                else None
            ),
            "athlete": (
                {
                    "id": self.athlete.id,
                    "username": self.athlete.username,
                    "email": self.athlete.email
                }
                if self.athlete
                else None
            )
        }


# =========================================================
# COACH-ATHLETE CONNECTION
# Design A:
# One coach can manage many athletes.
# One athlete can connect to only one coach.
# =========================================================

class CoachAthlete(db.Model):
    __tablename__ = "coach_athletes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    status = db.Column(
        db.Enum(ConnectionStatus),
        default=ConnectionStatus.PENDING,
        nullable=False,
        index=True
    )

    assigned_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    responded_at = db.Column(
        db.DateTime,
        nullable=True
    )

    coach = db.relationship(
        "User",
        foreign_keys=[coach_id],
        back_populates="coach_links"
    )

    athlete = db.relationship(
        "User",
        foreign_keys=[athlete_id],
        back_populates="athlete_link"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "coach_id",
            "athlete_id",
            name="unique_coach_athlete"
        ),

        db.CheckConstraint(
            "coach_id != athlete_id",
            name="coach_cannot_be_athlete"
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "athlete_id": self.athlete_id,
            "status": self.status.value,
            "assigned_date": (
                self.assigned_date.isoformat()
                if self.assigned_date
                else None
            ),
            "responded_at": (
                self.responded_at.isoformat()
                if self.responded_at
                else None
            ),
            "coach": (
                {
                    "id": self.coach.id,
                    "username": self.coach.username,
                    "email": self.coach.email
                }
                if self.coach
                else None
            ),
            "athlete": (
                {
                    "id": self.athlete.id,
                    "username": self.athlete.username,
                    "email": self.athlete.email
                }
                if self.athlete
                else None
            )
        }