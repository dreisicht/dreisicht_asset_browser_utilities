"""All dependencies for getting intersecting bounding boxes."""

import bpy
from mathutils import Vector

EXTRA_DELTA = 0.001


def check_one_axis(a, b):
  min_a = min(a) - EXTRA_DELTA
  max_a = max(a) + EXTRA_DELTA
  min_b = min(b) - EXTRA_DELTA
  max_b = max(b) + EXTRA_DELTA
  return (min_a <= min_b and min_b <= max_a) or (min_b <= min_a and min_a <= max_b)


def check_if_cube_within_cube(verts_cube_a, verts_cube_b, mat_a, mat_b):
  verts_cube_a = convert_vector_list_in_float_tuples([mat_a @ v for v in verts_cube_a])
  verts_cube_b = convert_vector_list_in_float_tuples([mat_b @ v for v in verts_cube_b])

  for i in range(3):
    if not check_one_axis([co[i] for co in verts_cube_a], [co[i] for co in verts_cube_b]):
      return False
  return True


def convert_vector_list_in_float_tuples(vector_list):
  float_tuples = []
  for vector in vector_list:
    float_tuples.append((vector.x, vector.y, vector.z))
  return float_tuples


def are_bounding_boxs_intersecting(obj_a, obj_b):
  return check_if_cube_within_cube([Vector(co) for co in obj_a.bound_box], [Vector(co)
                                                                            for co in obj_b.bound_box], obj_a.matrix_world, obj_b.matrix_world)


def get_intersects(obj, others):
  intersects = []
  for oob in others:
    if are_bounding_boxs_intersecting(obj, oob):
      intersects.append(oob)
  return intersects


def get_all_intersects(bpy_objects):
  all_intersects = {}
  bpy_objects = set(ob for ob in bpy_objects if ob.type == "MESH")
  for active_object in bpy_objects:
    other_objects = bpy_objects - {active_object}
    all_intersects[active_object] = get_intersects(active_object, other_objects)
  return all_intersects


def bfs(graph, start_node):
  visited = set()
  # visited.add(start_node)
  queue = [start_node]
  while queue:
    m = queue.pop(0)
    for neighbour in graph[m]:
      if neighbour not in visited:
        visited.add(neighbour)
        queue.append(neighbour)
  return tuple(visited)


def get_node_groups(graph):
  groups = set()
  all_visited = set()
  for node in graph:
    if node not in all_visited:
      node_group = tuple(bfs(graph, node))
      groups.add(node_group)
      for n in node_group:
        all_visited.add(n)
  return groups


def move_list_of_objects_to_collection(bpy_objects):
  if not bpy_objects:
    return
  new_col = bpy.data.collections.new(name=bpy_objects[0].name)
  bpy.context.scene.collection.children.link(new_col)
  for obj in bpy_objects:
    new_col.objects.link(obj)


def create_collection_groups():
  original_intersects = get_all_intersects(bpy.context.selected_objects)
  for group in get_node_groups(original_intersects):
    move_list_of_objects_to_collection(group)
