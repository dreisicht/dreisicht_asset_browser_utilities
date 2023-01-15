import bpy
from dreisicht_asset_browser_utilities import core
from dreisicht_asset_browser_utilities.core import ConvertCollectionsToCatalogs, AddTagToObjects, AddTagToCollections, DabuPanel, NameCollectionLikeFile, ParkObjects, MoveObjectsCollection
import importlib
import sys

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
                       DabuPanel, NameCollectionLikeFile, ParkObjects,
                       MoveObjectsCollection]


def register():
  importlib.reload(core)
  for cls in to_register_classes:
    bpy.utils.register_class(cls)


def unregister():
  for cls in reversed(to_register_classes):
    bpy.utils.unregister_class(cls)
    del cls


if __name__ == "__main__":
  register()
