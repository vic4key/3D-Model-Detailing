import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Load your grayscale image (replace 'your_image.png' with your actual image file)
img_path = "data/height-map.bmp"
img = Image.open(img_path)
height_map = np.array(img)

# Create a meshgrid based on image dimensions
x, y = np.meshgrid(np.arange(height_map.shape[1]), np.arange(height_map.shape[0]))

# Plot the 3D terrain
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, height_map, cmap='terrain')
plt.show()
