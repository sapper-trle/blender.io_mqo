﻿# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Script copyright (C) Thomas PORTASSAU (50thomatoes50)
# Contributors: Campbell Barton, Jiri Hnidek, Paolo Ciccone, Thomas Larsson, http://blender.stackexchange.com/users/185/adhi


# <pep8-80 compliant>

bl_info = {
    "name": "Metasequoia format (.mqo)",
    "author": "50thomatoes50",
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import-Export MQO, UV's, "
                   "materials and textures",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/MQO",
    "tracker_url": "https://github.com/50thomatoes50/blender.io_mqo/issues",
    "category": "Import-Export"}


#http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Multi-File_packages#init_.py
if "bpy" in locals():
    import importlib #imp module deprecated
    if "import_mqo" in locals():
        importlib.reload(import_mqo)
    if "export_mqo" in locals():
        importlib.reload(export_mqo)

import os
import bpy
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import (ExportHelper,
                                 ImportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )


class ExportMQO(bpy.types.Operator, ExportHelper):
    """Export to a Metasequoia file (.mqo)"""
    bl_idname = "io_export_scene.mqo"
    bl_description = 'Export to mqo file format (.mqo)'
    bl_label = "Export mqo"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
 
    # From ExportHelper. Filter filenames.
    filename_ext = ".mqo"
    filter_glob : StringProperty(default="*.mqo", options={'HIDDEN'})

    scale : bpy.props.FloatProperty(
        name = "Scale", 
        description="Scale mesh. Value > 1 means bigger, value < 1 means smaller", 
        default = 1, min = 0.001, max = 1000.0, step=1, precision=3, soft_min=.001, soft_max=1000.0)
 
    rot90 : bpy.props.BoolProperty(
        name = "Up axis correction",
        description="Blender up axis is Z but Metasequoia up axis is Y\nExporter will invert value to be in the correct direction",
        default = True)
    
    invert : bpy.props.BoolProperty(
        name = "Correction of inverted faces",
        description="Correction of inverted faces",
        default = True)

    no_ngons : bpy.props.BoolProperty(
        name = "Convert ngons to triangles",
        description = "ngons not supported in older versions of Metasequoia",
        default = False)
    
    edge : bpy.props.BoolProperty(
        name = "Export lost edge",
        description="Export edge which is not attached to a polygon",
        default = True)
 
    uv_exp : bpy.props.BoolProperty(
        name = "Export UV",
        description="Export UV",
        default = True)
    
    uv_cor : bpy.props.BoolProperty(
        name = "Convert UV",
        description="Invert UV map to be in the same direction as Metasequoia",
        default = True)
        
    mat_exp : bpy.props.BoolProperty(
        name = "Export Materials",
        description="...",
        default = True)
    
    mod_exp : bpy.props.BoolProperty(
        name = "Export Modifier",
        description="Export modifier like mirror or/and subdivision surface",
        default = True)
    
    def execute(self, context):
        msg = ".mqo export: Executing"
        self.report({'INFO'}, msg)
        print(msg)
        if self.scale < 1:
            s = "%.0f times smaller" % 1.0/self.scale
        elif self.scale > 1:
            s = "%.0f times bigger" % self.scale
        else:
            s = "same size"            
        msg = ".mqo export: Objects will be %s"%(s)
        print(msg)
        self.report({'INFO'}, msg)
        from . import export_mqo
        meshobjects = [ob for ob in context.scene.objects if ob.type == 'MESH']
        export_mqo.export_mqo(self,
            self.properties.filepath, 
            meshobjects, 
            self.rot90, self.invert, self.no_ngons, self.edge, self.uv_exp, self.uv_cor, self.mat_exp, self.mod_exp,
            self.scale)
        return {'FINISHED'}
 
    def invoke(self, context, event):
        meshobjects = [ob for ob in context.scene.objects if ob.type == 'MESH']
        if not meshobjects:
            msg = ".mqo export: Cancelled - No MESH objects to export."
            self.report({'ERROR'}, msg)
            print(msg,"\n")
            return{'CANCELLED'}
        pth, fn = os.path.split(bpy.data.filepath)
        nm, xtn = os.path.splitext(fn)
        if nm =="":
            nm = meshobjects[0].name
        self.properties.filepath = nm
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportMQO(bpy.types.Operator, ImportHelper):
    """Import a Metasequoia file (.mqo)"""
    bl_idname = "io_import_scene.mqo"
    bl_description = 'Import from mqo file format (.mqo)'
    bl_label = "Import mqo"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO'}
 
    # From ImportHelper. Filter filenames.
    filter_glob : StringProperty(default="*.mqo;*.mqoz", options={'HIDDEN'})

    scale : bpy.props.FloatProperty(
        name = "Scale", 
        description="Scale mesh. Value > 1 means bigger, value < 1 means smaller", 
        default = 1, min = 0.001, max = 1000.0, step=1, precision=3, soft_min=0.001, soft_max=1000.0)
 
    rot90 : bpy.props.BoolProperty(
        name = "Up axis correction",
        description="Blender up axis is Z but Metasequoia up axis is Y\nExporter will invert value to be in the correct direction",
        default = True)

    debug : bpy.props.BoolProperty(
        name = "Show debug text",
        description="Print debug text to console",
        default = False)
 
    def execute(self, context):
        import pathlib # Python 3.4
        pth  = pathlib.Path(self.properties.filepath)

        if pth.suffix is "":
            pth  = pathlib.Path(self.properties.filepath + ".mqo")
            file_exists = pth.exists()
            if not file_exists:
                pth = pathlib.Path(self.properties.filepath + ".mqoz")
                file_exists = pth.exists()
                if not file_exists:
                    pth = pathlib.Path(self.properties.filepath)
        else:
            file_exists = pth.exists() 

        if not file_exists:
            msg = "File not found: %s" % pth 
            print(msg)
            self.report({'ERROR'}, msg)
            return{'CANCELLED'}  
        
        if pth.suffix.lower() not in [".mqo", ".mqoz"]:
            msg = "Not a Metasequoia file: %s" % pth
            print(msg)
            self.report({'ERROR'}, msg)
            return{'CANCELLED'}

        msg = ".mqo import: Opening %s"% pth
        print(msg)
        self.report({'INFO'}, msg)
        if self.scale < 1:
            s = "%.0f times smaller" % (1.0/self.scale)
        elif self.scale > 1:
            s = "%.0f times bigger" % self.scale
        else:
            s = "same size"            
        msg = ".mqo import: Objects will be %s"%(s)
        print(msg)
        self.report({'INFO'}, msg)        
        from . import import_mqo
        import_mqo.open_mqo(self,
            pth, 
            self.rot90,
            self.scale,
            self.debug)
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportMQO.bl_idname, text="50Thom Metasequoia (.mqo)")


def menu_func_export(self, context):
    self.layout.operator(ExportMQO.bl_idname, text="50Thom Metasequoia (.mqo)")


def register():
    bpy.utils.register_class(ImportMQO)
    bpy.utils.register_class(ExportMQO)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportMQO)
    bpy.utils.unregister_class(ExportMQO)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
