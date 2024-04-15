import os
import numpy as np
from PIL import Image, ImageDraw

IMAGE_PATH  = R"data\tank-wheel\grayscale\lateral.jpg"
IMAGE_SIZE  = (512, 512)
EXPO_HEIGHT = 2.0

def load_image(image_path: str) -> np.array:
    result = None
    try:
        image  = Image.open(image_path).convert('L')
        result = np.array(image).astype(np.float32) / 255.0 # normalize pixel values to [0.0, 1.0]
    except Exception as e:
        result = None
        print(f"Error loading or normalizing the image: {e}")
    return result

def generate_depthmap(image: np.array) -> np.array:
    '''
    Generate depth-map by transform pixel of 2d image
    '''
    # find lowest and highest pixel values
    pixel_lowest  = 0
    pixel_highest = 0
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            value = image[x][y]
            if value < pixel_lowest:
                pixel_lowest = value
            if value > pixel_highest:
                pixel_highest = value
    pixel_max_height = pixel_highest - pixel_lowest
    # pixel transformation
    result = np.zeros(IMAGE_SIZE)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            value = image[x][y]
            value = (value - pixel_lowest) / pixel_max_height # normalize pixel that base on lowest and highest pixel values
            value **= EXPO_HEIGHT # exponential transformation (contrast adjustment, brightness enhancement, noise reduction)
            result[x][y] = value
    print(f"Generated Depthmap (low = {pixel_lowest:.3f}, high = {pixel_highest:.3f})")
    return result

def generate_vertices(depth_map: np.array) -> list:
    '''
    Generate vertices for a 2D image
    '''
    vertices = []
    base = (-1, -0.75, -1)
    size = 2
    max_height = 0.5
    step_x = size / (IMAGE_SIZE[0] - 1)
    step_y = size / (IMAGE_SIZE[1] - 1)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            x_coord = base[0] + step_x*x 
            y_coord = base[1] + max_height * depth_map[x][y]
            z_coord = base[2] + step_y*y
            vertices.append((x_coord, y_coord, z_coord))
    print("Generated Vertices")
    return vertices
    
def generate_edges_and_triangles() -> tuple:
    '''
    Generate edges and triangles for a 2D array
    '''
    edges = []
    triangles = []
    for x in range(IMAGE_SIZE[0] - 1):
        for y in range(IMAGE_SIZE[1] - 1):
            v = x * IMAGE_SIZE[0] + y
            v0 = v
            v1 = v + 1
            v2 = v + IMAGE_SIZE[0] + 1
            v3 = v + IMAGE_SIZE[0]
            edges.append((v0, v1))
            edges.append((v1, v2))
            edges.append((v2, v0))
            edges.append((v2, v3))
            edges.append((v3, v0))
            triangles.append((v0, v1, v2))
            triangles.append((v0, v2, v3))
    print("Generated Edges & Triangles")
    return (edges, triangles)

def export_depth_map(depth_map, image_path):
    image = Image.new("RGB", IMAGE_SIZE, 0)
    draw  = ImageDraw.ImageDraw(image)
    for x in range(IMAGE_SIZE[0]):
        for y in range(IMAGE_SIZE[1]):
            color = int(depth_map[x][y] * 255.0)
            draw.point((x, y), (color, color, color))
    image.save(image_path) 
    print(f"Saved '{image_path}'")
    return

def export_3d_model(vertices, triangles, edges, filename): # wavefront .obj file format
    # https://en.wikipedia.org/wiki/Wavefront_.obj_file
    with open(filename, "w") as file:
        # export vertices : https://en.wikipedia.org/wiki/Wavefront_.obj_file#Geometric_vertex
        for vertex in vertices:
            file.write(f"v {vertex[0]:.5f} {vertex[1]:.5f} {vertex[2]:.5f}\n")
        # export faces : https://en.wikipedia.org/wiki/Wavefront_.obj_file#Face_elements
        for triangle in triangles: # vertex indices
            file.write(f"f {triangle[2] + 1} {triangle[1] + 1} {triangle[0] + 1}\n") # the offset in that vertex list, starting at 1
        # for edge in edges:
        #     file.write(f"f {edge[0] + 1} {edge[1] + 1}\n")
        print(f"Saved '{filename}'")
    return

def main():
    # generate 3d model
    image = load_image(IMAGE_PATH)
    depth_map = generate_depthmap(image)
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
    export_3d_model(vertices, triangles, edges, RF"{output_dir}\{file_name}.obj")

if __name__ == "__main__":
    main()
