# Quick Start Guide - Sport Injury Risk Prediction Portal

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd c:\Users\VICTUS\myproject
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

Output should show:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Step 3: Open in Browser
- Navigate to: **http://localhost:5000**
- You'll see the login/register page

---

## First-Time User Flow

### As an Athlete

1. **Register**
   - Click "Register" tab
   - Choose role: "Athlete"
   - Create account (username, email, password)
   - Password must have: 8+ chars, 1 uppercase, 1 number

2. **Complete Profile**
   - Fill in personal data: name, age, height, weight
   - Select your sport and training experience
   - Add injury history if applicable

3. **Log Exercises**
   - Record daily training sessions
   - Include: type, duration, intensity
   - Optionally add distance and calories

4. **Get Risk Assessment**
   - Click "Risk Assessment"
   - System analyzes your profile and exercise history
   - Shows injury risk percentage and recommendations

### As a Coach

1. **Register**
   - Choose role: "Coach"
   - Create account

2. **Access Dashboard**
   - View summary of managed athletes
   - See high-risk athletes at a glance

3. **Add Athletes**
   - Use athlete ID to assign athletes to monitor
   - Click "Add Athlete" on dashboard

4. **Monitor Progress**
   - View each athlete's profile
   - Review their exercise logs
   - Check latest risk assessments
   - Receive alerts for high-risk situations

---

## Test Accounts

Create test accounts during setup:

**Athlete Test Account:**
- Username: testathlete1
- Email: athlete@test.com
- Password: TestPassword123

**Coach Test Account:**
- Username: testcoach1
- Email: coach@test.com
- Password: CoachPass123

---

## Key Features Overview

### Injury Risk Assessment
- Analyzes: BMI, training volume, recovery time, previous injuries
- Scores from 0-100%
- Four risk levels: Low, Medium, High, Critical

### Overtraining Detection
- Monitors training frequency
- Alerts on inadequate recovery
- Detects intensity spikes
- Provides specific recommendations

### Exercise Analytics
- Weekly statistics
- Exercise type breakdown
- Intensity distribution
- Total volume tracking

### Coach Dashboard
- Total athletes count
- High-risk athlete alerts
- Overtraining cases
- Quick metrics summary

---

## Common Tasks

### Log a Training Session
```
1. Click "Exercise Log"
2. Select date
3. Enter exercise type (e.g., "10K Run")
4. Set duration in minutes
5. Choose intensity: Low → Moderate → High → Very High
6. Add optional distance/calories
7. Click "Log Exercise"
```

### Update My Profile
```
1. Click "My Profile"
2. Edit any field (height, weight, sport, etc.)
3. Add injury history if needed
4. Click "Save Profile"
```

### Run Injury Assessment
```
1. Click "Risk Assessment"
2. Click "Run Assessment Now"
3. View results:
   - Risk score percentage
   - Risk level (color-coded)
   - Personalized recommendations
   - Specific risk factors identified
```

### As Coach: View Athlete Details
```
1. Click "My Athletes"
2. Find athlete in table
3. Click "View Details"
4. See their profile and risk assessment history
```

---

## Understanding Risk Levels

| Risk Level | Score | What It Means | Action |
|-----------|-------|--------------|--------|
| **Low** | 0-30% | Healthy training | Continue current routine |
| **Medium** | 30-50% | Monitor closely | Review training intensity |
| **High** | 50-70% | Caution needed | Reduce volume/intensity |
| **Critical** | 70-100% | Immediate action | Take extra rest days |

---

## Troubleshooting

**Q: Can't access http://localhost:5000**
- A: Make sure app.py is running (`python app.py`)
- Check port 5000 isn't used by another app

**Q: "Module not found" error**
- A: Run: `pip install -r requirements.txt`
- Make sure virtual environment is activated

**Q: Can't login after registering**
- A: Check email and password spelling
- Password must have uppercase letter and number

**Q: Database seems corrupted**
- A: Delete `sport_injury.db` file
- Restart app (creates new clean database)

**Q: Need to reset everything**
- A: Deactivate venv, delete venv folder and sport_injury.db
- Follow setup steps again

---

## API Testing (Optional)

Test API endpoints using Postman or curl:

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","email":"user@test.com","password":"Pass1234","role":"athlete"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"Pass1234"}'

# Get current user (requires token)
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Next Steps

1. Create your account and profile
2. Log at least 5-7 days of exercise data
3. Run a risk assessment
4. Review recommendations and adjust training
5. If coach: add athletes and monitor their progress

---

## Support

If you encounter issues:
1. Check README.md for detailed documentation
2. Review error messages in browser console (F12)
3. Check terminal/command prompt for Flask logs
4. Verify all dependencies installed: `pip list`

---

## System Architecture

```
Browser (Frontend)
    ↓
HTML/CSS/JS Dashboard
    ↓ (HTTP REST API)
Flask Backend
    ↓
SQLAlchemy ORM
    ↓
SQLite Database
    ↓
ML Predictor (scikit-learn)
```

---

Enjoy monitoring and optimizing your athletic performance! 🏃‍♂️⚽🏀
