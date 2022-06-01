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

import bpy
from . import generate_ue_mat_nodes

bl_info = {
    "name" : "Material Nodes Copy to UE",
    "author" : "KeyToon9",
    "description" : "",
    "blender" : (3, 00, 0),
    "version" : (0, 0, 1),
    "location" : "",
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
        
        generate_ue_mat_nodes.get_ue_mat_str(self.get_selected_nodes(context), context.window.height)
        
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

def register():
    bpy.utils.register_class(CP2U_OT_CopyMatNodesOperator)
    bpy.utils.register_class(CP2U_PT_MatEditorPanel)

def unregister():
    bpy.utils.unregister_class(CP2U_OT_CopyMatNodesOperator)
    bpy.utils.unregister_class(CP2U_PT_MatEditorPanel)
