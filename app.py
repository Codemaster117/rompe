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
    
    def generate_seed_images(self):
        """Load seed images from static/seed_images folder"""
        seed_images = []
        
        # Path to static seed images folder
        static_folder = os.path.join(app.static_folder or 'static')
        seed_folder = os.path.join(static_folder, 'seed_images')
        
        print(f"Looking for seed images in: {seed_folder}")
        print(f"Static folder: {static_folder}")
        print(f"Folder exists: {os.path.exists(seed_folder)}")
        
        if os.path.exists(seed_folder):
            all_files = os.listdir(seed_folder)
            print(f"All files in folder: {all_files}")
            
            image_files = [f for f in all_files 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            print(f"Image files found: {image_files}")
            
            for filename in sorted(image_files):
                filepath = os.path.join(seed_folder, filename)
                print(f"Trying to load: {filepath}")
                try:
                    with Image.open(filepath) as image:
                        print(f"Successfully opened: {filename}")
                        
                        # Convert to RGB if necessary
                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        # Resize to 400x400
                        image = image.resize((400, 400), Image.Resampling.LANCZOS)
                        
                        # Create clean name from filename
                        name = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ').title()
                        
                        seed_images.append({
                            'name': name,
                            'image': image,
                            'data': self.image_to_base64(image)
                        })
                        print(f"Successfully processed: {name}")
                        
                except Exception as e:
                    print(f"ERROR loading {filename}: {str(e)}")
        else:
            print(f"ERROR: Folder does not exist: {seed_folder}")
            print(f"Available files in static: {os.listdir(static_folder) if os.path.exists(static_folder) else 'static folder not found'}")
            
            # Create a fallback test image
            test_image = Image.new('RGB', (400, 400), '#4CAF50')
            draw = ImageDraw.Draw(test_image)
            draw.text((150, 190), "Add Images", fill='white', font_size=24)
            draw.text((120, 210), "to static/seed_images/", fill='white', font_size=16)
            
            seed_images.append({
                'name': 'Add Your Images',
                'image': test_image,
                'data': self.image_to_base64(test_image)
            })
        
        print(f"Total images loaded: {len(seed_images)}")
        return seed_images
    
    def image_to_base64(self, image):
        """Convert PIL image to base64 data URL"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        base64_data = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"
    
    def create_puzzle_pieces(self, image_data, grid_size=6):
        """Create puzzle pieces from image data"""
        try:
            # Decode base64 image
            image_data = image_data.replace('data:image/png;base64,', '')
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize to ensure it's 400x400
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            
            pieces = []
            piece_size = 400 // grid_size
            
            for row in range(grid_size):
                for col in range(grid_size):
                    # Calculate piece boundaries
                    left = col * piece_size
                    top = row * piece_size
                    right = left + piece_size
                    bottom = top + piece_size
                    
                    # Extract piece from image
                    piece = image.crop((left, top, right, bottom))
                    
                    # Convert to base64
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
            
            # Assign new positions
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

# Create global puzzle generator
puzzle_generator = JigsawGenerator()

@app.route('/')
def index():
    """Serve the main puzzle page"""
    return render_template('index.html')

@app.route('/api/seed-images')
def get_seed_images():
    """Get all available seed images"""
    images = [{'name': img['name'], 'data': img['data']} for img in puzzle_generator.seed_images]
    return jsonify({'images': images})

@app.route('/api/create-puzzle/<int:image_index>')
def create_puzzle(image_index):
    """Create a new puzzle from selected seed image"""
    if 0 <= image_index < len(puzzle_generator.seed_images):
        selected_image = puzzle_generator.seed_images[image_index]
        puzzle_data = puzzle_generator.create_puzzle_pieces(selected_image['data'], grid_size=6)
        
        if puzzle_data:
            return jsonify({
                'success': True,
                'puzzle': puzzle_data,
                'image_name': selected_image['name']
            })
    
    return jsonify({'success': False, 'error': 'Invalid image selection'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

