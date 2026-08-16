from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import tempfile
import traceback
import database
import ocr_service
import local_llm_service

app = Flask(__name__)
# Enable CORS for React frontend (running on localhost:5173 or other remote IPs/ports)
CORS(app)

# Initialize DB on startup
database.init_db()

HTML_DOCS = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HealthPulse Backend API</title>
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
    .route-link:hover { color: #38bdf8; text-decoration: underline; }
    .desc { color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="status-badge"><span class="status-dot"></span> API Server Online</div>
      <h1>HealthPulse Backend API</h1>
      <p>Flask REST API for weight tracking, step metrics, Gemini & Local Mac Gemma 4 12B Vision OCR.</p>
      <a href="http://localhost:5173" class="btn" target="_blank">Open React Frontend (Port 5173) &rarr;</a>
    </div>

    <div class="endpoints-card">
      <h2 style="font-size: 18px; margin-bottom: 16px;">Available REST Endpoints</h2>
      
      <div class="endpoint">
        <div>
          <span class="method get">GET</span>
          <a class="route-link" href="/api/health" target="_blank">/api/health</a>
        </div>
        <span class="desc">Health check status</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method post">POST</span>
          <span class="route-link">/api/upload-scale-photo</span>
        </div>
        <span class="desc">Upload scale photo (Gemini, Local Gemma, or Tesseract)</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method post">POST</span>
          <span class="route-link">/api/test-local-llm</span>
        </div>
        <span class="desc">Test connection to Mac Gemma server (192.168.4.27)</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method get">GET</span>
          <a class="route-link" href="/api/entries" target="_blank">/api/entries</a>
        </div>
        <span class="desc">Fetch all logged entries</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method get">GET</span>
          <a class="route-link" href="/api/stats" target="_blank">/api/stats</a>
        </div>
        <span class="desc">7-day avg, streaks & weight progress</span>
      </div>

      <div class="endpoint">
        <div>
          <span class="method get">GET</span>
          <a class="route-link" href="/api/goals" target="_blank">/api/goals</a>
        </div>
        <span class="desc">User step/weight targets & AI settings</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'status': 'ok',
            'message': 'HealthPulse Backend API is running',
            'endpoints': [
                '/api/health',
                '/api/upload-scale-photo',
                '/api/test-local-llm',
                '/api/entries',
                '/api/stats',
                '/api/goals'
            ]
        })
    return render_template_string(HTML_DOCS)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Health Tracker API is running'})

@app.route('/api/test-local-llm', methods=['POST'])
def test_local_llm():
    """
    Test connectivity to the local Mac LLM server.
    """
    try:
        data = request.get_json() or {}
        server_url = data.get('server_url', 'http://192.168.4.27:11434')
        success, msg = local_llm_service.test_connection(server_url)
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error testing server: {str(e)}'}), 500

