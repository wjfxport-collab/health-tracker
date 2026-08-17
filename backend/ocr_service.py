import os
import re
import threading
from datetime import datetime
from PIL import Image
import piexif
import gemini_service
import database

def extract_exif_timestamp(img_path):
    """
    Extract original capture date and time from EXIF metadata.
    Returns (date_str_YYYY_MM_DD, formatted_time_str, raw_exif_datetime) or (None, None, None).
    """
    try:
        image = Image.open(img_path)
        exif_data = image.getexif()
        datetime_str = None
        
        if exif_data:
            exif_ifd = exif_data.get_ifd(0x8769)
            if exif_ifd:
                datetime_str = exif_ifd.get(36867) or exif_ifd.get(36868)
            if not datetime_str:
                datetime_str = exif_data.get(306)

        if not datetime_str:
            try:
                exif_dict = piexif.load(img_path)
                exif_ifd = exif_dict.get('Exif', {})
                dt_bytes = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal) or exif_ifd.get(piexif.ExifIFD.DateTimeDigitized)
                if not dt_bytes and '0th' in exif_dict:
                    dt_bytes = exif_dict['0th'].get(piexif.ImageIFD.DateTime)
                if dt_bytes and isinstance(dt_bytes, bytes):
                    datetime_str = dt_bytes.decode('utf-8', errors='ignore')
            except Exception:
                pass

        if datetime_str:
            dt_match = re.search(r'(\d{4})[:\-](\d{2})[:\-](\d{2})\s+(\d{2}):(\d{2})(?::(\d{2}))?', str(datetime_str))
            if dt_match:
                year, month, day, hour, minute, second = dt_match.groups()
                date_formatted = f"{year}-{month}-{day}"
                
                h_int = int(hour)
                am_pm = "AM" if h_int < 12 else "PM"
                h_12 = h_int % 12 or 12
                time_formatted = f"{h_12}:{minute} {am_pm}"
                
                return date_formatted, time_formatted, datetime_str

    except Exception as e:
        print(f"Warning: could not read EXIF data: {e}")

    return None, None, None

def _run_async_worker(user_id, job_id, tmp_path, api_key):
    """
    Background worker thread: parses scale photo with Gemini Flash & updates DB.
    """
    try:
        # 1. Extract EXIF timestamp
        exif_date, exif_time, raw_dt = extract_exif_timestamp(tmp_path)
        date_to_use = exif_date if exif_date else datetime.now().strftime('%Y-%m-%d')
        time_to_use = exif_time if exif_time else datetime.now().strftime('%I:%M %p')

        # 2. Call Google Gemini Flash Vision
        gemini_res = gemini_service.parse_scale_with_gemini(tmp_path, api_key=api_key)

        if gemini_res.get('success') and gemini_res.get('weight'):
            weight_val = float(gemini_res['weight'])
            unit_val = gemini_res.get('unit', 'lbs')
            notes_val = str(gemini_res.get('notes') or f"Photo scan ({time_to_use})")

            # Save entry for user
            database.upsert_entry(
                user_id,
                date_to_use,
                weight=weight_val,
                notes=notes_val
            )

            # Update job status to completed
            database.update_scale_upload_job(
                job_id,
                status='completed',
                weight=weight_val,
                unit=unit_val,
                date=date_to_use,
                time=time_to_use,
                notes=notes_val
            )
            print(f"[Async Job {job_id}] Successfully parsed {weight_val} {unit_val} on {date_to_use}")
        else:
            # Mark job failed so the UI displays the warning banner
            error_msg = gemini_res.get('error') or "Scale display numbers were unreadable or obscured by reflections."
            database.update_scale_upload_job(
                job_id,
                status='failed',
                date=date_to_use,
                time=time_to_use,
                error=error_msg
            )
            print(f"[Async Job {job_id}] Failed: {error_msg}")

    except Exception as e:
        print(f"[Async Job {job_id}] Error in worker: {e}")
        database.update_scale_upload_job(
            job_id,
            status='failed',
            error=f"Processing error: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

def start_async_scale_processing(user_id, job_id, tmp_path, api_key=None):
    """
    Launch non-blocking background thread to process the scale photo.
    """
    t = threading.Thread(
        target=_run_async_worker,
        args=(user_id, job_id, tmp_path, api_key),
        daemon=True
    )
    t.start()
    return job_id
