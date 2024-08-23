import numpy as np
from PIL import Image

def save_obj(filename, vertices, faces):
    """
    Saves the vertices and faces of a 3D model to an OBJ file.

    Parameters:
    - filename (str): The path to the output OBJ file.
    - vertices (list of tuples): The list of vertices, where each vertex is represented as a tuple (x, y, z).
    - faces (list of tuples): The list of faces, where each face is represented as a tuple of vertex indices (1-based index).
    """
    with open(filename, 'w') as f:
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")

def rotate_x(vertices, angle_degrees):
    """
    Rotates the vertices around the X-axis by a given angle.

    Parameters:
    - vertices (list of tuples): The list of vertices to rotate.
    - angle_degrees (float): The angle in degrees by which to rotate the vertices around the X-axis.

    Returns:
    - rotated_vertices (list of tuples): The rotated list of vertices.
    """
    angle_radians = np.radians(angle_degrees)
    cos_angle = np.cos(angle_radians)
    sin_angle = np.sin(angle_radians)
    
    rotated_vertices = []
    for v in vertices:
        x, y, z = v
        y_new = y * cos_angle - z * sin_angle
        z_new = y * sin_angle + z * cos_angle
        rotated_vertices.append((x, y_new, z_new))
    
    return rotated_vertices

def generate_tile(heightmap_path, output_path, tile_size=100, base_thickness=3, z_add=0, target_size=5.0, full_field=True, res=100):
    """
    Generates a 3D tile model from a heightmap image and saves it as an OBJ file.

    Parameters:
    - heightmap_path (str): The path to the input heightmap image.
    - output_path (str): The path to the output OBJ file.
    - tile_size (float): The size of the tile in the X and Y dimensions (in arbitrary units).
    - base_thickness (float): The thickness of the base of the tile.
    - z_add (float): A value to add to the Z-coordinate (height) of all vertices, controlling the overall height of the tile.
    - target_size (float): The target width and height of the final 3D model (in cm).
    - full_field (bool): Whether to generate the full base and sides of the tile (True) or just the top surface (False).
    - res (int): The resolution to which the heightmap image should be downsampled (res x res).
    """
    print(f"Loading heightmap from: {heightmap_path}")
    im = Image.open(heightmap_path).convert('L')
    print(f"Original image size: {im.size}")

    # Downsample the image to res x res resolution
    print(f"Downsampling image to {res}x{res} resolution")
    im = im.resize((res, res), Image.LANCZOS)
    print(f"Downsampled image size: {im.size}")
    
    z = np.asarray(im) / 255.0  # Normalize pixel values between 0 and 1
    h, w = z.shape
    print(f"Image array shape: {z.shape}")
    
    # Scale heightmap to desired tile size
    scale_x = tile_size / w
    scale_y = tile_size / h
    z *= base_thickness
    print(f"Scaling image to tile size: {tile_size}x{tile_size}")
    
    # Apply absolute z_add to z heights before scaling
    z += z_add
    print(f"Applied z_add: {z_add}")
    
    # Generate vertices for the top surface
    vertices = []
    for y in range(h):
        for x in range(w):
            vertices.append((x * scale_x, y * scale_y, z[y, x]))
    print("Generated vertices for the top surface")

    if full_field:
        # Generate vertices for the base, using the same grid as the top surface
        base_vertices = [(x * scale_x, y * scale_y, -base_thickness) for y in range(h) for x in range(w)]
        vertices.extend(base_vertices)
        print("Generated vertices for the base")

        # Add the four corner vertices for the bottom face
        bottom_corners = [
            (0, 0, -base_thickness),
            (tile_size, 0, -base_thickness),
            (tile_size, tile_size, -base_thickness),
            (0, tile_size, -base_thickness)
        ]
        vertices.extend(bottom_corners)
        print("Added corner vertices for the bottom face")

    # Generate quads for the top surface
    faces = []
    for y in range(h - 1):
        for x in range(w - 1):
            i = y * w + x
            faces.append((i, i + 1, i + w + 1, i + w))
    print("Generated quads for the top surface")

    if full_field:
        # Generate quads for the sides
        for y in range(h - 1):
            for x in range(w - 1):
                i = y * w + x
                base_i = i + h * w

                # Front side
                if y == 0:
                    faces.append((i, i + 1, base_i + 1, base_i))

                # Back side
                if y == h - 2:
                    faces.append((i + w, i + w + 1, base_i + w + 1, base_i + w))

                # Left side
                if x == 0:
                    faces.append((i, i + w, base_i + w, base_i))

                # Right side
                if x == w - 2:
                    faces.append((i + 1, i + w + 1, base_i + w + 1, base_i + 1))

        # Correct the bottom face quad
        bottom_quad = (
            len(vertices) - 4,  # Bottom left
            len(vertices) - 3,  # Bottom right
            len(vertices) - 2,  # Top right
            len(vertices) - 1   # Top left
        )
        faces.append(bottom_quad)
        print("Generated quads for the sides and bottom")

    # Calculate the scaling factor to fit the slab within target_size x target_size cm
    max_dimension = max(tile_size, tile_size)
    scale_factor = target_size / max_dimension
    print(f"Calculated scale factor: {scale_factor}")

    # Apply the scale factor to x, y, and z coordinates (but not z_add)
    vertices = [(v[0] * scale_factor, v[1] * scale_factor, v[2] * scale_factor) for v in vertices]
    print("Applied scaling factor to all vertices")
    
    # Rotate the vertices by -90 degrees around the X-axis
    vertices = rotate_x(vertices, -90)
    print("Rotated vertices by -90 degrees around the X-axis")
    
    # Save to OBJ file
    save_obj(output_path, vertices, faces)
    print(f"Saved 3D model to {output_path}")

if __name__ == "__main__":
    heightmap_path = '/Users/maxine/Downloads/1_casino_navy_stitched.jpg'  # heightmap image path
    output_path = "output8.obj"  # output OBJ file path
    z_add = 0  # Manually tuned to match examples, controls height of block
    generate_tile(heightmap_path, output_path, z_add=z_add, target_size=5.0, full_field=False, res=100)  # Target size is width/height of block
