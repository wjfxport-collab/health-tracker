import os
import json
import base64
from PIL import Image, ImageOps
import io
from google import genai
from google.genai import types
from config import settings

# Priority active Gemini Flash Vision models
FLASH_VISION_MODELS = [
    'gemini-flash-latest',
    'gemini-2.5-flash-lite',
    'gemini-3-flash-preview',
    'gemini-pro-latest'
]

def parse_scale_with_gemini(img_path, api_key=None):
    """
    Submit bathroom scale photo to Google Gemini Flash Vision for high-precision parsing.
    """
    key = (api_key or settings.GEMINI_API_KEY).strip()
    if not key:
        return {
            'success': False,
            'error': 'No Gemini API Key configured. Please add your key in Settings or .env file.',
            'engine': 'none'
        }

    try:
        # 1. Open and optimize image
        img = Image.open(img_path)
        img = ImageOps.exif_transpose(img) # Auto-rotate based on EXIF
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        max_dim = 1600
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=88)
        img_bytes = img_byte_arr.getvalue()

        # 2. Configure Gemini Client
        client = genai.Client(api_key=key)

        prompt = """
You are an expert computer vision model specialized in reading digital bathroom scales.
Examine this photo of a bathroom scale display carefully.

Your tasks:
1. Locate the primary digital numeric weight reading on the LCD/LED screen (even if 7-segment digital font, aqua/blue backlight, or has light reflections).
2. Look specifically for the exact decimal numbers (e.g. 208.4, 175.2, 78.6, 180.0). Pay close attention to distinguish between '0', '2', '3', and '8' on 7-segment displays.
3. Identify the unit displayed ('lbs', 'lb', 'kg', 'st') if visible; default to 'lbs' if not explicitly stated.
4. Determine if the weight number is legible.

Respond ONLY with a JSON object in this exact schema:
{
  "legible": true,
  "weight": 208.4,
  "unit": "lbs",
  "confidence": 98,
  "notes": "Aqua LCD display reading 208.4 lbs"
}
"""

        last_error = None
        for model_name in FLASH_VISION_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=img_bytes,
                            mime_type='image/jpeg'
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )

                resp_text = response.text.strip()
                parsed = json.loads(resp_text)

                weight_val = parsed.get('weight')
                if weight_val is not None:
                    weight_val = float(weight_val)

                is_legible = bool(parsed.get('legible', False)) and (weight_val is not None)

                return {
                    'success': is_legible,
                    'weight': weight_val,
                    'unit': str(parsed.get('unit', 'lbs')).lower().rstrip('s') + 's',
                    'confidence': int(parsed.get('confidence', 95 if is_legible else 0)),
                    'notes': str(parsed.get('notes', f'Parsed by {model_name}')),
                    'engine': model_name,
                    'raw_text': f"Weight: {weight_val} {parsed.get('unit', '')}"
                }
            except Exception as model_err:
                last_error = str(model_err)
                print(f"Gemini Flash attempt on {model_name} error: {model_err}")
                continue

        return {
            'success': False,
            'error': f"Scale reading was not legible: {last_error}",
            'engine': 'gemini-error'
        }

    except Exception as e:
        print(f"Gemini Flash Vision error: {e}")
        return {
            'success': False,
            'error': f"Failed to process photo: {str(e)}",
            'engine': 'gemini-error'
        }
