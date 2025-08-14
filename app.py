from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import base64
from PIL import Image, ImageDraw
import io
import os

app = Flask(__name__)
CORS(app)

class JigsawGenerator:
    def __init__(self):
        self.seed_images = []
    
def generate_seed_images(self):
    """Load only seed images from files - no programmatic images"""
    seed_images = []
    
    # Create a 'seed_images' folder in your project
    seed_folder = os.path.join(os.path.dirname(__file__), 'seed_images')
    
    if os.path.exists(seed_folder):
        for filename in os.listdir(seed_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(seed_folder, filename)
                try:
                    image = Image.open(filepath)
                    # Resize to 400x400
                    image = image.resize((400, 400), Image.Resampling.LANCZOS)
                    
                    seed_images.append({
                        'name': os.path.splitext(filename)[0],
                        'image': image,
                        'data': self.image_to_base64(image)
                    })
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    return seed_images
    
    def create_gradient_image(self, colors, name):
        """Create a gradient image with given colors"""
        width, height = 400, 400
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create radial gradient effect
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2
        
        for y in range(height):
            for x in range(width):
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                ratio = min(distance / max_radius, 1.0)
                
                # Interpolate between colors
                if ratio <= 0.33:
                    color = self.interpolate_color(colors[0], colors[1], ratio * 3)
                elif ratio <= 0.66:
                    color = self.interpolate_color(colors[1], colors[2], (ratio - 0.33) * 3)
                else:
                    color = self.interpolate_color(colors[2], colors[3], (ratio - 0.66) * 3)
                
                draw.point((x, y), color)
        
        return {
            'name': name,
            'image': image,
            'data': self.image_to_base64(image)
        }
    
    def create_geometric_pattern(self, pattern_id):
        """Create geometric patterns"""
        width, height = 400, 400
        image = Image.new('RGB', (width, height), '#F8F9FA')
        draw = ImageDraw.Draw(image)
        
        if pattern_id == 0:  # Circles
            colors = ['#FF6B9D', '#C44FAD', '#7209B7', '#A663CC']
            for i in range(20):
                x = random.randint(0, width)
                y = random.randint(0, height)
                radius = random.randint(20, 80)
                color = random.choice(colors)
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                           fill=color + '80')  # Semi-transparent
        
        elif pattern_id == 1:  # Triangles
            colors = ['#4ECDC4', '#44A08D', '#093637', '#B2FEFA']
            for i in range(15):
                x1, y1 = random.randint(0, width), random.randint(0, height)
                x2, y2 = x1 + random.randint(-60, 60), y1 + random.randint(-60, 60)
                x3, y3 = x1 + random.randint(-60, 60), y1 + random.randint(-60, 60)
                color = random.choice(colors)
                draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=color + '80')
        
        else:  # Rectangles
            colors = ['#FFA726', '#FF7043', '#FF5722', '#FFCC80']
            for i in range(25):
                x1, y1 = random.randint(0, width-50), random.randint(0, height-50)
                x2, y2 = x1 + random.randint(30, 100), y1 + random.randint(30, 100)
                color = random.choice(colors)
                draw.rectangle([x1, y1, x2, y2], fill=color + '80')
        
        return {
            'name': f'geometric_{pattern_id}',
            'image': image,
            'data': self.image_to_base64(image)
        }
    
    def interpolate_color(self, color1, color2, ratio):
        """Interpolate between two hex colors"""
        c1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
        
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        return (r, g, b)
    
    def image_to_base64(self, image):
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def shuffle_puzzle(self, grid_size, seed=None):
        """Generate a shuffled puzzle configuration"""
        if seed is not None:
            random.seed(seed)
        
        total_pieces = grid_size * grid_size
        pieces = list(range(total_pieces))
        random.shuffle(pieces)
        
        return pieces

# Initialize the jigsaw generator
jigsaw_gen = JigsawGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/seed-images')
def get_seed_images():
    """Get all available seed images"""
    images = []
    for img_data in jigsaw_gen.seed_images:
        images.append({
            'id': img_data['name'],
            'name': img_data['name'].replace('_', ' ').title(),
            'data': img_data['data']
        })
    return jsonify(images)

@app.route('/api/puzzle/generate', methods=['POST'])
def generate_puzzle():
    """Generate a shuffled puzzle - always 6x6 (extreme)"""
    data = request.get_json()
    grid_size = 6  # Always extreme difficulty
    seed = data.get('seed', None)
    
    shuffled_pieces = jigsaw_gen.shuffle_puzzle(grid_size, seed)
    
    return jsonify({
        'grid_size': grid_size,
        'pieces': shuffled_pieces,
        'seed': seed
    })

@app.route('/api/puzzle/validate', methods=['POST'])
def validate_puzzle():
    """Check if puzzle is solved"""
    data = request.get_json()
    current_order = data.get('current_order', [])
    
    is_solved = all(i == pos for i, pos in enumerate(current_order))
    
    return jsonify({
        'is_solved': is_solved,
        'message': 'Congratulations! Puzzle solved!' if is_solved else 'Keep trying!'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    app.run(host='0.0.0.0', port=port, debug=True)

