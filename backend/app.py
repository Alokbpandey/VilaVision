from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import requests
from PIL import Image
import base64
from io import BytesIO
import time
import uuid
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any
import tempfile
from dataclasses import dataclass, field
from http import HTTPStatus
from datetime import datetime
import shutil

app = Flask(__name__)

@app.route('/api/process', methods=['POST'])
def process():
    file = request.files.get('file')  # Check for uploaded file
    url = request.form.get('url')    # Check for URL

    if file:
        # Handle uploaded file
        # file.save() or process it directly
        return jsonify({"message": "File processed successfully!"})

    elif url:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # Save or process the file content
            return jsonify({"message": "URL processed successfully!"})
        except requests.RequestException as e:
            return jsonify({"error": f"Failed to process URL: {str(e)}"}), 400

    return jsonify({"error": "No file or URL provided"}), 400


# Load environment variables
load_dotenv()

# Configuration class
@dataclass
class Config:
    # API Configuration
    VILA_API_URL: str = os.getenv('NVIDIA_API_URL', 'https://ai.api.nvidia.com/v1/vlm/nvidia/vila')
    API_KEY: Optional[str] = os.getenv('NVIDIA_API_KEY')
    ASSETS_API_URL: str = "https://api.nvcf.nvidia.com/v2/nvcf/assets"
    
    # File Handling
    UPLOAD_FOLDER: str = 'uploads'
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {'png', 'jpg', 'jpeg', 'gif', 'mp4'})
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Image Processing
    MAX_IMAGE_SIZE: int = 180000  # 180KB for base64 encoded image
    MAX_WIDTH: int = 1200
    MAX_HEIGHT: int = 1200
    MIN_QUALITY: int = 60
    INITIAL_QUALITY: int = 95
    
    # VILA Model Parameters
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.20
    TOP_P: float = 0.70
    SEED: int = 50
    NUM_FRAMES_PER_INFERENCE: int = 8
    
    # API Response
    REQUEST_TIMEOUT: int = 30
    STREAM_TIMEOUT: int = 300
    
    # Supported Media Types
    SUPPORTED_MEDIA: Dict[str, Tuple[str, str]] = field(
        default_factory=lambda: {
            "png": ("image/png", "img"),
            "jpg": ("image/jpg", "img"),
            "jpeg": ("image/jpeg", "img"),
            "gif": ("image/gif", "img"),
            "mp4": ("video/mp4", "video")
        }
    )

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)


# Load configuration
config = Config()

# Validation
if not config.API_KEY:
    raise ValueError('NVIDIA_API_KEY environment variable is required')

# Setup directories
temp_dir = tempfile.mkdtemp()
os.makedirs(temp_dir, exist_ok=True)
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# Configure logging
def setup_logging():
    """Configure application logging"""
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # File handler for general logs
    file_handler = TimedRotatingFileHandler(
        'logs/app.log',
        when='midnight',
        interval=1,
        backupCount=7
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    
    # Error log handler
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10_000_000,
        backupCount=5
    )
    error_handler.setFormatter(log_format)
    error_handler.setLevel(logging.ERROR)
    
    # Configure Flask logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)

setup_logging()

# Custom Exceptions
class VILAError(Exception):
    """Base exception for VILA-related errors"""
    pass

class ImageProcessingError(VILAError):
    """Exception raised for image processing errors"""
    pass

class VideoProcessingError(VILAError):
    """Exception raised for video processing errors"""
    pass

class APIError(VILAError):
    """Exception raised for API-related errors"""
    pass

# Utility Functions
def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in config.ALLOWED_EXTENSIONS

def get_mime_type(ext: str) -> str:
    """Get MIME type for file extension"""
    return config.SUPPORTED_MEDIA[ext][0]

def get_media_type(ext: str) -> str:
    """Get media type (img/video) for file extension"""
    return config.SUPPORTED_MEDIA[ext][1]

