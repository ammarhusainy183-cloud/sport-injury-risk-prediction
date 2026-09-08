import sys
import time
import json
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print('requests not installed. Please run: pip install requests')
    sys.exit(2)

BASE = 'http://127.0.0.1:5000/api'

def post(path, token=None, payload=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = requests.post(urljoin(BASE+'/', path.lstrip('/')), json=payload or {}, headers=headers)
    return r

def get(path, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = requests.get(urljoin(BASE+'/', path.lstrip('/')), headers=headers)
    return r

def main(argv=None):
    suffix = str(int(time.time()))[-5:]
    coach = {'username': f'coach_{suffix}', 'email': f'coach_{suffix}@example.com', 'password': 'Password1!','role':'coach'}
    athlete = {'username': f'athlete_{suffix}', 'email': f'athlete_{suffix}@example.com', 'password': 'Password1!','role':'athlete'}

    print('Registering coach...')
    r = post('/auth/register', payload=coach)
    print(r.status_code, r.text)
    if r.status_code not in (200,201):
        print('Coach registration failed')
        return 1
    coach_token = r.json().get('access_token') or r.json().get('token') or r.json().get('accessToken')
    if not coach_token:
        print('No coach token returned, attempting login...')
        r2 = post('/auth/login', payload={'email': coach['email'], 'password': coach['password']})
        print(r2.status_code, r2.text)
        if not r2.ok:
            return 1
        coach_token = r2.json().get('access_token') or r2.json().get('token')

    print('Registering athlete (with coach_email)...')
    athlete_payload = dict(athlete)
    athlete_payload['profile'] = {
        'first_name':'Test','last_name':'Ath','age':25,'height':180.0,'weight':75.0,'sport':'running','years_of_experience':3,'training_frequency':3,'injury_history':'None','coach_email': coach['email']
    }
    r = post('/auth/register', payload=athlete_payload)
    print(r.status_code, r.text)
    if r.status_code not in (200,201):
        print('Athlete registration failed')
        return 1
    athlete_token = r.json().get('access_token') or r.json().get('token') or r.json().get('accessToken')
    if not athlete_token:
        print('No athlete token returned, attempting login...')
        r2 = post('/auth/login', payload={'email': athlete['email'], 'password': athlete['password']})
        print(r2.status_code, r2.text)
        if not r2.ok:
            return 1
        athlete_token = r2.json().get('access_token') or r2.json().get('token')

    print('Verifying athlete profile...')
    r = get('/profile', token=athlete_token)
    print(r.status_code, r.text)
    if r.status_code == 404:
        print('Profile missing, creating...')
        payload = athlete_payload['profile']
        r2 = post('/profile/create', token=athlete_token, payload=payload)
        print(r2.status_code, r2.text)
        if not r2.ok:
            return 1

    print('Logging an exercise...')
    exercise = {'date': time.strftime('%Y-%m-%d'), 'exercise_type':'Running','duration_minutes':30,'intensity':'moderate','distance':5.0,'calories_burned':400,'notes':'Test run'}
    r = post('/exercises', token=athlete_token, payload=exercise)
    print(r.status_code, r.text)
    if not r.ok:
        return 1

    print('Running assessment...')
    r = post('/risk/assess', token=athlete_token)
    print(r.status_code, r.text)
    if not r.ok:
        return 1

    print('Coach fetching athletes...')
    r = get('/coach/athletes', token=coach_token)
    print(r.status_code, r.text)
    if not r.ok:
        return 1

    athletes = r.json().get('athletes') or []
    if not athletes:
        print('No athletes returned to coach — failure')
        return 1

    athlete_id = athletes[0].get('user_id') or athletes[0].get('id')
    print('Fetching coach athlete detail for id', athlete_id)
    r = get(f'/coach/athlete/{athlete_id}', token=coach_token)
    print(r.status_code, r.text)
    if not r.ok:
        return 1

    print('\nE2E smoke test succeeded')
    return 0


if __name__ == '__main__':
    sys.exit(main())
