from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageDraw
import random
import base64
import io
import os

app = Flask(__name__)
CORS(app)

class JigsawGenerator:
    def __init__(self):
        self.seed_images = []
        self.load_seed_images()
    
    def load_seed_images(self):
        """Load seed images from multiple possible locations"""
        # Try multiple locations for images
        possible_paths = [
            os.path.join(app.root_path, 'seed_images'),
            os.path.join(app.root_path, 'static', 'seed_images'),
            os.path.join(app.root_path, 'static', 'images')
        ]
        
        print("=== LOADING SEED IMAGES ===")
        print(f"App root path: {app.root_path}")
        
        for path in possible_paths:
            print(f"Checking path: {path}")
            if os.path.exists(path):
                print(f"✓ Path exists: {path}")
                try:
                    files = os.listdir(path)
                    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
                    print(f"Found {len(image_files)} images: {image_files}")
                    
                    for img_file in image_files:
                        img_path = os.path.join(path, img_file)
                        try:
                            # Load and process image
                            with Image.open(img_path) as img:
                                # Convert to RGB if necessary
                                if img.mode in ('RGBA', 'P'):
                                    img = img.convert('RGB')
                                
                                # Resize to 400x400
                                img = img.resize((400, 400), Image.Resampling.LANCZOS)
                                
                                # Convert to base64
                                buffer = io.BytesIO()
                                img.save(buffer, format='JPEG', quality=85)
                                img_str = base64.b64encode(buffer.getvalue()).decode()
                                
                                self.seed_images.append({
                                    'name': os.path.splitext(img_file)[0].replace('_', ' ').replace('-', ' ').title(),
                                    'data': f"data:image/jpeg;base64,{img_str}"
                                })
                                print(f"✓ Successfully loaded: {img_file}")
                        except Exception as e:
                            print(f"✗ Error loading {img_file}: {str(e)}")
                    
                    if self.seed_images:
                        print(f"✓ Total images loaded: {len(self.seed_images)}")
                        return  # Stop after first successful path
                        
                except Exception as e:
                    print(f"✗ Error accessing {path}: {str(e)}")
            else:
                print(f"✗ Path does not exist: {path}")
        
        # If no images found, create fallback images
        if not self.seed_images:
            print("No seed images found - creating fallback images...")
            self.create_fallback_images()
    
    def create_fallback_images(self):
        """Create beautiful fallback images if no seed images are found"""
        fallback_configs = [
            {"name": "Ocean Sunset", "colors": [(255, 94, 77), (255, 154, 0), (255, 206, 84)]},
            {"name": "Mountain Dawn", "colors": [(74, 144, 226), (124, 58, 237), (219, 39, 119)]},
            {"name": "Forest Mist", "colors": [(16, 185, 129), (101, 163, 13), (34, 197, 94)]},
            {"name": "Desert Bloom", "colors": [(245, 101, 101), (251, 146, 60), (252, 211, 77)]},
            {"name": "Arctic Aurora", "colors": [(59, 130, 246), (147, 51, 234), (236, 72, 153)]},
            {"name": "Tropical Paradise", "colors": [(6, 182, 212), (52, 211, 153), (110, 231, 183)]}
        ]
        
        for config in fallback_configs:
            img = Image.new('RGB', (400, 400))
            draw = ImageDraw.Draw(img)
            
            # Create gradient
            colors = config["colors"]
            for y in range(400):
                # Calculate color interpolation
                ratio = y / 399
                if ratio < 0.5:
                    # Interpolate between first and second color
                    blend_ratio = ratio * 2
                    r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * blend_ratio)
                    g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * blend_ratio)
                    b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * blend_ratio)
                else:
                    # Interpolate between second and third color
                    blend_ratio = (ratio - 0.5) * 2
                    r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * blend_ratio)
                    g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * blend_ratio)
                    b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * blend_ratio)
                
                draw.line([(0, y), (400, y)], fill=(r, g, b))
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            self.seed_images.append({
                'name': config["name"],
                'data': f"data:image/jpeg;base64,{img_str}"
            })
            print(f"✓ Created fallback image: {config['name']}")
    
    def create_puzzle(self, image_data, difficulty=6):
        """Create jigsaw puzzle pieces from an image"""
        try:
            # Decode base64 image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Ensure image is 400x400
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate piece dimensions
            piece_width = 400 // difficulty
            piece_height = 400 // difficulty
            
            pieces = []
            for row in range(difficulty):
                for col in range(difficulty):
                    # Extract piece
                    left = col * piece_width
                    top = row * piece_height
                    right = left + piece_width
                    bottom = top + piece_height
                    
                    piece = image.crop((left, top, right, bottom))
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    piece.save(buffer, format='JPEG', quality=95)
                    piece_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    pieces.append({
                        'id': row * difficulty + col,
                        'correct_position': row * difficulty + col,
                        'image': f"data:image/jpeg;base64,{piece_str}"
                    })
            
            # Shuffle pieces (but keep track of correct positions)
            shuffled_pieces = pieces.copy()
            random.shuffle(shuffled_pieces)
            
            # Reassign IDs to shuffled positions
            for i, piece in enumerate(shuffled_pieces):
                piece['current_position'] = i
            
            return {
                'pieces': shuffled_pieces,
                'difficulty': difficulty,
                'total_pieces': len(pieces),
                'piece_size': {'width': piece_width, 'height': piece_height}
            }
            
        except Exception as e:
            print(f"Error creating puzzle: {str(e)}")
            return None