def process_image(image_path: str) -> Tuple[str, int, int]:
    """
    Process and optimize image for VILA API
    Returns: (base64_string, width, height)
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGBA
            img = img.convert('RGBA')
            
            # Initial resize if needed
            width, height = img.size
            if width > config.MAX_WIDTH or height > config.MAX_HEIGHT:
                ratio = min(config.MAX_WIDTH/width, config.MAX_HEIGHT/height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                width, height = new_size
            
            output = BytesIO()
            quality = config.INITIAL_QUALITY
            
            while True:
                output.seek(0)
                output.truncate()
                img.save(output, format='PNG', optimize=True, quality=quality)
                
                if len(output.getvalue()) <= config.MAX_IMAGE_SIZE:
                    break
                    
                if quality > config.MIN_QUALITY:
                    quality -= 5
                else:
                    # Resize image if quality reduction isn't enough
                    width = int(width * 0.9)
                    height = int(height * 0.9)
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                    quality = config.INITIAL_QUALITY
                
                if width < 100 or height < 100:
                    raise ImageProcessingError(
                        "Unable to reduce image to required size while maintaining quality"
                    )
            
            return base64.b64encode(output.getvalue()).decode(), width, height
            
    except Exception as e:
        raise ImageProcessingError(f"Image processing failed: {str(e)}")

def upload_asset(file_path: str, description: str) -> str:
    """Upload asset to NVIDIA's asset storage"""
    try:
        ext = get_file_extension(file_path)
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # Get upload URL
        headers = {
            "Authorization": f"Bearer {config.API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        response = requests.post(
            config.ASSETS_API_URL,
            headers=headers,
            json={
                "contentType": get_mime_type(ext),
                "description": description
            },
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        upload_info = response.json()
        
        # Upload file
        response = requests.put(
            upload_info["uploadUrl"],
            data=data,
            headers={
                "x-amz-meta-nvcf-asset-description": description,
                "content-type": get_mime_type(ext)
            },
            timeout=config.STREAM_TIMEOUT
        )
        response.raise_for_status()
        
        return upload_info["assetId"]
        
    except Exception as e:
        raise APIError(f"Asset upload failed: {str(e)}")

def delete_asset(asset_id: str):
    """Delete asset from NVIDIA's storage"""
    try:
        response = requests.delete(
            f"{config.ASSETS_API_URL}/{asset_id}",
            headers={"Authorization": f"Bearer {config.API_KEY}"},
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except Exception as e:
        app.logger.error(f"Failed to delete asset {asset_id}: {str(e)}")

def process_vila_request(prompt: str, media_content: str, asset_ids: list = None) -> dict:
    """Make request to VILA API"""
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    if asset_ids:
        asset_seq = ",".join(asset_ids)
        headers.update({
            "NVCF-INPUT-ASSET-REFERENCES": asset_seq,
            "NVCF-FUNCTION-ASSET-IDS": asset_seq
        })
    
    payload = {
        "messages": [{
            "role": "user",
            "content": f"{prompt} {media_content}"
        }],
        "max_tokens": config.MAX_TOKENS,
        "temperature": config.TEMPERATURE,
        "top_p": config.TOP_P,
        "seed": config.SEED,
        "num_frames_per_inference": config.NUM_FRAMES_PER_INFERENCE,
        "stream": False,
        "model": "nvidia/vila"
    }
    
    try:
        response = requests.post(
            config.VILA_API_URL,
            headers=headers,
            json=payload,
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        raise APIError(f"VILA API request failed: {str(e)}")

# Routes
@app.route('/api/process', methods=['POST'])
def process():
    """Process media file and get VILA model response"""
    temp_file = None
    asset_id = None
    
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), HTTPStatus.BAD_REQUEST
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'Empty filename'}), HTTPStatus.BAD_REQUEST
            
        prompt = request.form.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), HTTPStatus.BAD_REQUEST

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), HTTPStatus.BAD_REQUEST

        # Save file
        filename = secure_filename(file.filename)
        temp_file = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")
        file.save(temp_file)
        
        ext = get_file_extension(filename)
        media_type = get_media_type(ext)
        
        if media_type == "img":
            # Process image
            base64_image, width, height = process_image(temp_file)
            media_content = f'<img src="data:image/png;base64,{base64_image}" />'
            vila_response = process_vila_request(prompt, media_content)
            
            response_data = {
                'vila_response': vila_response,
                'image_metadata': {
                    'width': width,
                    'height': height,
                    'size_bytes': len(base64.b64decode(base64_image))
                }
            }
            
        else:  # video
            # Upload video as asset
            asset_id = upload_asset(temp_file, "Video analysis request")
            media_content = f'<video src="data:{get_mime_type(ext)};asset_id,{asset_id}" />'
            vila_response = process_vila_request(prompt, media_content, [asset_id])
            
            response_data = {
                'vila_response': vila_response,
                'video_metadata': {
                    'asset_id': asset_id
                }
            }
        
        return jsonify(response_data), HTTPStatus.OK
        
    except (ImageProcessingError, VideoProcessingError, APIError) as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
        
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), HTTPStatus.INTERNAL_SERVER_ERROR
        
    finally:
        # Cleanup
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                app.logger.error(f"Error cleaning up file {temp_file}: {str(e)}")
        
        if asset_id:
            delete_asset(asset_id)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

# Error Handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large'}), HTTPStatus.REQUEST_ENTITY_TOO_LARGE

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), HTTPStatus.BAD_REQUEST

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), HTTPStatus.INTERNAL_SERVER_ERROR

# Cleanup on shutdown
def cleanup():
    """Clean up temporary files on shutdown"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        app.logger.error(f"Cleanup error: {str(e)}")


# Main
if __name__ == '__main__':
    # Register cleanup
    import atexit
    atexit.register(cleanup)
    
    # Start server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )

    