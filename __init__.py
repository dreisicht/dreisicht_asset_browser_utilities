import bpy
from dreisicht_asset_browser_utilities import main
import importlib

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

to_register_classes = [main.ConvertCollectionsToCatalogs,
                       main.AddTagToObjects,
                       main.AddTagToCollections,
                       main.DabuPanel,
                       main.NameCollectionLikeFile,
                       main.GridObject,
                       main.MoveObjectsCollection,
                       main.SortSelectedObjectsToCollections]


def register():
  importlib.reload(main)
  for cls in to_register_classes:
    bpy.utils.register_class(cls)


def unregister():
  for cls in reversed(to_register_classes):
    bpy.utils.unregister_class(cls)
    del cls


if __name__ == "__main__":
  register()
