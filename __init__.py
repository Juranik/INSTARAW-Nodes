"""
ComfyUI INSTARAW
A general-purpose custom nodes package by Instara

INSTARAW is a collection of powerful custom nodes for ComfyUI that brings together
hard-to-install dependencies and integrations in one convenient package.

Features:
- API Integrations: SeeDream, Ideogram, and more
- Easy Installation: Pre-packaged dependencies
- Modular Design: Easy to extend and customize
- INSTARAW Brand: Where we push the boundaries

Created by Instara
"""

import os
import sys
import importlib

# ─── FIX: Namespace collision between ComfyUI's global `nodes` module
# and our local `nodes/` sub-package.
#
# ComfyUI loads custom nodes by directly exec'ing __init__.py via importlib.
# The `custom_nodes/` directory is a namespace package, so when we do
# `from .nodes import ...`, Python may resolve `.nodes` against the
# *already-loaded* ComfyUI `nodes` module instead of our local `nodes/` folder.
#
# Solution: Explicitly import our `nodes` sub-package using its full filesystem
# path, bypassing the broken relative import resolution entirely.
# ───

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_NODES_PKG_DIR = os.path.join(_THIS_DIR, "nodes")

# Register JS web extensions with ComfyUI
try:
    _comfyui_nodes = importlib.import_module("nodes")
    if "ComfyUI_INSTARAW" not in _comfyui_nodes.EXTENSION_WEB_DIRS:
        _comfyui_nodes.EXTENSION_WEB_DIRS["ComfyUI_INSTARAW"] = os.path.join(_THIS_DIR, "js")
except Exception:
    pass  # Not critical if it fails

# ─── Direct import of our nodes sub-package ───
# We import each sub-package's __init__.py manually to collect NODE_CLASS_MAPPINGS.

def _import_subpackage(parent_pkg_name, subpkg_name, subpkg_dir):
    """Import a sub-package by inserting its parent into sys.path temporarily."""
    init_file = os.path.join(subpkg_dir, "__init__.py")
    if not os.path.isfile(init_file):
        return {}, {}

    full_name = f"{parent_pkg_name}.{subpkg_name}"
    
    # Use importlib to load from file path
    spec = importlib.util.spec_from_file_location(full_name, init_file,
        submodule_search_locations=[subpkg_dir])
    if spec is None:
        return {}, {}
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    
    # Ensure the parent package is registered so relative imports work
    parent_name = parent_pkg_name
    if parent_name not in sys.modules:
        sys.modules[parent_name] = sys.modules[__name__]
    
    spec.loader.exec_module(module)
    
    class_mappings = getattr(module, "NODE_CLASS_MAPPINGS", {})
    display_mappings = getattr(module, "NODE_DISPLAY_NAME_MAPPINGS", {})
    return class_mappings, display_mappings


# First, register ourselves and our nodes package in sys.modules
# so that relative imports from within sub-packages can resolve correctly.
_our_pkg_name = __name__  # e.g. "custom_nodes.ComfyUI_INSTARAW" or just "ComfyUI_INSTARAW"
_nodes_pkg_name = f"{_our_pkg_name}.nodes"

# Create a proper package module for "nodes"
_nodes_spec = importlib.util.spec_from_file_location(
    _nodes_pkg_name,
    os.path.join(_NODES_PKG_DIR, "__init__.py"),
    submodule_search_locations=[_NODES_PKG_DIR]
)

if _nodes_spec:
    _nodes_module = importlib.util.module_from_spec(_nodes_spec)
    sys.modules[_nodes_pkg_name] = _nodes_module
    # Also register our modules/ directory for relative imports from nodes
    _modules_dir = os.path.join(_THIS_DIR, "modules")
    _modules_pkg_name = f"{_our_pkg_name}.modules"
    if _modules_pkg_name not in sys.modules:
        _modules_spec = importlib.util.spec_from_file_location(
            _modules_pkg_name,
            os.path.join(_modules_dir, "__init__.py") if os.path.isfile(os.path.join(_modules_dir, "__init__.py")) else None,
            submodule_search_locations=[_modules_dir]
        )
        if _modules_spec:
            _modules_module = importlib.util.module_from_spec(_modules_spec)
            sys.modules[_modules_pkg_name] = _modules_module
            try:
                _modules_spec.loader.exec_module(_modules_module)
            except Exception:
                pass

    # Now exec the nodes __init__.py which will do all the sub-imports
    try:
        _nodes_spec.loader.exec_module(_nodes_module)
        NODE_CLASS_MAPPINGS = getattr(_nodes_module, "NODE_CLASS_MAPPINGS", {})
        NODE_DISPLAY_NAME_MAPPINGS = getattr(_nodes_module, "NODE_DISPLAY_NAME_MAPPINGS", {})
        print(f"[INSTARAW] ✅ Loaded {len(NODE_CLASS_MAPPINGS)} nodes successfully!")
    except Exception as e:
        print(f"[INSTARAW] ❌ Failed to load nodes package: {e}")
        import traceback
        traceback.print_exc()
        NODE_CLASS_MAPPINGS = {}
        NODE_DISPLAY_NAME_MAPPINGS = {}
else:
    print(f"[INSTARAW] ❌ Could not find nodes package at {_NODES_PKG_DIR}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

# Import creative API to register endpoints (after nodes are loaded)
try:
    creative_api_path = os.path.join(_NODES_PKG_DIR, "api_nodes", "creative_api.py")
    if os.path.isfile(creative_api_path):
        _api_spec = importlib.util.spec_from_file_location(
            f"{_nodes_pkg_name}.api_nodes.creative_api", creative_api_path)
        if _api_spec:
            _api_mod = importlib.util.module_from_spec(_api_spec)
            _api_spec.loader.exec_module(_api_mod)
except Exception as e:
    print(f"[INSTARAW] Warning: Could not load creative_api: {e}")
    print("[INSTARAW] Creative/Character generation features will not be available.")

# Required exports for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

# Package metadata
__version__ = "1.2.0"
__author__ = "Instara"
__description__ = "INSTARAW - General purpose custom nodes for ComfyUI"