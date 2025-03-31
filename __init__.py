# BlenderWebPreview - Blender Addon for Web Preview and Export
# For Blender 4.0+

bl_info = {
    "name": "BlendXWeb",
    "author": "Egret",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > BlendXweb",
    "description": "Preview and export Blender scenes to web browsers",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import os
import sys
import json
import threading
import webbrowser
import shutil
import socket
import tempfile
from pathlib import Path
import subprocess

# Global server variable
preview_server = None

# ------------------------------------
# Server Component
# ------------------------------------

class WebPreviewServer:
    """Simple HTTP server to serve the Blender scene preview"""
    
    def __init__(self):
        self.server_process = None
        self.port = 3000  # Fixed port to 3000
        self.temp_dir = None
        self.is_running = False
        
    def find_available_port(self):
        """Find an available port for the server"""
        # Using fixed port 3000
        self.port = 3000
        return self.port
        
    def start_server(self):
        """Start the HTTP server"""
        if self.is_running:
            return
            
        # Create a temporary directory for serving files
        self.temp_dir = tempfile.mkdtemp()
        
        # Find an available port
        self.find_available_port()
        
        # Set up the server using Python's built-in HTTP server
        server_script = os.path.join(os.path.dirname(__file__), "server", "server.py")
        
        # Start the server process
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, server_script, str(self.port), self.temp_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.is_running = True
            print(f"Server started on port {self.port}")
        except Exception as e:
            print(f"Failed to start server: {e}")
            self.is_running = False
            
    def stop_server(self):
        """Stop the HTTP server"""
        if not self.is_running:
            return
            
        # Terminate the server process
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            
        # Clean up the temporary directory - with error handling
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Could not remove temp directory: {e}")
                # We'll just let it be and Windows will clean it up later
            self.temp_dir = None
            
        self.is_running = False
        print("Server stopped")
        
    def get_url(self):
        """Get the URL for the web preview"""
        if not self.is_running:
            return None
        return f"http://localhost:{self.port}"

# ------------------------------------
# Export Functions
# ------------------------------------

def export_scene_to_gltf(context, filepath, export_settings):
    """Export the current scene to glTF format"""
    
    # Configure export settings for glTF - using GLB format instead
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',  # Changed from GLTF_EMBEDDED to GLB
            export_selected=export_settings.get('export_selected', False),
            export_animations=export_settings.get('export_animations', True),
            export_cameras=export_settings.get('export_cameras', True),
            export_lights=export_settings.get('export_lights', True)
        )
    except TypeError as e:
        # If the above parameters don't work, try with minimal parameters
        print(f"Trying minimal export parameters due to error: {e}")
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB'  # Only use the format parameter
        )
    except Exception as e:
        print(f"Error during export: {e}")
        raise
    
    return filepath

