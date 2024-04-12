import os
import numpy as np
from PIL import Image, ImageDraw

IMAGE_PATH = R"data\tank-wheel\grayscale\frontal.jpg"
IMAGE_SIZE = (512, 512)

EXPO_HEIGHT = 2

COLORS = {
    "grass" : (34,139,34),
    "forest" : (0, 100, 0),
    "sand" : (238, 214, 175),
    "water" : (65,105,225),
    "rock" : (139, 137, 137),
    "snow" : (255, 250, 250)
}

LUT_VECTORS = (
    (-1, 1), (0, 1), (1, 1),
    (-1, 0),         (1, 0),
    (-1, -1), (0, -1), (1, -1)
)

def normalize(input_map, minimum, maximum, expo):
    scale = maximum - minimum
    output_map = np.zeros(IMAGE_SIZE)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            output_map[x][y] = ((input_map[x][y] - minimum)/scale)**expo
    return output_map

def load_image_and_normalize(image_path):
    """
    Loads an image from the specified path and normalizes pixel values to [0.0, 1.0].
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        np.ndarray: Normalized image as a NumPy array.
    """
    try:
        # Load the image
        image = Image.open(image_path).convert('L')
        
        # Convert to NumPy array
        image_array = np.array(image)
        
        # Normalize pixel values to [0.0, 1.0]
        normalized_image = image_array.astype(np.float32) / 255.0
        
        return normalized_image
    except Exception as e:
        print(f"Error loading or normalizing the image: {e}")
        return None

def generate_depthmap_from_image():
    depthmap = load_image_and_normalize(IMAGE_PATH)
    return depthmap

def generate_depthmap():
    minimum = 0
    maximum = 0
    depthmap = generate_depthmap_from_image()
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            new_value = depthmap[x][y]
            if new_value < minimum:
                minimum = new_value
            if new_value > maximum:
                maximum = new_value
    print(f"Generated Depthmap (minimum = {minimum:.3f}, maximum = {maximum:.3f})")
    return normalize(depthmap, minimum, maximum, EXPO_HEIGHT)

def out_of_bounds(point):
    if 0 <= point[0] < IMAGE_SIZE[0] and 0 <= point[1] < IMAGE_SIZE[1]:
        return True
    if point[1] < 0 or point[1] >= IMAGE_SIZE[1]:
        return True
    return False

def generate_slopemap(depthmap):
    valid = lambda point: 0 <= point[0] < IMAGE_SIZE[0] and 0 <= point[1] < IMAGE_SIZE[1]
    slopemap = np.zeros(IMAGE_SIZE)
    minimum = 0
    maximum = 0
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            slope = 0
            for vector in LUT_VECTORS:
                point = (x+vector[0], y+vector[1])
                if not valid(point): continue
                slope += abs(depthmap[x][y]-depthmap[point[0]][point[1]])
            slope = slope/8
            slopemap[x][y] = slope
            if slope < minimum:
                minimum = slope
            if slope > maximum:
                maximum = slope
    print("Generated Slopemap")
    return normalize(slopemap, minimum, maximum, 1)

def get_color(height, slope):
    if height > 0.2 and height < 0.9 and slope > 0.45:
       return COLORS["rock"]
    if height <= 0.2:
        return COLORS["water"]
    elif height > 0.2 and height <= 0.225:
        return COLORS["sand"]
    elif height > 0.225 and height <= 0.45:
        return COLORS["grass"]
    elif height > 0.45 and height <= 0.85:
        return COLORS["forest"]
    elif height > 0.85 and height <= 0.9:
        return COLORS["rock"]
    elif height > 0.9:
        return COLORS["snow"]

def generate_vertices(depthmap):
    vertices = []
    base = (-1, -0.75, -1)
    size = 2
    max_height = 0.5
    step_x = size/(IMAGE_SIZE[0]-1)
    step_y = size/(IMAGE_SIZE[1]-1)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            x_coord = base[0] + step_x*x 
            y_coord = base[1] + max_height*depthmap[x][y]
            z_coord = base[2] + step_y*y
            vertices.append((x_coord, y_coord, z_coord))
    print("Generated Vertices")
    return vertices
    
def generate_edges_and_surfaces():
    edges = []
    surfaces = []
    for x in range(IMAGE_SIZE[0]-1):
        for y in range(IMAGE_SIZE[1]-1):
            base = x*IMAGE_SIZE[0]+y
            a = base
            b = base+1
            c = base+IMAGE_SIZE[0]+1
            d = base+IMAGE_SIZE[0]
            edges.append((a, b))
            edges.append((b, c))
            edges.append((c, a))
            edges.append((c, d))
            edges.append((d, a))
            surfaces.append((a, b, c))
            surfaces.append((a, c, d))
    print("Generated Edges & Surfaces")
    return edges, surfaces

def export_norm_map(norm_map, filename):
    image = Image.new('RGB', IMAGE_SIZE, 0)
    draw = ImageDraw.ImageDraw(image)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            color = int(norm_map[x][y]*255)
            draw.point((x, y), (color, color, color))
    image.save(filename) 
    print(f"Saved '{filename}'")
    return

def export_texture(depthmap, slopemap, filename):
    image = Image.new('RGB', IMAGE_SIZE, 0)
    draw = ImageDraw.ImageDraw(image)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            draw.point((x, y), get_color(depthmap[x][y], slopemap[x][y]))
    image.save(filename)
    print(f"Saved '{filename}'")
    return

def export_3d_model(vertices, tris, filename):
    file = open(filename, "w")
    for vertex in vertices:
      file.write("v " + str(vertex[0]) + " " + str(vertex[1]) + " " + str(vertex[2]) + "\n")
    for tri in tris:
      file.write("f " + str(tri[2]+1) + " " + str(tri[1]+1) + " " + str(tri[0]+1) + "\n")
    file.close()
    print(f"Saved '{filename}'")
    return

def main():
    # generate 3d model
    depthmap = generate_depthmap()
    slopemap = generate_slopemap(depthmap)
    vertices = generate_vertices(depthmap)
    edges, surfaces = generate_edges_and_surfaces()

    # make output directory
    parts = IMAGE_PATH.split("\\")
    folder_name = parts[1]
    file_name   = parts[3].split(".")[0]
    output_dir  = RF"result\{folder_name}\{file_name}"
    os.makedirs(output_dir, exist_ok=True)

    # export 3d model to files
    export_3d_model(vertices, surfaces, RF"{output_dir}\model.obj")
    export_norm_map(depthmap, RF"{output_dir}\depthmap.png")
    export_norm_map(slopemap, RF"{output_dir}\slopemap.png")
    export_texture(depthmap, slopemap, RF"{output_dir}\texture.png")

if __name__ == "__main__":
    main()
