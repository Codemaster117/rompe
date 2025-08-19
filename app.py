from flask import Flask, render_template, jsonify
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
        self.seed_images = self.generate_seed_images()
    
    def load_static_images(self):
        """Load images from static/seed_images folder"""
        seed_images = []
        
        # Get the static folder path
        static_folder = os.path.join(app.root_path, 'static')
        seed_folder = os.path.join(static_folder, 'seed_images')
        
        print(f"=== LOADING STATIC IMAGES ===")
        print(f"App root path: {app.root_path}")
        print(f"Static folder: {static_folder}")
        print(f"Seed folder: {seed_folder}")
        print(f"Static folder exists: {os.path.exists(static_folder)}")
        print(f"Seed folder exists: {os.path.exists(seed_folder)}")
        
        if os.path.exists(seed_folder):
            try:
                all_files = os.listdir(seed_folder)
                print(f"All files in seed folder: {all_files}")
                
                # Filter for image files
                image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
                image_files = [f for f in all_files if f.lower().endswith(image_extensions)]
                print(f"Image files found: {image_files}")
                
                for filename in sorted(image_files):
                    filepath = os.path.join(seed_folder, filename)
                    try:
                        print(f"Loading: {filepath}")
                        with Image.open(filepath) as img:
                            # Convert to RGB if needed
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Resize to 400x400
                            img = img.resize((400, 400), Image.Resampling.LANCZOS)
                            
                            # Create display name
                            name = os.path.splitext(filename)[0]
                            name = name.replace('-', ' ').replace('_', ' ').title()
                            
                            seed_images.append({
                                'name': name,
                                'image': img.copy(),
                                'data': self.image_to_base64(img)
                            })
                            print(f"✓ Successfully loaded: {name}")
                            
                    except Exception as e:
                        print(f"✗ Error loading {filename}: {e}")
                        
            except Exception as e:
                print(f"Error reading seed folder: {e}")
        else:
            print(f"Seed folder not found: {seed_folder}")
            if os.path.exists(static_folder):
                print(f"Static folder contents: {os.listdir(static_folder)}")
        
        print(f"Total static images loaded: {len(seed_images)}")
        return seed_images
    
    def create_fallback_images(self):
        """Create colorful fallback images if no static images found"""
        print("Creating fallback images...")
        fallback_images = []
        
        # Gradient patterns
        gradients = [
            {
                'name': 'Ocean Sunset',
                'colors': [(255, 107, 107), (76, 175, 196), (168, 85, 247)],
            },
            {
                'name': 'Forest Dawn',
                'colors': [(168, 230, 207), (255, 217, 61), (74, 222, 128)],
            },
            {
                'name': 'Purple Dream',
                'colors': [(196, 181, 253), (255, 182, 193), (147, 197, 253)],
            },
            {
                'name': 'Warm Glow',
                'colors': [(251, 191, 36), (248, 113, 113), (252, 231, 243)],
            }
        ]
        
        for grad in gradients:
            image = self.create_gradient_image(grad['colors'], grad['name'])
            fallback_images.append({
                'name': grad['name'],
                'image': image,
                'data': self.image_to_base64(image)
            })
        
        return fallback_images
    
    def create_gradient_image(self, colors, name):
        """Create a radial gradient image"""
        image = Image.new('RGB', (400, 400))
        
        center_x, center_y = 200, 200
        max_radius = 280
        
        for y in range(400):
            for x in range(400):
                # Calculate distance from center
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                ratio = min(distance / max_radius, 1.0)
                
                # Interpolate through color stops
                color_stops = len(colors) - 1
                if color_stops == 0:
                    r, g, b = colors[0]
                else:
                    segment = ratio * color_stops
                    idx = int(segment)
                    local_ratio = segment - idx
                    
                    if idx >= color_stops:
                        r, g, b = colors[-1]
                    else:
                        c1, c2 = colors[idx], colors[idx + 1]
                        r = int(c1[0] + (c2[0] - c1[0]) * local_ratio)
                        g = int(c1[1] + (c2[1] - c1[1]) * local_ratio)
                        b = int(c1[2] + (c2[2] - c1[2]) * local_ratio)
                
                image.putpixel((x, y), (r, g, b))
        
        return image
    
    def generate_seed_images(self):
        """Load images from static folder, fallback to generated images"""
        # Try to load static images first
        static_images = self.load_static_images()
        
        if static_images:
            print(f"Using {len(static_images)} static images")
            return static_images
        else:
            print("No static images found, using fallback images")
            return self.create_fallback_images()
    
    def image_to_base64(self, image):
        """Convert PIL image to base64 data URL"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        img_data = buffer.getvalue()
        base64_data = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"
    
    def create_puzzle_pieces(self, image_data, grid_size=6):
        """Create puzzle pieces from image data"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Ensure proper format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            
            pieces = []
            piece_size = 400 // grid_size
            
            # Create pieces
            for row in range(grid_size):
                for col in range(grid_size):
                    left = col * piece_size
                    top = row * piece_size
                    right = left + piece_size
                    bottom = top + piece_size
                    
                    # Extract piece
                    piece = image.crop((left, top, right, bottom))
                    piece_data = self.image_to_base64(piece)
                    
                    pieces.append({
                        'id': row * grid_size + col,
                        'row': row,
                        'col': col,
                        'data': piece_data,
                        'correct_position': row * grid_size + col
                    })
            
            # Shuffle pieces
            shuffled_pieces = pieces.copy()
            random.shuffle(shuffled_pieces)
            
            # Assign shuffled positions
            for i, piece in enumerate(shuffled_pieces):
                piece['current_position'] = i
            
            return {
                'pieces': shuffled_pieces,
                'original_image': self.image_to_base64(image),
                'grid_size': grid_size,
                'total_pieces': len(pieces)
            }
            
        except Exception as e:
            print(f"Error creating puzzle pieces: {e}")
            return None