def generate_preview_files(context, temp_dir):
    """Generate all necessary files for web preview"""
    # Export the scene to glTF
    gltf_path = os.path.join(temp_dir, "scene.glb")  # Using .glb format
    export_settings = {
        'export_selected': False,  # Export entire scene
        'export_animations': True,
        'export_cameras': True,
        'export_lights': True
    }
    export_scene_to_gltf(context, gltf_path, export_settings)
    
    # Copy the web viewer files
    viewer_files_dir = os.path.join(os.path.dirname(__file__), "web")
    
    # Ensure these key files exist and are not empty
    key_files = ['index.html', 'js/viewer.js', 'css/style.css']
    for file in key_files:
        source_file = os.path.join(viewer_files_dir, file)
        if not os.path.exists(source_file) or os.path.getsize(source_file) == 0:
            print(f"Warning: Required file {file} is missing or empty!")
            
    # First copy individual files to ensure they're properly handled
    index_source = os.path.join(viewer_files_dir, "index.html")
    index_dest = os.path.join(temp_dir, "index.html")
    
    if os.path.exists(index_source) and os.path.getsize(index_source) > 0:
        shutil.copy2(index_source, index_dest)
        print(f"Copied index.html: {os.path.getsize(index_dest)} bytes")
    else:
        print(f"Error: index.html is missing or empty! Path: {index_source}")
        # Create a basic index.html if missing
        with open(index_dest, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlendXweb | By Egret</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div id="container">
        <div id="viewer"></div>
        <div id="controls">
            <div id="info-panel">
                <h2 id="scene-title">Blender Scene</h2>
                <div id="scene-stats"></div>
            </div>
            <div id="control-panel">
                <div class="control-group">
                    <h3>Camera</h3>
                    <button id="btn-reset-camera">Reset Camera</button>
                    <div class="control-row">
                        <button id="btn-top-view">Top</button>
                        <button id="btn-front-view">Front</button>
                        <button id="btn-side-view">Side</button>
                    </div>
                </div>
                <div class="control-group">
                    <h3>Display</h3>
                    <div class="control-row">
                        <label>
                            <input type="checkbox" id="toggle-wireframe">
                            Wireframe
                        </label>
                    </div>
                    <div class="control-row">
                        <label>
                            <input type="checkbox" id="toggle-grid" checked>
                            Grid
                        </label>
                    </div>
                    <div class="control-row">
                        <label>
                            <input type="checkbox" id="toggle-lights" checked>
                            Lights
                        </label>
                    </div>
                </div>
                <div class="control-group" id="animation-controls">
                    <h3>Animation</h3>
                    <div class="control-row">
                        <button id="btn-play">Play</button>
                        <button id="btn-pause">Pause</button>
                        <button id="btn-stop">Stop</button>
                    </div>
                    <div class="control-row">
                        <input type="range" id="animation-slider" min="0" max="100" value="0">
                    </div>
                    <div class="control-row">
                        <span id="animation-time">0 / 0</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.149.0/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dat-gui/0.7.9/dat.gui.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.149.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.149.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.149.0/examples/js/loaders/DRACOLoader.js"></script>
    <script src="js/viewer.js"></script>
</body>
</html>
            """)
        print("Created default index.html")
    
    # Make sure directories exist before copying files
    js_dir = os.path.join(temp_dir, "js")
    css_dir = os.path.join(temp_dir, "css")
    
    os.makedirs(js_dir, exist_ok=True)
    os.makedirs(css_dir, exist_ok=True)
    
    # Copy JS file
    js_source = os.path.join(viewer_files_dir, "js", "viewer.js")
    js_dest = os.path.join(js_dir, "viewer.js")
    
    if os.path.exists(js_source) and os.path.getsize(js_source) > 0:
        shutil.copy2(js_source, js_dest)
        print(f"Copied viewer.js: {os.path.getsize(js_dest)} bytes")
    else:
        print(f"Error: viewer.js is missing or empty! Path: {js_source}")
    
    # Copy CSS file
    css_source = os.path.join(viewer_files_dir, "css", "style.css")
    css_dest = os.path.join(css_dir, "style.css")
    
    if os.path.exists(css_source) and os.path.getsize(css_source) > 0:
        shutil.copy2(css_source, css_dest)
        print(f"Copied style.css: {os.path.getsize(css_dest)} bytes")
    else:
        print(f"Error: style.css is missing or empty! Path: {css_source}")
            
    # Create a scene info JSON file with metadata
    scene_info = {
        "title": bpy.path.basename(bpy.data.filepath) or "Untitled Scene",
        "objects": len(bpy.data.objects),
        "has_animations": any(obj.animation_data for obj in bpy.data.objects)
    }
    
    with open(os.path.join(temp_dir, "scene_info.json"), 'w') as f:
        json.dump(scene_info, f)
        
    return temp_dir

def package_for_export(context, export_path):
    """Package all files into a standalone web export"""
    # Create a temporary directory for staging files
    try:
        temp_dir = tempfile.mkdtemp()
        
        # Generate all the preview files
        generate_preview_files(context, temp_dir)
        
        # Create a zip file with all contents
        shutil.make_archive(export_path, 'zip', temp_dir)
        
        # Clean up with error handling
        try:
            shutil.rmtree(temp_dir)
        except:
            print("Warning: Could not remove temporary directory after export")
            
        return export_path + ".zip"
    except Exception as e:
        print(f"Error during export: {e}")
        return None

# ------------------------------------
# Operators
# ------------------------------------

class WEB_PREVIEW_OT_preview_scene(bpy.types.Operator):
    """Preview the current scene in a web browser"""
    bl_idname = "web_preview.preview_scene"
    bl_label = "Preview in Browser"
    
    def execute(self, context):
        # Get the server instance
        global preview_server
        
        # Initialize server if needed
        if preview_server is None:
            preview_server = WebPreviewServer()
        
        # Start the server if it's not already running
        if not preview_server.is_running:
            preview_server.start_server()
            
        # Generate preview files
        try:
            generate_preview_files(context, preview_server.temp_dir)
        except Exception as e:
            self.report({'ERROR'}, f"Error generating preview: {str(e)}")
            return {'CANCELLED'}
        
        # Open the web browser
        webbrowser.open(preview_server.get_url())
        
        return {'FINISHED'}

class WEB_PREVIEW_OT_export_scene(bpy.types.Operator):
    """Export the current scene as a standalone web package"""
    bl_idname = "web_preview.export_scene"
    bl_label = "Export Scene to Web"
    
    filepath: bpy.props.StringProperty(
        name="Export Path",
        description="Path to export the web package",
        default="",
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        # Set default filename based on blend file
        blend_filepath = bpy.data.filepath
        if blend_filepath:
            filename = os.path.splitext(os.path.basename(blend_filepath))[0] + "_web"
            self.filepath = os.path.join(os.path.dirname(blend_filepath), filename)
        else:
            self.filepath = "untitled_web"
            
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # Package and export the scene
        try:
            export_path = package_for_export(context, self.filepath)
            if export_path:
                self.report({'INFO'}, f"Scene exported to {export_path}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Export failed")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export error: {str(e)}")
            return {'CANCELLED'}

class WEB_PREVIEW_OT_stop_server(bpy.types.Operator):
    """Stop the web preview server"""
    bl_idname = "web_preview.stop_server"
    bl_label = "Stop Server"
    
    def execute(self, context):
        global preview_server
        
        if preview_server and preview_server.is_running:
            preview_server.stop_server()
            self.report({'INFO'}, "Web preview server stopped")
        else:
            self.report({'INFO'}, "Server is not running")
            
        return {'FINISHED'}

# ------------------------------------
# UI
# ------------------------------------

class WEB_PREVIEW_PT_panel(bpy.types.Panel):
    """Panel for web preview controls"""
    bl_label = "BlendXweb By Egret"
    bl_idname = "WEB_PREVIEW_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlendXweb'
    
    def draw(self, context):
        layout = self.layout
        
        # Get server status
        global preview_server
        
        # Preview section
        box = layout.box()
        box.label(text="Preview")
        
        row = box.row()
        row.operator("web_preview.preview_scene", icon='WORLD')
        
        # Server status
        is_running = preview_server and preview_server.is_running
        box.label(text=f"Server: {'Running' if is_running else 'Offline'}")
        
        if is_running:
            box.operator("web_preview.stop_server", icon='X')
            box.label(text=f"Port: {preview_server.port}")
        
        # Export section
        box = layout.box()
        box.label(text="Export")
        box.operator("web_preview.export_scene", icon='EXPORT')

# ------------------------------------
# Addon Preferences
# ------------------------------------

class WebPreviewPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Blender Web Preview/BlendXweb Settings")
        # TODO: Add global addon settings here

# ------------------------------------
# Registration
# ------------------------------------

classes = (
    WebPreviewPreferences,
    WEB_PREVIEW_OT_preview_scene,
    WEB_PREVIEW_OT_export_scene,
    WEB_PREVIEW_OT_stop_server,
    WEB_PREVIEW_PT_panel
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # Stop the server if it's running
    global preview_server
    if preview_server and preview_server.is_running:
        preview_server.stop_server()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()