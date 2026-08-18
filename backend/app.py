from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import sys
import tempfile
import traceback
from pydantic import ValidationError

from config import settings
import secrets_vault
import database
from models import User, Entry, Goal, WebAuthnCredential, ScaleUploadJob
import schemas
import ocr_service
import auth_service
from auth_service import login_required
import ssl_manager

app = Flask(__name__)
# Enable CORS for React frontend (supports authorization headers & credentials)
CORS(app, supports_credentials=True)

# Initialize DB on startup
database.init_db()

HTML_DOCS = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HealthPulse Backend API (SQLAlchemy 2.0 ORM)</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px 20px; }
    .container { max-width: 800px; margin: 0 auto; }
    .header { background: #1e293b; padding: 30px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 24px; }
    .status-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(5, 150, 105, 0.2); color: #34d399; border: 1px solid rgba(5, 150, 105, 0.4); padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 700; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; }
    h1 { margin: 16px 0 8px; font-size: 28px; font-weight: 800; }
    p { color: #94a3b8; font-size: 15px; margin: 0; }
    .btn { display: inline-block; background: #059669; color: white; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 700; margin-top: 20px; transition: background 0.15s; }
    .btn:hover { background: #047857; }
    .endpoints-card { background: #1e293b; border-radius: 16px; border: 1px solid #334155; padding: 24px; }
    .endpoint { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid #334155; }
    .endpoint:last-child { border-bottom: none; }
    .method { font-size: 12px; font-weight: 800; padding: 4px 8px; border-radius: 6px; }
    .get { background: rgba(37, 99, 235, 0.2); color: #60a5fa; }
    .post { background: rgba(5, 150, 105, 0.2); color: #34d399; }
    .put { background: rgba(217, 119, 6, 0.2); color: #fbbf24; }
    .delete { background: rgba(225, 29, 72, 0.2); color: #fb7185; }
    .route-link { color: #e2e8f0; font-family: monospace; text-decoration: none; font-size: 14px; }
    .desc { color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="status-badge"><span class="status-dot"></span> SQLAlchemy 2.0 ORM Active</div>
      <h1>HealthPulse Backend API</h1>
      <p>Decoupled Architecture with SQLAlchemy 2.0 ORM, Pydantic v2 DTOs, Fernet Secrets Vault, and WebAuthn Biometrics.</p>
      <a href="http://localhost:5173" class="btn" target="_blank">Open React Frontend (Port 5173) &rarr;</a>
    </div>

    <div class="endpoints-card">
      <h2 style="font-size: 18px; margin-bottom: 16px;">Available REST Endpoints</h2>
      
      <div class="endpoint">
        <div>
          <span class="method post">POST</span>
          <span class="route-link">/api/auth/register</span>
        </div>
        <span class="desc">Register new user account</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method post">POST</span>
          <span class="route-link">/api/auth/login</span>
        </div>
        <span class="desc">Password login & token generation</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method post">POST</span>
          <span class="route-link">/api/auth/webauthn/login/verify</span>
        </div>
        <span class="desc">Biometric / Passkey passwordless sign-in</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method post">POST</span>
          <span class="route-link">/api/upload-scale-photo/async</span>
        </div>
        <span class="desc">Instant async upload with Gemini Flash & EXIF</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method get">GET</span>
          <span class="route-link">/api/entries</span>
        </div>
        <span class="desc">User-isolated weight & step history</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method get">GET</span>
          <span class="route-link">/api/stats</span>
        </div>
        <span class="desc">User statistics, 7d/30d avg & streaks</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_DOCS)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Health Tracker API is running',
        'orm': 'SQLAlchemy 2.0 Declarative Mapped Models',
        'dto_layer': 'Pydantic v2 Contract Validation',
        'secrets_vault': 'Fernet Authenticated AES-128-CBC'
    })

# ==========================================
# AUTHENTICATION & WEBAUTHN ENDPOINTS
# ==========================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        raw_json = request.get_json() or {}
        try:
            req_data = schemas.UserRegisterRequest.model_validate(raw_json)
        except ValidationError as val_err:
            first_err = val_err.errors()[0]
            field = first_err.get('loc', ['field'])[-1]
            return jsonify({'success': False, 'error': f"{field}: {first_err.get('msg')}"}), 400

        existing = database.get_user_by_username(req_data.username)
        if existing:
            return jsonify({'success': False, 'error': f'Username "{req_data.username}" is already taken.'}), 409

        pwd_hash = auth_service.hash_user_password(req_data.password)
        user = database.create_user(req_data.username, pwd_hash)
        if not user:
            return jsonify({'success': False, 'error': 'Failed to create user account.'}), 500

        token = auth_service.create_access_token(user['id'], user['username'])
        user_dto = schemas.UserResponse(id=user['id'], username=user['username'])
        return jsonify({
            'success': True,
            'token': token,
            'user': user_dto.model_dump()
        }), 201

    except Exception as e:
        app.logger.error(f"Error in register: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        raw_json = request.get_json() or {}
        try:
            req_data = schemas.UserLoginRequest.model_validate(raw_json)
        except ValidationError as val_err:
            return jsonify({'success': False, 'error': 'Username and password are required.'}), 400

        user = database.get_user_by_username(req_data.username)
        if not user or not auth_service.verify_user_password(user['password_hash'], req_data.password):
            return jsonify({'success': False, 'error': 'Invalid username or password.'}), 401

        token = auth_service.create_access_token(user['id'], user['username'])
        user_dto = schemas.UserResponse(id=user['id'], username=user['username'])
        return jsonify({
            'success': True,
            'token': token,
            'user': user_dto.model_dump()
        })

    except Exception as e:
        app.logger.error(f"Error in login: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_current_user_profile():
    try:
        user_id = request.current_user['id']
        user = database.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        credentials = database.get_webauthn_credentials_for_user(user_id)
        passkey_dtos = [schemas.WebAuthnPasskeyItem.model_validate(c) for c in credentials]
        profile_dto = schemas.UserProfileResponse(
            id=user['id'],
            username=user['username'],
            created_at=user['created_at'],
            passkeys_count=len(credentials),
            passkeys=passkey_dtos
        )
        return jsonify({
            'success': True,
            'user': profile_dto.model_dump()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- WebAuthn Registration (Passkey Enrollment) ---

@app.route('/api/auth/webauthn/register/options', methods=['POST'])
@login_required
def webauthn_register_options():
    try:
        user_id = request.current_user['id']
        username = request.current_user['username']
        options = auth_service.create_registration_challenge(user_id, username)
        return jsonify({'success': True, 'options': options})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/webauthn/register/verify', methods=['POST'])
@login_required
def webauthn_register_verify():
    try:
        user_id = request.current_user['id']
        data = request.get_json() or {}
        challenge = data.get('challenge')
        credential_id = data.get('credential_id')
        public_key = data.get('public_key')
        nickname = data.get('nickname', 'Biometric Device')

        verified_challenge = auth_service.verify_registration_challenge(challenge)
        if not verified_challenge or verified_challenge.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Invalid or expired WebAuthn challenge.'}), 400

        database.save_webauthn_credential(
            user_id=user_id,
            credential_id=credential_id,
            public_key=public_key,
            nickname=nickname
        )
        return jsonify({'success': True, 'message': 'Passkey / Biometric device successfully enrolled!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- WebAuthn Login (Biometric / Passkey Sign-In) ---

@app.route('/api/auth/webauthn/login/options', methods=['POST'])
def webauthn_login_options():
    try:
        data = request.get_json() or {}
        username = data.get('username')
        user = database.get_user_by_username(username) if username else None
        user_id = user['id'] if user else None
        
        options = auth_service.create_authentication_challenge(user_id=user_id, username=username)
        return jsonify({'success': True, 'options': options})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/webauthn/login/verify', methods=['POST'])
def webauthn_login_verify():
    try:
        data = request.get_json() or {}
        challenge = data.get('challenge')
        credential_id = data.get('credential_id')

        verified_challenge = auth_service.verify_authentication_challenge(challenge)
        if not verified_challenge:
            return jsonify({'success': False, 'error': 'Invalid or expired WebAuthn authentication challenge.'}), 400

        cred = database.get_webauthn_credential_by_id(credential_id)
        if not cred:
            return jsonify({'success': False, 'error': 'Passkey not recognized.'}), 404

        token = auth_service.create_access_token(cred['user_id'], cred['username'])
        user_dto = schemas.UserResponse(id=cred['user_id'], username=cred['username'])
        return jsonify({
            'success': True,
            'token': token,
            'user': user_dto.model_dump()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/webauthn/credentials/<int:cred_id>', methods=['DELETE'])
@login_required
def delete_passkey(cred_id):
    try:
        user_id = request.current_user['id']
        deleted = database.delete_webauthn_credential(cred_id, user_id)
        if not deleted:
            return jsonify({'success': False, 'error': 'Passkey not found'}), 404
        return jsonify({'success': True, 'message': 'Passkey removed.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# ASYNCHRONOUS SCALE PHOTO UPLOAD PIPELINE
# ==========================================

@app.route('/api/upload-scale-photo/async', methods=['POST'])
@login_required
def upload_scale_photo_async():
    try:
        user_id = request.current_user['id']
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo file provided in request (key "photo")'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename uploaded'}), 400

        goals = database.get_goals(user_id) or {}
        api_key = (goals.get('gemini_api_key') or settings.GEMINI_API_KEY).strip()

        suffix = os.path.splitext(file.filename)[1] or '.jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        job_id = database.create_scale_upload_job(user_id)

        # Launch background worker
        ocr_service.start_async_scale_processing(user_id, job_id, tmp_path, api_key=api_key)

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'processing',
            'message': 'Photo uploaded successfully. Processing in background with Gemini Flash Vision.'
        }), 202

    except Exception as e:
        app.logger.error(f"Error in upload_scale_photo_async: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-scale-photo/status', methods=['GET'])
@login_required
def get_scale_upload_status():
    try:
        user_id = request.current_user['id']
        jobs = database.get_active_scale_upload_jobs(user_id)
        job_dtos = [schemas.ScaleUploadJobItem.model_validate(j) for j in jobs]
        res = schemas.ScaleUploadStatusResponse(jobs=job_dtos)
        return jsonify(res.model_dump())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-scale-photo/jobs/<int:job_id>/dismiss', methods=['POST'])
@login_required
def dismiss_scale_upload_job(job_id):
    try:
        user_id = request.current_user['id']
        database.dismiss_scale_upload_job(job_id, user_id)
        return jsonify({'success': True, 'message': 'Job dismissed.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# USER-SCOPED ENTRIES & STATS ENDPOINTS
# ==========================================

@app.route('/api/entries', methods=['GET'])
@login_required
def get_entries():
    try:
        user_id = request.current_user['id']
        entries = database.get_all_entries(user_id)
        entry_dtos = [schemas.EntryResponse.model_validate(e) for e in entries]
        response = schemas.EntryListResponse(entries=entry_dtos)
        return jsonify(response.model_dump())
    except Exception as e:
        app.logger.error(f"Error in get_entries: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
@login_required
def add_entry():
    try:
        user_id = request.current_user['id']
        raw_json = request.get_json() or {}
        try:
            req_data = schemas.EntryCreateRequest.model_validate(raw_json)
        except ValidationError as val_err:
            first_err = val_err.errors()[0]
            field = first_err.get('loc', ['field'])[-1]
            return jsonify({'success': False, 'error': f"{field}: {first_err.get('msg')}"}), 400

        entry = database.upsert_entry(
            user_id=user_id,
            date_str=req_data.date,
            weight=req_data.weight,
            steps=req_data.steps,
            notes=req_data.notes or ""
        )
        entry_dto = schemas.EntryResponse.model_validate(entry)
        return jsonify({'success': True, 'entry': entry_dto.model_dump()}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
@login_required
def update_entry(entry_id):
    try:
        user_id = request.current_user['id']
        raw_json = request.get_json() or {}
        try:
            req_data = schemas.EntryUpdateRequest.model_validate(raw_json)
        except ValidationError as val_err:
            first_err = val_err.errors()[0]
            field = first_err.get('loc', ['field'])[-1]
            return jsonify({'success': False, 'error': f"{field}: {first_err.get('msg')}"}), 400

        entry = database.update_entry(
            user_id=user_id,
            entry_id=entry_id,
            date_str=req_data.date,
            weight=req_data.weight,
            steps=req_data.steps,
            notes=req_data.notes or ""
        )
        if not entry:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        
        entry_dto = schemas.EntryResponse.model_validate(entry)
        return jsonify({'success': True, 'entry': entry_dto.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_entry(entry_id):
    try:
        user_id = request.current_user['id']
        deleted = database.delete_entry(user_id, entry_id)
        if not deleted:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    try:
        user_id = request.current_user['id']
        goals = database.get_goals(user_id)
        
        user_key = goals.get('gemini_api_key', '')
        effective_key = user_key or settings.GEMINI_API_KEY
        has_api_key = bool(effective_key)

        goal_dto = schemas.GoalResponse(
            id=goals['id'],
            user_id=goals['user_id'],
            daily_steps_goal=goals['daily_steps_goal'],
            target_weight=goals['target_weight'],
            starting_weight=goals['starting_weight'],
            weight_unit=goals['weight_unit'],
            has_gemini_api_key=has_api_key,
            gemini_api_key_masked=secrets_vault.mask_secret(effective_key),
            gemini_api_key=user_key,
            updated_at=goals.get('updated_at')
        )
        return jsonify({'success': True, 'goals': goal_dto.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/goals', methods=['POST'])
@login_required
def update_goals():
    try:
        user_id = request.current_user['id']
        raw_json = request.get_json() or {}
        try:
            req_data = schemas.GoalUpdateRequest.model_validate(raw_json)
        except ValidationError as val_err:
            first_err = val_err.errors()[0]
            field = first_err.get('loc', ['field'])[-1]
            return jsonify({'success': False, 'error': f"{field}: {first_err.get('msg')}"}), 400

        goals = database.update_goals(
            user_id=user_id,
            daily_steps_goal=req_data.daily_steps_goal,
            target_weight=req_data.target_weight,
            starting_weight=req_data.starting_weight,
            weight_unit=req_data.weight_unit,
            gemini_api_key=req_data.gemini_api_key or ""
        )
        
        user_key = goals.get('gemini_api_key', '')
        effective_key = user_key or settings.GEMINI_API_KEY

        goal_dto = schemas.GoalResponse(
            id=goals['id'],
            user_id=goals['user_id'],
            daily_steps_goal=goals['daily_steps_goal'],
            target_weight=goals['target_weight'],
            starting_weight=goals['starting_weight'],
            weight_unit=goals['weight_unit'],
            has_gemini_api_key=bool(effective_key),
            gemini_api_key_masked=secrets_vault.mask_secret(effective_key),
            gemini_api_key=user_key,
            updated_at=goals.get('updated_at')
        )
        return jsonify({'success': True, 'goals': goal_dto.model_dump()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        user_id = request.current_user['id']
        entries = database.get_all_entries(user_id)
        goals = database.get_goals(user_id) or {}
        
        step_goal = int(goals.get('daily_steps_goal') or 10000)
        target_weight = float(goals.get('target_weight') or 165.0)
        starting_weight = float(goals.get('starting_weight') or 185.0)
        unit = str(goals.get('weight_unit') or 'lbs')

        if not entries:
            stats_dto = schemas.StatsData(
                total_days_logged=0,
                latest_weight=None,
                starting_weight=starting_weight,
                target_weight=target_weight,
                weight_change=0.0,
                weight_unit=unit,
                progress_percent=0.0,
                today_steps=0,
                today_weight=None,
                avg_steps_7d=0,
                avg_steps_30d=0,
                best_step_day=0,
                total_steps=0,
                current_step_streak=0,
                days_goal_met=0
            )
            return jsonify(schemas.StatsResponse(stats=stats_dto).model_dump())

        weight_entries = [e for e in entries if e.get('weight') is not None]
        latest_weight = float(weight_entries[0]['weight']) if weight_entries else None
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_entry = next((e for e in entries if e['date'] == today_str), None)
        today_steps = int(today_entry['steps']) if today_entry and today_entry.get('steps') is not None else 0
        today_weight = float(today_entry['weight']) if today_entry and today_entry.get('weight') is not None else None

        weight_change = 0.0
        progress_pct = 0.0
        if latest_weight is not None and starting_weight is not None:
            weight_change = round(latest_weight - starting_weight, 1)
            total_needed = starting_weight - target_weight
            if total_needed != 0:
                actual_lost = starting_weight - latest_weight
                progress_pct = max(0.0, min(100.0, round((actual_lost / total_needed) * 100, 1)))

        step_entries = [e for e in entries if e.get('steps') is not None]
        total_steps = sum(int(e['steps']) for e in step_entries)
        best_step_day = max((int(e['steps']) for e in step_entries), default=0)
        days_goal_met = sum(1 for e in step_entries if int(e['steps']) >= step_goal)

        now_dt = datetime.now()
        seven_days_ago = (now_dt - timedelta(days=7)).strftime('%Y-%m-%d')
        thirty_days_ago = (now_dt - timedelta(days=30)).strftime('%Y-%m-%d')

        steps_7d = [int(e['steps']) for e in step_entries if e['date'] >= seven_days_ago]
        avg_7d = round(sum(steps_7d) / len(steps_7d)) if steps_7d else 0

        steps_30d = [int(e['steps']) for e in step_entries if e['date'] >= thirty_days_ago]
        avg_30d = round(sum(steps_30d) / len(steps_30d)) if steps_30d else 0

        streak = 0
        sorted_asc = sorted(step_entries, key=lambda x: x['date'], reverse=True)
        for e in sorted_asc:
            if int(e['steps']) >= step_goal:
                streak += 1
            else:
                break

        stats_dto = schemas.StatsData(
            total_days_logged=len(entries),
            latest_weight=latest_weight,
            starting_weight=starting_weight,
            target_weight=target_weight,
            weight_change=weight_change,
            weight_unit=unit,
            progress_percent=progress_pct,
            today_steps=today_steps,
            today_weight=today_weight,
            avg_steps_7d=avg_7d,
            avg_steps_30d=avg_30d,
            best_step_day=best_step_day,
            total_steps=total_steps,
            current_step_streak=streak,
            days_goal_met=days_goal_met
        )
        return jsonify(schemas.StatsResponse(stats=stats_dto).model_dump())
    except Exception as e:
        app.logger.error(f"Error in get_stats: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', settings.PORT))
    host = os.environ.get('HOST', settings.HOST)
    use_ssl = settings.ENABLE_SSL or '--ssl' in sys.argv or os.environ.get('USE_SSL', '0') == '1'
    ssl_context = None
    if use_ssl:
        ssl_cert, ssl_key = ssl_manager.get_ssl_cert_paths()
        ssl_context = (ssl_cert, ssl_key) if ssl_cert and ssl_key else None

    if ssl_context:
        print(f"🔒 Starting HealthPulse HTTPS Server on https://{host}:{port} (Cert: {ssl_cert})")
        app.run(host=host, port=port, ssl_context=ssl_context, debug=False, use_reloader=False)
    else:
        print(f"🚀 Starting HealthPulse HTTP Server on http://{host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False)
