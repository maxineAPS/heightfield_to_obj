import numpy as np
from PIL import Image

def load_obj(obj_path):
    """
    Loads the vertices, faces, and UV coordinates from an OBJ file.
    
    Parameters:
    - obj_path (str): The path to the input OBJ file.
    
    Returns:
    - vertices (list of tuples): The list of vertices (x, y, z).
    - faces (list of tuples): The list of faces (as tuples of vertex indices).
    - uvs (list of tuples): The list of UV coordinates for each vertex.
    """
    vertices = []
    faces = []
    uvs = []

    with open(obj_path, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == 'v':  # Vertices
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif parts[0] == 'f':  # Faces
                face = [int(v.split('/')[0]) - 1 for v in parts[1:]]
                faces.append(tuple(face))
            elif parts[0] == 'vt':  # UV coordinates
                uvs.append((float(parts[1]), float(parts[2])))

    return vertices, faces, uvs

def save_obj(filename, vertices, faces):
    """
    Saves the vertices and faces of a 3D model to an OBJ file.
    
    Parameters:
    - filename (str): The path to the output OBJ file.
    - vertices (list of tuples): The list of vertices (x, y, z).
    - faces (list of tuples): The list of faces (as tuples of vertex indices).
    """
    with open(filename, 'w') as f:
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")

def calculate_face_normal(v0, v1, v2):
    """
    Calculates the normal of a face given three vertices.
    
    Parameters:
    - v0, v1, v2 (tuple): The coordinates of the three vertices of the face.
    
    Returns:
    - normal (tuple): The normalized normal vector of the face.
    """
    v0 = np.array(v0)
    v1 = np.array(v1)
    v2 = np.array(v2)

    # Calculate two edge vectors
    edge1 = v1 - v0
    edge2 = v2 - v0

    # Cross product to get the face normal
    normal = np.cross(edge1, edge2)

    # Normalize the normal
    normal /= np.linalg.norm(normal)
    
    return normal

def apply_heightfield_to_obj(obj_path, heightmap_path, output_path, displacement_scale=1.0):
    """
    Applies a heightmap to an OBJ model by displacing its vertices based on their UV coordinates and the face normals.

    Parameters:
    - obj_path (str): The path to the input OBJ file.
    - heightmap_path (str): The path to the heightmap image.
    - output_path (str): The path to the output OBJ file.
    - displacement_scale (float): Scale factor for the heightfield displacement.
    """
    # Step 1: Load the OBJ file (vertices, faces, and UVs)
    vertices, faces, uvs = load_obj(obj_path)

    # Step 2: Load the heightmap image and normalize it to [0, 1]
    heightmap = Image.open(heightmap_path).convert('L')
    heightmap_array = np.array(heightmap) / 255.0  # Normalize pixel values between 0 and 1
    h_map, w_map = heightmap_array.shape

    # Step 3: Displace the vertices using the heightmap and face normals
    displaced_vertices = np.array(vertices)
    for face in faces:
        # Get the three vertices of the face
        v0_idx, v1_idx, v2_idx = face[0], face[1], face[2]
        v0, v1, v2 = vertices[v0_idx], vertices[v1_idx], vertices[v2_idx]

        # Calculate the face normal
        normal = calculate_face_normal(v0, v1, v2)

        for i in face:
            # Get the corresponding UV coordinate (normalized in the range [0, 1])
            uv = uvs[i]
            u, v = uv[0], uv[1]

            # Find the heightmap value corresponding to the UV coordinates
            # Scale UV coordinates to map them to the heightmap array
            u_idx = int(u * (w_map - 1))
            v_idx = int((1 - v) * (h_map - 1))  # Flip the V-axis for proper mapping

            height_value = heightmap_array[v_idx, u_idx]  # Get heightmap value

            # Step 4: Displace the vertex in the direction of the face normal
            displacement = normal * height_value * displacement_scale
            displaced_vertices[i] = displaced_vertices[i] + displacement

    # Step 5: Save the displaced OBJ file
    save_obj(output_path, displaced_vertices, faces)

    print(f"Displaced mesh saved to {output_path}")

if __name__ == "__main__":
    obj_path = '/Users/maxine/Desktop/cube.obj'  # The 3D object you want to displace
    heightmap_path = '/Users/maxine/Downloads/1_casino_navy_stitched.jpg'  # The path to the heightmap image
    output_path = 'output.obj'  # The path to save the displaced OBJ file
    apply_heightfield_to_obj(obj_path, heightmap_path, output_path, displacement_scale=0.01)
