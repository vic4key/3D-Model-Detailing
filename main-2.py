from PIL import Image
from pyhull.delaunay import DelaunayTri
from shapely import geometry
from skimage import measure
from scipy import interpolate
import math
import numpy as np
import struct
import sys

zExaggeration = 2
zScale = 73.63159488086174 * zExaggeration

outputSize = 140
layerThickness = 0.025
baseThickness = 3

def save_binary_stl(path, positions, scale=1):
    p = positions
    data = []
    data.append(b'\x00' * 80)
    data.append(struct.pack('<I', len(p) // 3))
    for vertices in zip(p[::3], p[1::3], p[2::3]):
        data.append(struct.pack('<fff', 0.0, 0.0, 0.0))
        for x, y, z in vertices:
            data.append(struct.pack('<fff', x * scale, y * scale, z * scale))
        data.append(struct.pack('<H', 0))
    data = b''.join(data)
    with open(path, 'wb') as fp:
        fp.write(data)

def simplify_path(points, tolerance):
    if len(points) < 2:
        return points
    line = geometry.LineString(points)
    line = line.simplify(tolerance, preserve_topology=False)
    return list(line.coords)

def main():
    print('loading image')
    im = Image.open(sys.argv[1])
    w, h = im.size
    scale = outputSize / max(w, h)
    printedHeight = zScale * scale
    numLayers = int(math.ceil(printedHeight / layerThickness))

    print('printed height =', printedHeight)
    print('num layers =', numLayers)

    z = np.asarray(im) / 65535
    f = interpolate.RectBivariateSpline(np.arange(z.shape[0]), np.arange(z.shape[1]), z * zScale)

    print('computing contours')
    contours = []
    n = numLayers
    for i in range(n+1):
        t = i / n
        contours.extend(measure.find_contours(z, t))

    print('creating point set')
    points = set()
    for n, contour in enumerate(contours):
        path = [(x, y) for x, y in contour]
        path = simplify_path(path, 0.25)
        points |= set(path)
    print(len(points))

    bx0 = min(x for x, _ in points)
    by0 = min(y for _, y in points)
    bx1 = max(x for x, _ in points)
    by1 = max(y for _, y in points)
    points.add((bx0, by0))
    points.add((bx1, by0))
    points.add((bx0, by1))
    points.add((bx1, by1))
    points = list(points)

    print('triangulating')
    tri = DelaunayTri(points)
    print(len(tri.vertices))
    print(len(tri.points))

    print('computing z values')
    zs = dict(((x, y), f(x, y)[0][0]) for x, y in points)

    print('building positions')
    positions = []
    for i0, i1, i2 in tri.vertices:
        x0, y0 = tri.points[i0]
        x1, y1 = tri.points[i1]
        x2, y2 = tri.points[i2]
        z0 = zs[(x0, y0)]
        z1 = zs[(x1, y1)]
        z2 = zs[(x2, y2)]
        positions.append((y0, -x0, z0))
        positions.append((y1, -x1, z1))
        positions.append((y2, -x2, z2))

    print('building sides and bottom')
    z = -baseThickness / scale
    positions.append((by0, -bx0, z))
    positions.append((by1, -bx1, z))
    positions.append((by0, -bx1, z))
    positions.append((by0, -bx0, z))
    positions.append((by1, -bx0, z))
    positions.append((by1, -bx1, z))
    points_bx0 = list(sorted([(x, y) for x, y in points if abs(x-bx0) < 1e-9], key=lambda p: p[1]))
    points_by0 = list(sorted([(x, y) for x, y in points if abs(y-by0) < 1e-9], key=lambda p: p[0]))
    points_bx1 = list(sorted([(x, y) for x, y in points if abs(x-bx1) < 1e-9], key=lambda p: p[1]))
    points_by1 = list(sorted([(x, y) for x, y in points if abs(y-by1) < 1e-9], key=lambda p: p[0]))
    for (x0, y0), (x1, y1) in zip(points_bx0, points_bx0[1:]):
        z0 = zs[(x0, y0)]
        z1 = zs[(x1, y1)]
        positions.append((y0, -x0, z))
        positions.append((y0, -x0, z0))
        positions.append((y1, -x1, z1))
        positions.append((y0, -x0, z))
        positions.append((y1, -x1, z1))
        positions.append((y1, -x1, z))
    for (x0, y0), (x1, y1) in zip(points_bx1, points_bx1[1:]):
        z0 = zs[(x0, y0)]
        z1 = zs[(x1, y1)]
        positions.append((y0, -x0, z))
        positions.append((y1, -x1, z1))
        positions.append((y0, -x0, z0))
        positions.append((y0, -x0, z))
        positions.append((y1, -x1, z))
        positions.append((y1, -x1, z1))
    for (x0, y0), (x1, y1) in zip(points_by0, points_by0[1:]):
        z0 = zs[(x0, y0)]
        z1 = zs[(x1, y1)]
        positions.append((y0, -x0, z))
        positions.append((y1, -x1, z1))
        positions.append((y0, -x0, z0))
        positions.append((y0, -x0, z))
        positions.append((y1, -x1, z))
        positions.append((y1, -x1, z1))
    for (x0, y0), (x1, y1) in zip(points_by1, points_by1[1:]):
        z0 = zs[(x0, y0)]
        z1 = zs[(x1, y1)]
        positions.append((y0, -x0, z))
        positions.append((y0, -x0, z0))
        positions.append((y1, -x1, z1))
        positions.append((y0, -x0, z))
        positions.append((y1, -x1, z1))
        positions.append((y1, -x1, z))

    print('writing stl')
    save_binary_stl('out.stl', positions, scale)

if __name__ == '__main__':
    main()
