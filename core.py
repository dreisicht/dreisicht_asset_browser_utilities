import bpy
import importlib.util
import sys
import os

spec = importlib.util.spec_from_file_location(
    "asset_browser_utilities", "C:/Users/peter/AppData/Roaming/Blender Foundation/Blender/3.4/scripts/addons/asset_browser_utilities/__init__.py")
abu = importlib.util.module_from_spec(spec)
sys.modules["asset_browser_utilities"] = abu
spec.loader.exec_module(abu)
from asset_browser_utilities.module.catalog.tool import CatalogsHelper


def get_parking_lot_size(n_cars):
  counter = 1
  while True:
    if (counter * counter * 4) > n_cars:
      return counter
    counter += 1


def get_parent_collections_name(collection, parent_names):
  for parent_collection in bpy.data.collections:
    if collection.name in parent_collection.children.keys():
      parent_names.append(parent_collection.name)
      get_parent_collections_name(parent_collection, parent_names)
      return


def get_parent_collection(collection):
  if collection.name in bpy.context.scene.collection.children:
    return bpy.context.scene.collection
  for col in bpy.data.collections:
    if collection.name in col.children:
      return col


def get_collection_path_absolute(bpy_collection):
  parent_names = []
  parent_names.append(bpy_collection.name)
  get_parent_collections_name(bpy_collection, parent_names)
  parent_names.reverse()
  return '/'.join(parent_names)


def check_if_collection_has_asset_objects(bpy_collection):
  for col in bpy_collection.children_recursive:
    for obj in col.objects:
      if obj.asset_data:
        return True
  return False


def check_if_collection_has_asset_collections(bpy_collection):
  for col in bpy_collection.children_recursive:
    if col.asset_data:
      return True
  return False


def check_if_collection_has_any_assets(bpy_collection):
  for col in bpy_collection.children_recursive:
    if col.asset_data:
      return True
    for obj in col.objects:
      if obj.asset_data:
        return True
  for obj in bpy_collection.objects:
    if obj.asset_data:
      return True
  return False


def mark_data_with_tag(bpy_obj_or_col_list, tag):
  print(tag, bpy_obj_or_col_list)
  for obj_or_col in bpy_obj_or_col_list:
    if not obj_or_col.asset_data:
      continue
    new_tag = obj_or_col.asset_data.tags.new(tag)
    new_tag.name = tag


def add_assets_to_catalog(bpy_collection, catalog_name):
  cat_helper = CatalogsHelper()
  # The function ensure_or_create_catalog_definition takes as input a string for the name of the asset catalog.
  catalog_uuid = cat_helper.ensure_or_create_catalog_definition(catalog_name)
  # Add all objects marked as asset of the collection to the asset catalog
  for obj in bpy_collection.objects:
    if obj.asset_data:
      obj.asset_data.catalog_id = catalog_uuid
  # Add all child collections marked as asset to the catalog
  for col in bpy_collection.children:
    if col.asset_data:
      col.asset_data.catalog_id = catalog_uuid


def convert_collections_to_asset_catalog(parent_collection):
  # Recursively adds all collections to the asset catalog
  if not parent_collection.children:
    return
  for child_collection in parent_collection.children:
    if not check_if_collection_has_any_assets(child_collection):
      continue
    add_assets_to_catalog(child_collection, get_collection_path_absolute(child_collection))
    convert_collections_to_asset_catalog(child_collection)


class ConvertCollectionsToCatalogs(bpy.types.Operator):
  """Converts the collection hierarchy into an Asset Blayoutser catalog hierarchy."""
  bl_idname = "scene.convert_collections_to_catalogs"
  bl_label = "Convert Collections to Asset Catalogs"
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    convert_collections_to_asset_catalog(context.scene.collection)
    return {'FINISHED'}


class AddTagToObjects(bpy.types.Operator):
  """Adds the tag to the selected objects."""
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
    mark_data_with_tag(context.selected_objects, self.tag)
    return {'FINISHED'}


class AddTagToCollections(bpy.types.Operator):
  """Adds the tag to the selected Collections."""
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
      mark_data_with_tag(context.selected_ids, self.tag)

    return {'FINISHED'}


class ParkObjects(bpy.types.Operator):
  bl_idname = "scene.park_objects"
  bl_label = "Aligns the objects to a grid."
  bl_options = {'REGISTER', 'UNDO'}

  @classmethod
  def poll(cls, context):
    return context.active_object is not None

  def execute(self, context):
    y_size = get_parking_lot_size(len(context.selected_objects))
    counter = 0
    for bpy_object in context.selected_objects:
      # Safety checks
      if bpy_object.type == "EMPTY" and bpy_object.parent:
        print(bpy_object, bpy_object.parent)
        raise NotImplementedError

      if bpy_object.parent:
        continue
      n_col = counter % y_size
      n_row = counter // y_size
      print(n_row, n_col, counter, bpy_object)
      bpy_object.location = (n_row * 2.3, n_col * 8, 0)
      counter += 1
    return {'FINISHED'}


class MoveObjectsCollection(bpy.types.Operator):
  bl_idname = "scene.move_objects_collection"
  bl_description = "Moves all collections that contain the selected objects to the specified collection."
  bl_label = "Move Objects' Collection"
  bl_options = {"REGISTER", "UNDO"}

  # Not working because of AttributeError: 'MoveObjectsCollection' object has no attribute 'to_collection'
  # to_collection: bpy.props.PointerProperty(type=bpy.types.Collection)

  @classmethod
  def poll(cls, context):
    return context.selected_objects is not None

  def execute(self, context):
    for obj in context.selected_objects:
      col = obj.users_collection[0]
      print(col)
      if col.name in bpy.context.collection.children:
        continue
      get_parent_collection(col).children.unlink(col)
      bpy.context.collection.children.link(col)

    return {"FINISHED"}


class NameCollectionLikeFile(bpy.types.Operator):
  bl_idname = "scene.name_collection_like_file"
  bl_label = "Name Collection like file"
  bl_description = "Copies the file name of the .blend file and renames the collection to that name."
  bl_options = {"REGISTER", "UNDO"}

  @classmethod
  def poll(cls, context):
    return context.collection is not None

  def execute(self, context):
    context.collection.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
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
# convert_collections_to_asset_catalog(bpy.context.scene.collection)
