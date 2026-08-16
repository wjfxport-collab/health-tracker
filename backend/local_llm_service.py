import os
import json
import base64
import re
import urllib.request
import urllib.error
from PIL import Image, ImageOps
import io

def encode_image_to_base64(img_path, max_dim=1200):
    """
    Open image, normalize rotation, resize, and convert to base64 JPEG string.
    """
    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_connection(server_url):
    """
    Test connectivity to the local Mac LLM server (e.g. http://192.168.4.27:11434).
    Returns (is_reachable: bool, message: str).
    """
    url = server_url.rstrip('/')
    test_urls = [
        f"{url}/v1/models",
        f"{url}/api/tags",
        f"{url}/api/version",
        url
    ]
    
    for u in test_urls:
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'HealthPulse-Tracker'})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status in (200, 204, 404, 405):
                    return True, f"Successfully connected to server at {url} (status {resp.status})"
        except urllib.error.HTTPError as he:
            if he.code in (200, 404, 405, 400):
                return True, f"Server responded at {url} (HTTP {he.code})"
        except Exception:
            continue
            
    return False, f"Could not reach local server at {url}. Make sure your Mac server is running and accessible over your LAN."

def parse_scale_with_local_llm(img_path, server_url='http://192.168.4.27:11434', model_name='gemma-4-12b'):
    """
    Submit bathroom scale photo to local Mac Gemma 4 12B vision server.
    Supports both OpenAI-compatible vision format and Ollama vision format.
    """
    base_url = (server_url or 'http://192.168.4.27:11434').rstrip('/')
    model = model_name or 'gemma-4-12b'

    b64_image = encode_image_to_base64(img_path)
    
    prompt = """
You are an expert vision model specialized in reading digital bathroom scales.
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

    # --- Strategy 1: OpenAI-Compatible Vision API (/v1/chat/completions) ---
    openai_url = f"{base_url}/v1/chat/completions" if not base_url.endswith('/v1/chat/completions') else base_url
    openai_payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300
    }

    try:
        req = urllib.request.Request(
            openai_url,
            data=json.dumps(openai_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content = data['choices'][0]['message']['content']
            parsed = extract_json_from_text(content)
            if parsed and parsed.get('weight') is not None:
                w = float(parsed['weight'])
                return {
                    'success': bool(parsed.get('legible', True)),
                    'weight': w,
                    'unit': str(parsed.get('unit', 'lbs')).lower().rstrip('s') + 's',
                    'confidence': int(parsed.get('confidence', 95)),
                    'notes': str(parsed.get('notes', f'Parsed by {model} on Mac')),
                    'engine': f'local-gemma-12b ({base_url})',
                    'raw_text': f"Weight: {w} {parsed.get('unit', 'lbs')}"
                }
    except Exception as e1:
        print(f"OpenAI vision endpoint failed on {openai_url}: {e1}. Trying Ollama native format...")

    # --- Strategy 2: Ollama Native Vision API (/api/chat) ---
    ollama_url = f"{base_url}/api/chat"
    ollama_payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [b64_image]
            }
        ],
        "stream": False,
        "format": "json"
    }

    try:
        req = urllib.request.Request(
            ollama_url,
            data=json.dumps(ollama_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content = data.get('message', {}).get('content') or data.get('response', '')
            parsed = extract_json_from_text(content)
            if parsed and parsed.get('weight') is not None:
                w = float(parsed['weight'])
                return {
                    'success': bool(parsed.get('legible', True)),
                    'weight': w,
                    'unit': str(parsed.get('unit', 'lbs')).lower().rstrip('s') + 's',
                    'confidence': int(parsed.get('confidence', 95)),
                    'notes': str(parsed.get('notes', f'Parsed by {model} on Mac')),
                    'engine': f'local-gemma-12b ({base_url})',
                    'raw_text': f"Weight: {w} {parsed.get('unit', 'lbs')}"
                }
    except Exception as e2:
        print(f"Ollama native endpoint failed on {ollama_url}: {e2}")

    return {
        'success': False,
        'error': f"Failed to connect to local Gemma 4 12B server at {base_url}. Ensure the server is running and accepting LAN connections.",
        'engine': f'local-gemma-12b ({base_url})'
    }

def extract_json_from_text(text):
    """
    Helper to extract JSON object from LLM response text.
    """
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Search for markdown fenced code block or outermost curly braces
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except Exception:
            pass
            
    # Fallback regex extraction of weight
    weight_match = re.search(r'"weight"\s*:\s*(\d{2,3}(?:\.\d{1,2})?)', text)
    if weight_match:
        return {
            'legible': True,
            'weight': float(weight_match.group(1)),
            'unit': 'lbs',
            'confidence': 90,
            'notes': 'Extracted via fallback pattern'
        }

    return None
