import bpy
import mathutils
import os

from dreisicht_asset_browser_utilities import catalog_utils
from dreisicht_asset_browser_utilities import get_intersecting_bounding_boxes


class ConvertCollectionsToCatalogs(bpy.types.Operator):
  """Converts the hierarchy of collections into an Asset Browser catalog hierarchy. Only collections with marked assets are being taken into account"""
  bl_idname = "scene.convert_collections_to_catalogs"
  bl_label = "Convert Collections to Asset Catalogs"
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    catalog_utils.convert_collections_to_asset_catalog(context.scene.collection)
    return {'FINISHED'}


class AddTagToObjects(bpy.types.Operator):
  """Adds the tag to the selected objects"""
  bl_idname = "scene.add_tag_to_objects"
  bl_label = "Adds the given tag to all "
  bl_options = {'REGISTER', 'UNDO'}

  tag: bpy.props.StringProperty()

  @classmethod
  def poll(cls, context):
    return context.active_object is not None

  def invoke(self, context, event):
    return context.window_manager.invoke_props_dialog(self)

  def execute(self, context):
    catalog_utils.mark_data_with_tag(context.selected_objects, self.tag)
    return {'FINISHED'}


class AddTagToCollections(bpy.types.Operator):
  """Adds the tag to the selected Collections"""
  bl_idname = "scene.add_tag_to_collections"
  bl_label = "Adds the given tag to all"
  bl_options = {'REGISTER', 'UNDO'}

  tag: bpy.props.StringProperty()

  @classmethod
  def poll(cls, context):
    return context.active_object is not None

  def invoke(self, context, event):
    return context.window_manager.invoke_props_dialog(self)

  def execute(self, context):
    outliner_area = None
    for area in bpy.context.screen.areas:
      if area.type == "OUTLINER":
        outliner_area = area
        break
    else:
      self.report({"ERROR"}, "No outliner visible!")
      return {"CANCELLED"}
    with context.temp_override(area=outliner_area):
      catalog_utils.mark_data_with_tag(context.selected_ids, self.tag)

    return {'FINISHED'}


class GridObject(bpy.types.Operator):
  bl_idname = "scene.park_objects"
  bl_description = "Aligns all objects to a grid"
  bl_label = "Aligns the objects to a grid"
  bl_options = {'REGISTER', 'UNDO'}

  x_size: bpy.props.FloatProperty(default=2.3)
  y_size: bpy.props.FloatProperty(default=8)

  @classmethod
  def poll(cls, context):
    return context.active_object is not None

  def execute(self, context):
    y_size = catalog_utils.get_parking_lot_size(len(context.selected_objects))
    counter = 0
    for bpy_object in context.selected_objects:
      # Safety checks
      if bpy_object.parent:
        continue
      if bpy_object.type == "EMPTY" and bpy_object.parent:
        raise NotImplementedError

      n_col = counter % y_size
      n_row = counter // y_size
      bpy_object.location = mathutils.Vector(
          (n_row * self.x_size, n_col * self.y_size, 0)) + context.scene.cursor.location
      counter += 1
    return {'FINISHED'}


class MoveObjectsCollection(bpy.types.Operator):
  bl_idname = "scene.move_objects_collection"
  bl_description = "Moves all collections that contain the selected objects to the active collection"
  bl_label = "Move Objects' Collection"
  bl_options = {"REGISTER", "UNDO"}

  # Not working because of AttributeError: 'MoveObjectsCollection' object has no attribute 'to_collection'
  # to_collection: bpy.props.PointerProperty(type=bpy.types.Collection)

  @classmethod
  def poll(cls, context):
    return context.selected_objects != []

  def execute(self, context):
    for obj in context.selected_objects:
      col = obj.users_collection[0]
      if col.name in bpy.context.collection.children:
        continue
      catalog_utils.get_parent_collection(col).children.unlink(col)
      bpy.context.collection.children.link(col)

    return {"FINISHED"}


class NameCollectionLikeFile(bpy.types.Operator):
  bl_idname = "scene.name_collection_like_file"
  bl_label = "Name Collection like file"
  bl_description = "Copies the file name of the .blend file and renames the collection to that name"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context):
    return context.collection is not None

  def execute(self, context):
    context.collection.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    return {"FINISHED"}


class SortSelectedObjectsToCollections(bpy.types.Operator):
  bl_idname = "scene.sort_objects_to_collections"
  bl_label = "Contacting Objects to Collections"
  bl_description = "Gets all objects in contact from the selected objects and sorts them into collections. Name of the collection is determined from the first object. The bounding box is being used for contact determination and might not be always precise"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context):
    return context.selected_objects is not None

  def execute(self, context):
    original_intersects = get_intersecting_bounding_boxes.get_all_intersects(bpy.context.selected_objects)
    for group in get_intersecting_bounding_boxes.get_node_groups(original_intersects):
      get_intersecting_bounding_boxes.move_list_of_objects_to_collection(group)
    return {"FINISHED"}


class DabuPanel(bpy.types.Panel):
  bl_idname = "SCENE_PT_dabu"
  bl_label = "DABU"
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = "Item"

  @classmethod
  def poll(cls, context):
    return (context.object is not None)

  def draw(self, context):
    layout = self.layout
    layout.operator("scene.convert_collections_to_catalogs", icon="CURRENT_FILE", text="Collections to Catalog")
    col = layout.column(align=True)
    col.operator("scene.add_tag_to_objects", icon="OBJECT_DATA", text="Add Object Tag")
    col.operator("scene.add_tag_to_collections", icon="OUTLINER_COLLECTION", text="Add Collection Tag")
    col = layout.column(align=True)
    col.operator("scene.name_collection_like_file", icon="FILE_TEXT")
    col.operator("scene.move_objects_collection", icon="OUTLINER")
    col.operator("scene.park_objects", icon="LIGHTPROBE_GRID")
    col.operator("scene.sort_objects_to_collections", icon="PIVOT_BOUNDBOX")
