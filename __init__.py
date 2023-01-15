import bpy
from dreisicht_asset_browser_utilities.core import ConvertCollectionsToCatalogs, AddTagToObjects, AddTagToCollections, DabuPanel, NameCollectionLikeFile

bl_info = {
    "name": "dreisicht Asset Browser Utilities ",
    "author": "Peter Baintner",
    "description": "Asset Browser QOL tools and batch operations",
    "blender": (3, 4, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Import-Export",
}

to_register_classes = [ConvertCollectionsToCatalogs,
                       AddTagToObjects,
                       AddTagToCollections,
                       DabuPanel, NameCollectionLikeFile]


def register():
  for cls in to_register_classes:
    bpy.utils.register_class(cls)


def unregister():
  for cls in to_register_classes:
    bpy.utils.unregister_class(cls)


if __name__ == "__main__":
  register()
