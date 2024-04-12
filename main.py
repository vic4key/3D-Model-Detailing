import os
import numpy as np
from PIL import Image, ImageDraw

IMAGE_PATH  = R"data\tank-wheel\grayscale\frontal.jpg"
IMAGE_SIZE  = (512, 512)
EXPO_HEIGHT = 2

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

def generate_depthmap(norm_image):
    minimum = 0
    maximum = 0
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            new_value = norm_image[x][y]
            if new_value < minimum:
                minimum = new_value
            if new_value > maximum:
                maximum = new_value
    print(f"Generated Depthmap (minimum = {minimum:.3f}, maximum = {maximum:.3f})")
    return normalize(norm_image, minimum, maximum, EXPO_HEIGHT)

def generate_vertices(depth_map):
    vertices = []
    base = (-1, -0.75, -1)
    size = 2
    max_height = 0.5
    step_x = size/(IMAGE_SIZE[0]-1)
    step_y = size/(IMAGE_SIZE[1]-1)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            x_coord = base[0] + step_x*x 
            y_coord = base[1] + max_height*depth_map[x][y]
            z_coord = base[2] + step_y*y
            vertices.append((x_coord, y_coord, z_coord))
    print("Generated Vertices")
    return vertices
    
def generate_edges_and_triangles():
    edges = []
    triangles = []
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
            triangles.append((a, b, c))
            triangles.append((a, c, d))
    print("Generated Edges & Triangles")
    return edges, triangles

def export_depth_map(norm_map, filename):
    image = Image.new('RGB', IMAGE_SIZE, 0)
    draw = ImageDraw.ImageDraw(image)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            color = int(norm_map[x][y]*255)
            draw.point((x, y), (color, color, color))
    image.save(filename) 
    print(f"Saved '{filename}'")
    return

def export_3d_model(vertices, triangles, filename): # wavefront .obj file format
    file = open(filename, "w")
    for vertex in vertices:
      file.write(f"v {vertex[0]:.5f} {vertex[1]:.5f} {vertex[2]:.5f}\n")
    for triangle in triangles:
      file.write(f"f {triangle[2]+1:.5f} {triangle[1]+1:.5f} {triangle[0]+1:.5f}\n")
    file.close()
    print(f"Saved '{filename}'")
    return

def main():
    # generate 3d model
    norm_img  = load_image_and_normalize(IMAGE_PATH)
    depth_map = generate_depthmap(norm_img)
    vertices  = generate_vertices(depth_map)
    edges, triangles = generate_edges_and_triangles()

    # make output directory
    parts = IMAGE_PATH.split("\\")
    folder_name = parts[1]
    file_name   = parts[3].split(".")[0]
    output_dir  = RF"result\{folder_name}"
    os.makedirs(output_dir, exist_ok=True)

    # export 3d model to files
    export_depth_map(depth_map, RF"{output_dir}\{file_name}_depth-map.png")
    export_3d_model(vertices, triangles, RF"{output_dir}\{file_name}.obj")

if __name__ == "__main__":
    main()
