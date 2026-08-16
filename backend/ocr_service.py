import os
import re
from datetime import datetime
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
import piexif
import gemini_service
import local_llm_service

# Configure user-space Tesseract paths
TESS_BIN = '/home/wjf42/.gemini/antigravity/scratch/tools/tesseract/usr/bin/tesseract'
if os.path.exists(TESS_BIN):
    pytesseract.pytesseract.tesseract_cmd = TESS_BIN
    os.environ['LD_LIBRARY_PATH'] = '/home/wjf42/.gemini/antigravity/scratch/tools/tesseract/usr/lib/x86_64-linux-gnu:' + os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['TESSDATA_PREFIX'] = '/home/wjf42/.gemini/antigravity/scratch/tools/tesseract/usr/share/tesseract-ocr/5/tessdata'

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

def detect_lcd_bounding_box(img):
    try:
        w, h = img.size
        small_w = 200
        small_h = int(h * (200.0 / w))
        small = img.resize((small_w, small_h), Image.Resampling.BILINEAR)
        
        rgb_img = small.convert('RGB')
        r, g, b = rgb_img.split()
        
        r_vals = list(r.tobytes())
        g_vals = list(g.tobytes())
        b_vals = list(b.tobytes())
        
        lcd_pixels = []
        for i in range(len(r_vals)):
            rv, gv, bv = r_vals[i], g_vals[i], b_vals[i]
            is_aqua = (gv > 70 and bv > 70 and ((gv + bv) // 2 - rv) > 20)
            is_blue = (bv > 90 and bv - rv > 30 and bv - gv > 15)
            is_green = (gv > 90 and gv - rv > 30)

            if is_aqua or is_blue or is_green:
                lcd_pixels.append(i)

        if len(lcd_pixels) > (small_w * small_h * 0.01):
            xs = [idx % small_w for idx in lcd_pixels]
            ys = [idx // small_w for idx in lcd_pixels]
            
            scale_x = w / float(small_w)
            scale_y = h / float(small_h)
            
            min_x = max(0, int((min(xs) - 8) * scale_x))
            max_x = min(w, int((max(xs) + 8) * scale_x))
            min_y = max(0, int((min(ys) - 8) * scale_y))
            max_y = min(h, int((max(ys) + 8) * scale_y))
            
            if (max_x - min_x) > 60 and (max_y - min_y) > 30:
                return (min_x, min_y, max_x, max_y)
    except Exception:
        pass

    return None

def parse_weight_candidates(raw_text):
    candidates = []
    if not raw_text:
        return candidates

    cleaned = raw_text.replace(',', '.').replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1').replace('S', '5').replace('s', '5').replace('B', '8')
    
    decimal_matches = re.finditer(r'(\d{2,3}\.\d{1,2})\s*(lbs?|kg)?', cleaned, re.IGNORECASE)
    for m in decimal_matches:
        try:
            val = float(m.group(1))
            unit_str = m.group(2).lower() if m.group(2) else 'lbs'
            if 30.0 <= val <= 500.0:
                score = 2.5
                if m.group(2):
                    score += 0.5
                candidates.append((val, unit_str, score))
        except ValueError:
            pass

    whole_with_unit = re.finditer(r'(\d{2,3})\s*(lbs?|kg)', cleaned, re.IGNORECASE)
    for m in whole_with_unit:
        try:
            val = float(m.group(1))
            unit_str = m.group(2).lower()
            if 30.0 <= val <= 500.0:
                candidates.append((val, unit_str, 1.8))
        except ValueError:
            pass

    four_digits = re.finditer(r'(?<!\d)(\d{4})(?!\d)\s*(lbs?|kg)?', cleaned, re.IGNORECASE)
    for m in four_digits:
        try:
            raw_int = int(m.group(1))
            if 1000 <= raw_int <= 4500:
                val = round(raw_int / 10.0, 1)
                unit_str = m.group(2).lower() if m.group(2) else 'lbs'
                candidates.append((val, unit_str, 1.5))
        except ValueError:
            pass

    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates

def generate_preprocessed_variants(img):
    variants = []
    w, h = img.size
    
    lcd_box = detect_lcd_bounding_box(img)
    crop_regions = []
    if lcd_box:
        crop_regions.append(('detected_lcd', img.crop(lcd_box)))
    
    upper_box = (int(w * 0.1), int(h * 0.04), int(w * 0.9), int(h * 0.65))
    crop_regions.append(('upper_center', img.crop(upper_box)))
    crop_regions.append(('full', img))

    for region_name, r_img in crop_regions:
        rw, rh = r_img.size
        if rw < 30 or rh < 20:
            continue
            
        target_w = max(600, min(1200, rw * 3))
        scale_factor = target_w / float(rw)
        target_h = int(rh * scale_factor)
        
        scaled = r_img.resize((target_w, target_h), Image.Resampling.BICUBIC)
        padded = ImageOps.expand(scaled, border=35, fill=(255, 255, 255))
        
        r_ch, g_ch, b_ch = padded.split()
        
        contrast_r = ImageEnhance.Contrast(r_ch).enhance(3.0)
        dilated_r = contrast_r.filter(ImageFilter.MinFilter(3))
        for thresh_val in [90, 115, 140, 165]:
            bin_r = dilated_r.point(lambda p: 255 if p > thresh_val else 0)
            variants.append((f"{region_name}_red_thresh_{thresh_val}", bin_r))
        
        gray = ImageOps.grayscale(padded)
        contrast_g = ImageEnhance.Contrast(gray).enhance(2.8)
        dilated_g = contrast_g.filter(ImageFilter.MinFilter(3))
        for thresh_val in [100, 130, 160]:
            bin_g = dilated_g.point(lambda p: 255 if p > thresh_val else 0)
            variants.append((f"{region_name}_gray_thresh_{thresh_val}", bin_g))

        inv = ImageOps.invert(contrast_g)
        dilated_inv = inv.filter(ImageFilter.MinFilter(3))
        for thresh_val in [100, 140]:
            bin_inv = dilated_inv.point(lambda p: 255 if p > thresh_val else 0)
            variants.append((f"{region_name}_inv_thresh_{thresh_val}", bin_inv))

    return variants

def run_local_ocr_fallback(img):
    variants = generate_preprocessed_variants(img)
    all_raw_text = []
    all_candidates = []
    psm_list = [6, 7, 8, 11]
    
    for var_name, v_img in variants:
        for psm in psm_list:
            cfg = f'--psm {psm} -c tessedit_char_whitelist=0123456789.lbskgLBSKG'
            try:
                text = pytesseract.image_to_string(v_img, config=cfg).strip()
                if text:
                    all_raw_text.append(text)
                    candidates = parse_weight_candidates(text)
                    all_candidates.extend(candidates)
                    if candidates and candidates[0][2] >= 2.5:
                        break
            except Exception:
                pass
        if all_candidates and all_candidates[0][2] >= 2.5:
            break

    if all_candidates:
        all_candidates.sort(key=lambda x: x[2], reverse=True)
        best_weight, best_unit, score = all_candidates[0]
        unique_snippets = list(dict.fromkeys(all_raw_text))[:4]
        return {
            'success': True,
            'weight': best_weight,
            'unit': best_unit,
            'confidence': round(min(1.0, score / 2.5) * 100),
            'raw_text': " | ".join(unique_snippets),
            'notes': f'Detected {best_weight} {best_unit} via local OCR',
            'engine': 'local-tesseract'
        }
    else:
        unique_snippets = list(dict.fromkeys(all_raw_text))[:3]
        return {
            'success': False,
            'error': 'Could not clearly read scale display numbers via local OCR. Try entering manually.',
            'raw_text': " | ".join(unique_snippets) if unique_snippets else "No digits detected",
            'engine': 'local-tesseract'
        }

def process_scale_photo(img_path, api_key=None, preferred_engine='gemini', local_llm_url='http://192.168.4.27:11434', local_llm_model='gemma-4-12b'):
    """
    Tri-Engine Vision & OCR pipeline:
    1. Extract EXIF timestamp (creation date & time).
    2. Engine Option A: 'local_llm' -> Local Mac Gemma 4 12B Vision Server (192.168.4.27).
    3. Engine Option B: 'gemini' -> Google Gemini Vision (Cloud).
    4. Engine Option C: 'local' (or automatic fallback) -> Local Tesseract OCR.
    5. Merge vision output with local camera EXIF timestamp.
    """
    exif_date, exif_time, raw_dt = extract_exif_timestamp(img_path)
    date_to_use = exif_date if exif_date else datetime.now().strftime('%Y-%m-%d')
    time_to_use = exif_time if exif_time else datetime.now().strftime('%I:%M %p')
    exif_found = exif_date is not None

    effective_key = (api_key or os.environ.get('GEMINI_API_KEY', '')).strip()

    # --- Option A: Local Mac Gemma 4 12B Vision Server ---
    if preferred_engine == 'local_llm':
        print(f"Submitting scale photo to Local Mac Gemma server at {local_llm_url} (model {local_llm_model})...")
        local_llm_res = local_llm_service.parse_scale_with_local_llm(
            img_path,
            server_url=local_llm_url,
            model_name=local_llm_model
        )
        if local_llm_res.get('success'):
            return {
                'success': True,
                'weight': local_llm_res.get('weight'),
                'unit': local_llm_res.get('unit', 'lbs'),
                'date': date_to_use,
                'time': time_to_use,
                'exif_found': exif_found,
                'confidence': local_llm_res.get('confidence', 95),
                'raw_text': local_llm_res.get('raw_text', ''),
                'notes': local_llm_res.get('notes', f'Parsed by Local Gemma ({local_llm_model}) on Mac'),
                'engine': local_llm_res.get('engine', f'local-gemma-12b ({local_llm_url})'),
                'message': f"Successfully parsed {local_llm_res.get('weight')} {local_llm_res.get('unit', 'lbs')} with Local Mac Gemma."
            }
        else:
            print(f"Local Mac LLM note: {local_llm_res.get('error')}. Falling back to local OCR...")

    # --- Option B: Google Gemini Cloud Vision ---
    elif preferred_engine == 'gemini' and effective_key:
        print("Using Google Gemini Vision for scale photo parsing...")
        gemini_res = gemini_service.parse_scale_with_gemini(img_path, api_key=effective_key)
        
        if gemini_res.get('success'):
            return {
                'success': True,
                'weight': gemini_res.get('weight'),
                'unit': gemini_res.get('unit', 'lbs'),
                'date': date_to_use,
                'time': time_to_use,
                'exif_found': exif_found,
                'confidence': gemini_res.get('confidence', 98),
                'raw_text': gemini_res.get('raw_text', ''),
                'notes': gemini_res.get('notes', 'Parsed by Gemini Vision'),
                'engine': gemini_res.get('engine', 'gemini-flash-latest'),
                'message': f"Successfully parsed {gemini_res.get('weight')} {gemini_res.get('unit', 'lbs')} with Gemini Vision."
            }
        else:
            print(f"Gemini Vision error: {gemini_res.get('error')}. Falling back to local OCR...")

    # --- Option C: Local Tesseract Fallback ---
    try:
        img = Image.open(img_path)
        img = ImageOps.exif_transpose(img)
        if img.mode != 'RGB':
            img = img.convert('RGB')
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to open image: {str(e)}',
            'date': date_to_use,
            'time': time_to_use,
            'exif_found': exif_found,
            'engine': 'local-tesseract'
        }

    local_res = run_local_ocr_fallback(img)
    return {
        'success': local_res.get('success', False),
        'weight': local_res.get('weight'),
        'unit': local_res.get('unit', 'lbs'),
        'date': date_to_use,
        'time': time_to_use,
        'exif_found': exif_found,
        'confidence': local_res.get('confidence', 0),
        'raw_text': local_res.get('raw_text', ''),
        'notes': local_res.get('notes', ''),
        'error': local_res.get('error'),
        'engine': local_res.get('engine', 'local-tesseract'),
        'message': f"Detected {local_res.get('weight')} {local_res.get('unit', 'lbs')} with Local OCR." if local_res.get('success') else None
    }
