# Blender Web Preview Addon
## Installation and Usage Guide

This addon allows you to preview your Blender scenes in a web browser and export them as standalone web packages.

## Prerequisites

- Blender 4.0 or newer
- Web browser with WebGL support (Chrome, Firefox, Edge, Safari)
- Python 3.7+ (typically included with Blender)

## Installation

### Method 1: Via Blender's Addon Installer

1. Download the addon as a ZIP file (do not extract it)
2. Open Blender and go to Edit > Preferences
3. Select the "Add-ons" tab
4. Click "Install..." button at the top right
5. Navigate to and select the downloaded ZIP file
6. Click "Install Add-on"
7. Enable the addon by checking the box next to "3D View: Blender Web Preview"

### Method 2: Manual Installation

1. Download and extract the addon files
2. Locate your Blender addons directory:
   - Windows: `%APPDATA%\Blender Foundation\Blender\4.0\scripts\addons`
   - macOS: `~/Library/Application Support/Blender/4.0/scripts/addons`
   - Linux: `~/.config/blender/4.0/scripts/addons`
3. Copy the entire `blender_web_preview` folder to the addons directory
4. Start Blender and go to Edit > Preferences > Add-ons
5. Search for "Web Preview" and enable the addon

## File Structure Setup

After installation, you need to run the file structure setup script once to create the necessary directories:

1. Open a terminal/command prompt
2. Navigate to the addon directory
3. Run `python setup_files.py`

## Using the Addon

### Accessing the Addon

Once installed, you can access the addon from the 3D View sidebar:

1. Open the sidebar by pressing `N` in the 3D View
2. Select the "Web Preview" tab

### Previewing in Browser

1. Set up your scene in Blender
2. Click the "Preview in Browser" button in the addon panel
3. A local server will start and your default web browser will open showing your scene
4. Use the controls in the browser to navigate and interact with the scene

### Exporting for Web

1. Set up your scene in Blender
2. Click the "Export Scene to Web" button in the addon panel
3. Choose a destination folder and filename
4. Click "Export"
5. A ZIP file will be created containing all necessary files for web viewing

## Web Viewer Controls

The web viewer provides several controls to interact with your scene:

### Camera Controls
- Left Mouse: Rotate the view
- Middle Mouse / Scroll: Zoom in/out
- Right Mouse: Pan the view
- Top/Front/Side buttons: Jump to standard views
- Reset Camera: Return to the initial view

### Display Options
- Wireframe: Toggle wireframe mode
- Grid: Toggle the reference grid
- Lights: Toggle scene lights (excluding ambient light)

### Animation Controls
- Play: Start the animation
- Pause: Pause the animation
- Stop: Stop and reset the animation
- Slider: Scrub through the animation timeline

## Troubleshooting

### Server Issues
- If the preview doesn't open, check if port 8000 is available or in use
- Try stopping and restarting the server from the addon panel

### Export Issues
- Make sure your Blender scene has been saved
- Check if you have write permissions for the export directory
- Ensure all textures are properly packed or referenced

### Web Viewer Issues
- Make sure your browser supports WebGL
- Check the browser console for any error messages
- Try using a different browser if issues persist

## License

This addon is licensed under the MIT License. See LICENSE file for details.

## Support

For issues, feature requests, or contributions, please visit the project repository.
