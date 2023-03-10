import bpy
import mathutils
import os
from copy import deepcopy

from dreisicht_asset_browser_utilities import catalog_utils
from dreisicht_asset_browser_utilities import get_intersecting_bounding_boxes


class ConvertCollectionsToCatalogs(bpy.types.Operator):
  """Converts the hierarchy of collections into an Asset Browser catalog hierarchy. Only collections with marked assets are being taken into account"""
  bl_idname = "scene.convert_collections_to_catalogs"
  bl_label = "Convert Collections to Asset Catalogs"
  bl_options = {'REGISTER', 'UNDO'}

  @classmethod
  def poll(cls, context):
    return context.collection is not None and context.collection is not context.scene.collection

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
    if context.active_object is not None and context.selected_objects != []:
      return False
    for ob in context.selected_objects:
      if not ob.asset_data:
        return False
    return True

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
    return context.collection is not None and context.collection is not context.scene.collection

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
  bl_idname = "scene.gridify_objects"
  bl_description = "Aligns all objects to a grid"
  bl_label = "Aligns the objects to a grid"
  bl_options = {'REGISTER', 'UNDO'}

  x_size: bpy.props.FloatProperty(default=2.3)
  y_size: bpy.props.FloatProperty(default=8)

  @classmethod
  def poll(cls, context):
    return context.active_object is not None and context.selected_objects != []

  def execute(self, context):
    y_size = catalog_utils.get_parking_lot_size(len(context.selected_objects), (self.y_size / self.x_size))
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
  bl_idname = "scene.subordinate_objects_collection"
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
    return context.collection is not None and context.collection is not context.scene.collection

  def execute(self, context):
    context.collection.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    return {"FINISHED"}


class SortSelectedObjectsToCollections(bpy.types.Operator):
  bl_idname = "scene.contacting_objects_to_collections"
  bl_label = "Contacting Objects to Collections"
  bl_description = "Gets all objects in contact from the selected objects and sorts them into collections. Name of the collection is determined from the first object. The bounding box is being used for contact determination and might not be always precise"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context):
    return context.active_object is not None and context.selected_objects != []

  def execute(self, context):
    if len(context.selected_objects) == 1:
      get_intersecting_bounding_boxes.move_list_of_objects_to_collection(context.selected_objects)
      return {"FINISHED"}
    original_intersects = get_intersecting_bounding_boxes.get_all_intersects(bpy.context.selected_objects)
    for group in get_intersecting_bounding_boxes.get_node_groups(original_intersects):
      get_intersecting_bounding_boxes.move_list_of_objects_to_collection(group)
    return {"FINISHED"}


class CollectionizeObject(bpy.types.Operator):
  bl_idname = "scene.collectionize_object"
  bl_label = "Collectionize Objects"
  bl_description = "Moves the empty and the children of the empty into a newly created collection"
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context):
    return context.selected_objects is not None

  def execute(self, context):
    for obj in context.selected_objects:
      if obj.parent:
        continue
      catalog_utils.collectionize_root_empty(obj)
    return {"FINISHED"}


class GroupByName(bpy.types.Operator):
  bl_idname = "scene.group_by_name"
  bl_label = "Group by Name"
  bl_description = "Groups all objects in the scene by names"
  bl_options = {"REGISTER", "UNDO"}

  group_identifier: bpy.props.StringProperty(name="Group Identifier")

  def execute(self, context):
    for obj in bpy.data.objects:
      if not "group_name" in obj.name:
        continue
      group_name = obj.name[:-3]
      group_collection = bpy.data.collections.get(group_name)
      if not group_collection:
        group_collection = bpy.data.collections.new(name=group_name)
      group_collection.objects.link(obj)
    return {"FINISHED"}


class AutoMarkCollectionsAsAssets(bpy.types.Operator):
  bl_idname = "scene.mark_collections_as_assets"
  bl_label = "Auto mark collections as assets"
  bl_description = "Marks all collections as assets, that don't have child assets"
  bl_options = {"REGISTER", "UNDO"}

  def execute(self, context):
    return {"FINISHED"}


class ConvertCollectionsToInstances(bpy.types.Operator):
  bl_idname = "scene.convert_collections_to_instances"
  bl_label = "Convert Collections ot Instances"
  bl_description = "Replaces the objects in the scene with correctly placed collection instances. "
  bl_options = {"REGISTER", "UNDO"}

  def execute(self, context):
    for col in bpy.data.collections:
      if not col.asset_data:
        continue
      root_objects = []
      for ob in col.objects:
        if ob.parent:
          continue
        root_objects.append(ob)
      if len(root_objects) > 1:
        raise NotImplementedError("There are more than one roots in the collection, which is not supported.")
      original_location = deepcopy(root_objects[0].location)
      root_objects[0].location = mathutils.Vector((0, 0, 0))
      collection_instance = catalog_utils.create_collection_instance(col, context)
      collection_instance.location = original_location
      catalog_utils.exclude_collection(col, context)
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
    col = layout.column(align=True)
    col.label(text="Tags")
    col.operator("scene.add_tag_to_objects", icon="OBJECT_DATA", text="Add Object Tag")
    col.operator("scene.add_tag_to_collections", icon="OUTLINER_COLLECTION", text="Add Collection Tag")

    col = layout.column(align=True)
    col.label(text="Change objects")
    col.operator("scene.gridify_objects", icon="LIGHTPROBE_GRID")

    col = layout.column(align=True)
    col.label(text="Create collections")
    col.operator("scene.contacting_objects_to_collections", icon="PIVOT_BOUNDBOX")
    col.operator("scene.collectionize_object", icon="GROUP")
    col.operator("scene.group_by_name", icon="FILE_FONT")

    col = layout.column(align=True)
    col.label(text="Edit collections")
    col.operator("scene.subordinate_objects_collection", icon="OUTLINER")
    col.operator("scene.name_collection_like_file", icon="FILE_TEXT")
    col.operator("scene.convert_collections_to_catalogs", icon="CURRENT_FILE", text="Collections to Catalog")
    col.operator("scene.mark_collections_as_assets", icon="ASSET_MANAGER")
    col.operator("scene.convert_collections_to_instances",
                 icon="OUTLINER_OB_GROUP_INSTANCE", text="Collections to Instances")
