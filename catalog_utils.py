import bpy
import os

try:
  from asset_browser_utilities.module.catalog.tool import CatalogsHelper
except ImportError:
  print("The asset browser utilities from https://github.com/Gorgious56/asset_browser_utilities/ need to be installed.")


def get_all_descendants(root):
  for child in root.children:
    yield child
    yield from get_all_descendants(child)


def exclude_collection(bpy_collection, context):
  for lc in get_all_descendants(context.view_layer.layer_collection):
    if bpy_collection == lc.collection:
      lc.exclude = True
      break
  else:
    raise ValueError


def create_collection_instance(bpy_collection, context):
  collection_instance = bpy.data.objects.new(name=bpy_collection.name, object_data=None)
  context.scene.collection.objects.link(collection_instance)
  collection_instance.instance_type = 'COLLECTION'
  collection_instance.instance_collection = bpy_collection
  collection_instance.empty_display_size = 0.1
  return collection_instance


def get_parking_lot_size(n_cars, ratio):
  counter = 1
  while True:
    if (counter * counter * ratio) > n_cars:
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
  extended_catalog_name = "gscatter/" + \
      os.path.normpath(bpy.data.filepath).split("\\")[9].split("_")[0] + "/" + catalog_name
  catalog_uuid = cat_helper.ensure_or_create_catalog_definition(extended_catalog_name)
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


def unlink_object_from_all_collections(bpy_object):
  for col in bpy_object.users_collection:
    col.objects.unlink(bpy_object)


def collectionize_root_empty(bpy_object):
  parent_col = bpy_object.users_collection[0]
  new_col = bpy.data.collections.new(name=bpy_object.name)
  parent_col.children.link(new_col)
  unlink_object_from_all_collections(bpy_object)
  new_col.objects.link(bpy_object)
  for obj in bpy_object.children_recursive:
    unlink_object_from_all_collections(obj)
    new_col.objects.link(obj)
