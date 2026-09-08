# Sport Injury Risk Prediction Portal

A comprehensive web application for predicting sports injury risk and monitoring athlete health. The system uses machine learning to assess injury risk based on athlete profiles, exercise routines, and training patterns.

## Features

### For Athletes
- **User Registration & Login**: Secure authentication with JWT tokens
- **Profile Management**: Track personal data (height, weight, age, sport, training experience)
- **Exercise Logging**: Record daily training sessions with intensity, duration, and metrics
- **Injury Risk Assessment**: AI-powered predictions based on training patterns
- **Overtraining Detection**: Automatic alerts when training volume becomes risky
- **Progress Monitoring**: View historical assessments and trends

### For Coaches
- **Athlete Management**: Monitor multiple athletes under your supervision
- **Dashboard Analytics**: Real-time overview of athlete health and risk levels
- **Risk Monitoring**: Track high-risk and critical-risk athletes
- **Individual Athlete Details**: Detailed view of each athlete's profile, exercises, and assessments
- **Assessment History**: View trends and historical risk assessments

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: JWT (JSON Web Tokens)
- **ML Model**: scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **API**: RESTful

## Project Structure

```
myproject/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── ml/
│   ├── __init__.py
│   └── predictor.py      # ML model for injury risk prediction
├── routes/
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── profile.py        # User profile endpoints
│   ├── exercises.py      # Exercise logging endpoints
│   ├── risk.py           # Risk assessment endpoints
│   └── coach.py          # Coach management endpoints
├── templates/
│   └── dashboard.html    # Single-page application frontend
├── static/               # Static files (CSS, JS, images)
├── database/             # Database files
├── dataset/              # Training data
└── tests/                # Test files
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Steps

1. **Clone/Open the Project**
   ```bash
   cd c:\Users\VICTUS\myproject
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

   The application will start at: `http://localhost:5000`

5. **Access the Web Interface**
   - Open your browser to `http://localhost:5000`
   - Register as an Athlete or Coach
   - Complete your profile
   - Start logging exercises and assessments

## API Endpoints

### Authentication (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - Login user
- `GET /me` - Get current user info
- `POST /logout` - Logout user

### User Profile (`/api/profile`)
- `POST /create` - Create/Update profile
- `GET` - Get current user's profile
- `PUT` - Update profile
- `GET /<user_id>` - Get another user's profile

### Exercise Tracking (`/api/exercises`)
- `POST` - Log new exercise
- `GET` - Get exercise history
- `GET /stats` - Get exercise statistics
- `GET /<exercise_id>` - Get specific exercise
- `PUT /<exercise_id>` - Update exercise
- `DELETE /<exercise_id>` - Delete exercise

### Risk Assessment (`/api/risk`)
- `POST /assess` - Run injury risk assessment
- `GET /latest` - Get latest assessment
- `GET /history` - Get assessment history
- `POST /<user_id>/assess` - Coach assesses athlete

### Coach Management (`/api/coach`)
- `GET /athletes` - Get coached athletes
- `GET /athlete/<athlete_id>` - Get athlete details
- `GET /athlete/<athlete_id>/assessments` - Get athlete assessments
- `GET /dashboard` - Get coach dashboard stats
- `POST /add-athlete/<athlete_id>` - Add athlete
- `DELETE /remove-athlete/<athlete_id>` - Remove athlete

## Database Models

### User
- id, username, email, password_hash, role, created_at, is_active

### UserProfile
- id, user_id, first_name, last_name, height, weight, age, sport, years_of_experience, training_frequency, injury_history

### ExerciseRoutine
- id, user_id, date, exercise_type, duration_minutes, intensity, distance, calories_burned, notes

### InjuryRiskAssessment
- id, user_id, assessment_date, risk_level, injury_percentage, overtraining_detected, overtraining_score, recommendations, risk_factors

### CoachAthlete
- id, coach_id, athlete_id, assigned_date

## Machine Learning Model

The injury risk predictor analyzes:

1. **Anthropometric Factors**
   - BMI (Body Mass Index)
   - Age and experience level

2. **Training Volume**
   - Weekly training frequency
   - Total duration and intensity
   - Intensity spikes

3. **Recovery Metrics**
   - Rest days per week
   - Recovery ratio

4. **Historical Data**
   - Previous injury history
   - Assessment trends

### Risk Level Classification
- **Low Risk** (0-30%): Maintain current training
- **Medium Risk** (30-50%): Monitor closely
- **High Risk** (50-70%): Reduce training volume
- **Critical Risk** (70-100%): Immediate intervention needed

### Overtraining Detection
Identifies when athletes are:
- Training too frequently
- Lacking adequate recovery
- Showing sudden intensity increases
- At previous injury sites

## Usage Examples

### 1. Athlete Registration & Profile Setup

```
1. Go to http://localhost:5000
2. Click "Register" → Select "Athlete"
3. Enter username, email, password
4. Click "My Profile"
5. Fill in: name, height, weight, age, sport, experience, injury history
6. Save profile
```

### 2. Log Exercise Sessions

```
1. Click "Exercise Log"
2. Select date and enter exercise type
3. Set duration, intensity, optional distance/calories
4. Add notes if desired
5. Save exercise
```

### 3. Run Risk Assessment

```
1. Click "Risk Assessment"
2. Click "Run Assessment Now"
3. View injury risk percentage, risk level, and recommendations
4. Review personalized advice
```

### 4. Coach Monitoring Athletes

```
1. Register as a Coach
2. Coach dashboard shows all metrics
3. Click "My Athletes" to view list
4. Click "View Details" for individual athlete assessment
5. Monitor trends and send recommendations
```

## Configuration

Edit `config.py` to customize:

```python
# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///sport_injury.db'

# JWT
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# Debug mode
DEBUG = True  # Set to False in production
```

## Security Considerations

1. Change `SECRET_KEY` and `JWT_SECRET_KEY` in production
2. Use HTTPS in production
3. Implement rate limiting for API
4. Add CSRF protection
5. Sanitize user inputs
6. Use environment variables for sensitive data

## Future Enhancements

- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced analytics and visualizations (charts/graphs)
- [ ] Email notifications for high-risk alerts
- [ ] Integration with wearable devices (smartwatches)
- [ ] Video form analysis for exercise quality
- [ ] Nutrition recommendations
- [ ] Physiotherapy recommendations
- [ ] Team management features
- [ ] Social features (athlete community)
- [ ] Payment system for premium features
- [ ] Multi-language support
- [ ] Dark mode UI

## Troubleshooting

### Port Already in Use
```bash
# Change port in app.py:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Database Issues
```bash
# Delete existing database and recreate
# rm sport_injury.db (or del sport_injury.db on Windows)
python app.py  # Will create new database
```

### JWT Token Errors
```bash
# Clear browser localStorage:
# Open DevTools (F12) → Console → localStorage.clear()
```

### CORS Issues
```bash
# Update CORS settings in app.py if needed
CORS(app, origins=['http://localhost:3000', 'http://localhost:5000'])
```

## Testing

Create `tests/test_app.py` to run unit tests:

```bash
pytest tests/
```

## Deployment

### Using Gunicorn (Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Using Docker
Create `Dockerfile` and `docker-compose.yml` for containerization.

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or suggestions, please contact the development team.

## Changelog

### Version 1.0 (Current)
- Initial release
- User authentication and profiles
- Exercise logging
- ML-based injury risk prediction
- Coach dashboard and athlete management
- Overtraining detection