# Initialize puzzle generator
puzzle_generator = JigsawGenerator()

@app.route('/')
def index():
    """Serve the main puzzle page"""
    return render_template('index.html')

@app.route('/api/debug')
def debug_info():
    """Debug endpoint to check file system"""
    debug_data = {
        'app_root_path': app.root_path,
        'current_directory': os.getcwd(),
        'static_folder_exists': os.path.exists(os.path.join(app.root_path, 'static')),
        'seed_images_count': len(puzzle_generator.seed_images),
        'image_names': [img['name'] for img in puzzle_generator.seed_images]
    }
    
    static_path = os.path.join(app.root_path, 'static')
    if os.path.exists(static_path):
        debug_data['static_contents'] = os.listdir(static_path)
        seed_path = os.path.join(static_path, 'seed_images')
        if os.path.exists(seed_path):
            debug_data['seed_images_contents'] = os.listdir(seed_path)
    
    return jsonify(debug_data)

@app.route('/api/seed-images')
def get_seed_images():
    """Get all available seed images"""
    try:
        images = []
        for img in puzzle_generator.seed_images:
            images.append({
                'name': img['name'],
                'data': img['data']
            })
        
        print(f"Serving {len(images)} seed images to frontend")
        return jsonify({'images': images})
        
    except Exception as e:
        print(f"Error in get_seed_images: {e}")
        return jsonify({'images': []}), 500

@app.route('/api/create-puzzle/<int:image_index>')
def create_puzzle(image_index):
    """Create a new puzzle from selected seed image"""
    try:
        print(f"Creating puzzle for image index: {image_index}")
        
        if 0 <= image_index < len(puzzle_generator.seed_images):
            selected_image = puzzle_generator.seed_images[image_index]
            puzzle_data = puzzle_generator.create_puzzle_pieces(selected_image['data'], grid_size=6)
            
            if puzzle_data:
                print(f"✓ Puzzle created successfully for: {selected_image['name']}")
                return jsonify({
                    'success': True,
                    'puzzle': puzzle_data,
                    'image_name': selected_image['name']
                })
            else:
                print("✗ Failed to create puzzle data")
                return jsonify({'success': False, 'error': 'Failed to create puzzle'}), 500
        else:
            print(f"✗ Invalid image index: {image_index} (available: 0-{len(puzzle_generator.seed_images)-1})")
            return jsonify({'success': False, 'error': 'Invalid image selection'}), 400
            
    except Exception as e:
        print(f"Error in create_puzzle: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Jigsaw Puzzle App...")
    print(f"Available images: {len(puzzle_generator.seed_images)}")
    app.run(debug=True, host='0.0.0.0', port=5000)
