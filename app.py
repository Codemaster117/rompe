from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
from PIL import Image, ImageDraw
import io
import logging

app = Flask(__name__)

# Configure CORS - Allow all origins for development, restrict for production
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_image_files():
    """Get list of image files from static/seed_images directory"""
    seed_images_path = os.path.join(app.static_folder, 'seed_images')
    image_files = []
    
    logger.info(f"Looking for images in: {seed_images_path}")
    
    if os.path.exists(seed_images_path):
        for filename in os.listdir(seed_images_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                image_files.append(filename)
                logger.info(f"Found image: {filename}")
    else:
        logger.warning(f"Directory does not exist: {seed_images_path}")
    
    return image_files

def create_fallback_image(name, width=400, height=300):
    """Create a fallback image if no seed images found"""
    img = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw some simple patterns based on name
    if 'sunset' in name.lower():
        for i in range(height):
            color_val = int(255 * (1 - i/height))
            draw.line([(0, i), (width, i)], fill=(255, color_val, color_val//2))
    elif 'mountain' in name.lower():
        for i in range(height):
            color_val = int(200 * (i/height)) + 55
            draw.line([(0, i), (width, i)], fill=(color_val//3, color_val//2, color_val))
    else:
        # Default gradient
        for i in range(height):
            color_val = int(255 * (i/height))
            draw.line([(0, i), (width, i)], fill=(color_val, color_val//2, 255-color_val))
    
    # Add title text
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        draw.text((10, 10), name, fill='white', font=font)
    except:
        draw.text((10, 10), name, fill='white')
    
    return img

def image_to_base64(pil_image):
    """Convert PIL image to base64 string"""
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@app.route('/')
def index():
    """Main page"""
    logger.info("Serving main page")
    return render_template('index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    response = jsonify({
        'status': 'healthy',
        'message': 'Jigsaw puzzle app is running'
    })
    
    # Add CORS headers manually as backup
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    
    return response

@app.route('/api/debug')
def debug():
    """Debug endpoint to check app status"""
    seed_images_path = os.path.join(app.static_folder, 'seed_images')
    image_files = get_image_files()
    
    debug_info = {
        'status': 'debug',
        'static_folder': app.static_folder,
        'seed_images_path': seed_images_path,
        'path_exists': os.path.exists(seed_images_path),
        'image_files': image_files,
        'total_images': len(image_files)
    }
    
    logger.info(f"Debug info: {debug_info}")
    
    response = jsonify(debug_info)
    
    # Add CORS headers manually as backup
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    
    return response

@app.route('/api/seed-images')
def get_seed_images():
    """Get list of available seed images with base64 data"""
    try:
        logger.info("Getting seed images...")
        image_files = get_image_files()
        images = []
        
        if not image_files:
            # Create fallback images if no files found
            logger.warning("No seed images found, creating fallbacks")
            fallback_names = ['Sunset Beach', 'Mountain Lake', 'Forest Path', 'Ocean Waves']
            for name in fallback_names:
                img = create_fallback_image(name)
                base64_data = image_to_base64(img)
                images.append({
                    'name': name,
                    'filename': f"{name.lower().replace(' ', '_')}.png",
                    'data': base64_data,
                    'type': 'fallback'
                })
        else:
            # Load actual images from static/seed_images
            seed_images_path = os.path.join(app.static_folder, 'seed_images')
            for filename in image_files:
                try:
                    filepath = os.path.join(seed_images_path, filename)
                    logger.info(f"Loading image: {filepath}")
                    
                    with Image.open(filepath) as img:
                        # Resize if too large
                        img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                        base64_data = image_to_base64(img)
                        
                        # Clean name from filename
                        name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
                        
                        images.append({
                            'name': name,
                            'filename': filename,
                            'data': base64_data,
                            'type': 'file'
                        })
                        
                except Exception as e:
                    logger.error(f"Error loading image {filename}: {str(e)}")
                    continue
        
        logger.info(f"Returning {len(images)} images")
        
        response = jsonify({'images': images})
        
        # Add CORS headers manually as backup
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_seed_images: {str(e)}")
        
        response = jsonify({'error': str(e)})
        response.status_code = 500
        
        # Add CORS headers even for errors
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        
        return response

# Add OPTIONS handler for CORS preflight requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_cors_preflight(path):
    """Handle CORS preflight requests"""
    response = jsonify({'status': 'OK'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@app.route('/static/seed_images/<filename>')
def serve_seed_image(filename):
    """Serve images from static/seed_images directory"""
    try:
        seed_images_path = os.path.join(app.static_folder, 'seed_images')
        return send_from_directory(seed_images_path, filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return "Image not found", 404

if __name__ == '__main__':
    # Ensure static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
    
    seed_images_dir = os.path.join('static', 'seed_images')
    if not os.path.exists(seed_images_dir):
        os.makedirs(seed_images_dir)
        logger.info(f"Created directory: {seed_images_dir}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
