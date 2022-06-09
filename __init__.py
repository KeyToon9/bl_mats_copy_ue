# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from posixpath import split
import sys
import bpy, os
from bpy.props import BoolProperty
from . import generate_ue_mat_nodes
from . import install

bl_info = {
    "name" : "Material Nodes Copy to UE",
    "author" : "KeyToon9",
    "description" : "",
    "blender" : (3, 00, 0),
    "version" : (0, 0, 1),
    "location" : "https://github.com/KeyToon9/bl_mats_copy_ue",
    "warning" : "",
    "category" : "Generic"
}

class CP2U_OT_CopyMatNodesOperator(bpy.types.Operator):
    bl_idname: str = "cp2u.copy_mat_nodes"
    bl_label: str = "Copy Nodes"

    def get_selected_nodes(self, context):
        nodes = []
        for node in context.active_object.active_material.node_tree.nodes:
            if node.select:
                nodes.append(node)
        return nodes

    def execute(self, context):
        mats_str = ''
        try:
            import pyperclip

            mats_str = generate_ue_mat_nodes.get_ue_mat_str(self.get_selected_nodes(context), context.window.height, self)
            pyperclip.copy(mats_str)
            self.report({'INFO'}, "Copy to clipboard.")
        except ModuleNotFoundError:
            print("Failed to import pyperclip module.")
            self.report({'ERROR'}, "Failed to import pyperclip module.")
            
            # try refresh system path
            import site
            install.update_sys_path(site.getusersitepackages(), [])

        
        return {"FINISHED"}

    def invoke(self, context, event):
        # print(event.type)

        return self.execute(context)
        
class CP2U_PT_MatEditorPanel(bpy.types.Panel):
    bl_idname: str = "cp2u.mat_editor_panel"
    bl_label: str = "CP2U"
    bl_category: str = 'CP'
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Copy To UE")
        row = layout.row()

        row.operator("cp2u.copy_mat_nodes", text="Copy", icon="COPYDOWN")

def get_name():
    return os.path.basename(os.path.dirname(os.path.realpath(__file__)))

def get_prefs():
    return bpy.context.preferences.addons[get_name()].preferences

class CP2U_OT_InstallPyperclip(bpy.types.Operator):
    bl_idname: str = "cp2u.install_pyperclip"
    bl_label: str = "Install Pyperclip"
    bl_description = "Install pip and pyperclip for Blender Python."

    def execute(self, context):
        print("\nCP2U: Installing PIP.")

        log = []

        pythonbinpath, ensurepippath, usersitepackagespath = install.get_python_path()
        installed = install.install_pip(pythonbinpath, ensurepippath, log, mode='USER')

        if installed:

            installed = install.update_pip(pythonbinpath, log, mode='USER')

            installed = install.install_pyperclip(pythonbinpath, log, mode='USER')

            get_prefs().is_installed_pyperclip, get_prefs().is_require_restart = install.test_import_pyperclip(installed, log, usersitepackagespath)

        return {"FINISHED"}

class CP2U_PT_AddonPreferencesPanel(bpy.types.AddonPreferences):
    bl_idname = __name__

    is_installed_pyperclip: BoolProperty(name="is_installed_pyperclip", default=False)
    is_require_restart: BoolProperty(name="is_require_restart", default=False)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Install PIP and pyperclip for Blender Python:")
        row = layout.row()

        row.operator("cp2u.install_pyperclip", text="Install Pyperclip", icon="IMPORT")

        # row = layout.row()
        # split = row.split(factor=0.3)
        # split.label(text="Copy Shortcut:")
        # split.box()
        # todo: custom shortcut for copy noeds

        

def register():
    bpy.utils.refresh_script_paths()
    bpy.utils.register_class(CP2U_OT_CopyMatNodesOperator)
    bpy.utils.register_class(CP2U_PT_MatEditorPanel)
    bpy.utils.register_class(CP2U_OT_InstallPyperclip)
    bpy.utils.register_class(CP2U_PT_AddonPreferencesPanel)

def unregister():
    bpy.utils.unregister_class(CP2U_OT_CopyMatNodesOperator)
    bpy.utils.unregister_class(CP2U_PT_MatEditorPanel)
    bpy.utils.unregister_class(CP2U_PT_AddonPreferencesPanel)
    bpy.utils.unregister_class(CP2U_OT_InstallPyperclip)

if __name__ == '__main__':
    register()