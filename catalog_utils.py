import bpy

try:
  from asset_browser_utilities.module.catalog.tool import CatalogsHelper
except ImportError:
  print("The asset browser utilities from https://github.com/Gorgious56/asset_browser_utilities/ need to be installed.")


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