# Initialize the generator
puzzle_generator = JigsawGenerator()

@app.route('/')
def index():
    """Serve the main puzzle interface"""
    return render_template('index.html')

@app.route('/api/seed-images')
def get_seed_images():
    """Get all available seed images"""
    return jsonify({
        'images': puzzle_generator.seed_images,
        'count': len(puzzle_generator.seed_images)
    })

@app.route('/api/create-puzzle', methods=['POST'])
def create_puzzle():
    """Create a new puzzle from selected image"""
    try:
        from flask import request
        data = request.get_json()
        image_data = data.get('imageData')
        difficulty = data.get('difficulty', 6)  # Always expert (6x6)
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        puzzle_data = puzzle_generator.create_puzzle(image_data, difficulty)
        if puzzle_data:
            return jsonify(puzzle_data)
        else:
            return jsonify({'error': 'Failed to create puzzle'}), 500
            
    except Exception as e:
        print(f"Error in create_puzzle: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug')
def debug_info():
    """Debug endpoint to check file system and image loading"""
    debug_info = {
        'app_root_path': app.root_path,
        'current_working_directory': os.getcwd(),
        'files_in_root': [],
        'seed_images_found': len(puzzle_generator.seed_images),
        'paths_checked': []
    }
    
    # Check root directory
    try:
        debug_info['files_in_root'] = os.listdir(app.root_path)
    except:
        debug_info['files_in_root'] = ['Error reading root directory']
    
    # Check possible image paths
    possible_paths = [
        os.path.join(app.root_path, 'seed_images'),
        os.path.join(app.root_path, 'static', 'seed_images'),
        os.path.join(app.root_path, 'static', 'images')
    ]
    
    for path in possible_paths:
        path_info = {
            'path': path,
            'exists': os.path.exists(path),
            'files': []
        }
        
        if os.path.exists(path):
            try:
                path_info['files'] = os.listdir(path)
            except:
                path_info['files'] = ['Error reading directory']
        
        debug_info['paths_checked'].append(path_info)
    
    return jsonify(debug_info)

# Route to serve images from seed_images folder
@app.route('/seed_images/<filename>')
def serve_seed_image(filename):
    """Serve images from seed_images folder"""
    seed_images_path = os.path.join(app.root_path, 'seed_images')
    if os.path.exists(seed_images_path):
        return send_from_directory(seed_images_path, filename)
    else:
        return "Image not found", 404

if __name__ == '__main__':
    print("Starting Jigsaw Puzzle App...")
    print(f"Looking for seed images in: {os.path.join(app.root_path, 'seed_images')}")
    app.run(debug=True, host='0.0.0.0', port=5000)