@app.route('/api/upload-scale-photo', methods=['POST'])
def upload_scale_photo():
    """
    Handle scale photo upload:
    - Extracts EXIF timestamp.
    - Routes to Gemini Vision, Local Mac Gemma 4 12B, or Local Tesseract OCR.
    - Saves to database if save_immediately is true.
    """
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo file provided in request (key "photo")'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename uploaded'}), 400

        # Retrieve AI settings from DB
        goals = database.get_goals() or {}
        api_key = goals.get('gemini_api_key') or os.environ.get('GEMINI_API_KEY', '')
        engine = goals.get('ocr_engine') or 'gemini'
        local_llm_url = goals.get('local_llm_url') or 'http://192.168.4.27:11434'
        local_llm_model = goals.get('local_llm_model') or 'gemma-4-12b'

        # Allow request overrides
        if request.form.get('api_key'):
            api_key = request.form.get('api_key')
        if request.form.get('engine'):
            engine = request.form.get('engine')
        if request.form.get('local_llm_url'):
            local_llm_url = request.form.get('local_llm_url')
        if request.form.get('local_llm_model'):
            local_llm_model = request.form.get('local_llm_model')

        suffix = os.path.splitext(file.filename)[1] or '.jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        try:
            result = ocr_service.process_scale_photo(
                tmp_path,
                api_key=api_key,
                preferred_engine=engine,
                local_llm_url=local_llm_url,
                local_llm_model=local_llm_model
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        save_immediately = request.form.get('save_immediately', 'false').lower() in ('true', '1')
        if save_immediately and result.get('success') and result.get('weight'):
            date_to_save = result.get('date') or datetime.now().strftime('%Y-%m-%d')
            weight_val = result.get('weight')
            steps_val = int(request.form.get('steps')) if request.form.get('steps') else None
            notes_val = str(request.form.get('notes', result.get('notes') or 'Logged via Scale Photo Vision')).strip()

            saved_entry = database.upsert_entry(
                date_to_save,
                weight=weight_val,
                steps=steps_val,
                notes=notes_val
            )
            result['saved_entry'] = saved_entry
            result['saved_to_db'] = True

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error in upload_scale_photo: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Failed to process photo: {str(e)}',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'exif_found': False
        }), 500

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        entries = database.get_all_entries()
        return jsonify({'success': True, 'entries': entries})
    except Exception as e:
        app.logger.error(f"Error in get_entries: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
def add_entry():
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required (YYYY-MM-DD)'}), 400
        
        weight = float(data['weight']) if data.get('weight') not in (None, '') else None
        steps = int(data['steps']) if data.get('steps') not in (None, '') else None
        notes = str(data.get('notes', '')).strip()

        entry = database.upsert_entry(date_str, weight=weight, steps=steps, notes=notes)
        return jsonify({'success': True, 'entry': entry}), 201
    except ValueError as ve:
        return jsonify({'success': False, 'error': f'Invalid number format: {str(ve)}'}), 400
    except Exception as e:
        app.logger.error(f"Error in add_entry: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required'}), 400
            
        weight = float(data['weight']) if data.get('weight') not in (None, '') else None
        steps = int(data['steps']) if data.get('steps') not in (None, '') else None
        notes = str(data.get('notes', '')).strip()

        entry = database.update_entry(entry_id, date_str, weight=weight, steps=steps, notes=notes)
        if not entry:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        return jsonify({'success': True, 'entry': entry})
    except Exception as e:
        app.logger.error(f"Error in update_entry: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    try:
        deleted = database.delete_entry(entry_id)
        if not deleted:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error in delete_entry: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/goals', methods=['GET'])
def get_goals():
    try:
        goals = database.get_goals()
        has_api_key = bool(goals.get('gemini_api_key') or os.environ.get('GEMINI_API_KEY'))
        response_goals = dict(goals)
        response_goals['has_gemini_api_key'] = has_api_key
        return jsonify({'success': True, 'goals': response_goals})
    except Exception as e:
        app.logger.error(f"Error in get_goals: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/goals', methods=['POST'])
def update_goals():
    try:
        data = request.get_json() or {}
        daily_steps_goal = int(data.get('daily_steps_goal', 10000))
        target_weight = float(data.get('target_weight', 165.0))
        starting_weight = float(data.get('starting_weight', 185.0))
        weight_unit = str(data.get('weight_unit', 'lbs')).strip()
        gemini_api_key = str(data.get('gemini_api_key', '')).strip()
        ocr_engine = str(data.get('ocr_engine', 'gemini')).strip()
        local_llm_url = str(data.get('local_llm_url', 'http://192.168.4.27:11434')).strip()
        local_llm_model = str(data.get('local_llm_model', 'gemma-4-12b')).strip()

        goals = database.update_goals(
            daily_steps_goal,
            target_weight,
            starting_weight,
            weight_unit,
            gemini_api_key=gemini_api_key,
            ocr_engine=ocr_engine,
            local_llm_url=local_llm_url,
            local_llm_model=local_llm_model
        )
        response_goals = dict(goals)
        response_goals['has_gemini_api_key'] = bool(gemini_api_key or os.environ.get('GEMINI_API_KEY'))
        return jsonify({'success': True, 'goals': response_goals})
    except Exception as e:
        app.logger.error(f"Error in update_goals: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        entries = database.get_all_entries()
        goals = database.get_goals() or {}
        
        step_goal = int(goals.get('daily_steps_goal') or 10000)
        target_weight = float(goals.get('target_weight') or 165.0)
        starting_weight = float(goals.get('starting_weight') or 185.0)
        unit = str(goals.get('weight_unit') or 'lbs')

        if not entries:
            return jsonify({
                'success': True,
                'stats': {
                    'total_days_logged': 0,
                    'latest_weight': None,
                    'starting_weight': starting_weight,
                    'target_weight': target_weight,
                    'weight_change': 0.0,
                    'weight_unit': unit,
                    'progress_percent': 0,
                    'today_steps': 0,
                    'today_weight': None,
                    'avg_steps_7d': 0,
                    'avg_steps_30d': 0,
                    'best_step_day': 0,
                    'total_steps': 0,
                    'current_step_streak': 0,
                    'days_goal_met': 0
                }
            })

        weight_entries = [e for e in entries if e.get('weight') is not None]
        latest_weight = float(weight_entries[0]['weight']) if weight_entries else None
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_entry = next((e for e in entries if e['date'] == today_str), None)
        today_steps = int(today_entry['steps']) if today_entry and today_entry.get('steps') is not None else 0
        today_weight = float(today_entry['weight']) if today_entry and today_entry.get('weight') is not None else None

        weight_change = 0.0
        progress_pct = 0
        if latest_weight is not None and starting_weight is not None:
            weight_change = round(latest_weight - starting_weight, 1)
            total_needed = starting_weight - target_weight
            if total_needed != 0:
                actual_lost = starting_weight - latest_weight
                progress_pct = max(0, min(100, round((actual_lost / total_needed) * 100, 1)))

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

        return jsonify({
            'success': True,
            'stats': {
                'total_days_logged': len(entries),
                'latest_weight': latest_weight,
                'starting_weight': starting_weight,
                'target_weight': target_weight,
                'weight_change': weight_change,
                'weight_unit': unit,
                'progress_percent': progress_pct,
                'today_steps': today_steps,
                'today_weight': today_weight,
                'avg_steps_7d': avg_7d,
                'avg_steps_30d': avg_30d,
                'best_step_day': best_step_day,
                'total_steps': total_steps,
                'current_step_streak': streak,
                'days_goal_met': days_goal_met
            }
        })
    except Exception as e:
        app.logger.error(f"Error in get_stats: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': f'Endpoint not found: {request.path}'}), 404
    return render_template_string(HTML_DOCS), 200

@app.errorhandler(500)
def handle_500(e):
    return jsonify({'success': False, 'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    print("Starting Health Tracker Flask API on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
