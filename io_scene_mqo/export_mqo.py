# ##### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>
"""
This script exports Metasequoia (*.mqo) files from Blender.

Usage:
Run this script from "File->Export" menu.

NO WIKI FOR THE MOMENT
http://wiki.blender.org/index.php/Scripts/Manual/Export/MQO


base source from : 
http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Multi-File_packages#Simple_obj_export
"""

import os
import time
import pprint
import bpy
import mathutils
import math
import bpy_extras.io_utils


def export_mqo(op, filepath, objects, rot90, invert, no_ngons, edge, uv_exp, uv_cor, mat_exp, mod_exp, scale):
    
    # Exit edit mode before exporting, so current object states are exported properly.
    #if bpy.ops.object.mode_set.poll():
    #    bpy.ops.object.mode_set(mode='OBJECT')

    if objects == None:
        msg = ".mqo export: No MESH objects to export."
        print(msg)
        op.report({'ERROR'}, msg)
        return
    with open(filepath, 'w') as fp:
        fw = fp.write
        msg = ".mqo export: Writing %s" % filepath
        print(msg)
        op.report({'INFO'}, msg)
      
        inte_mat = 0
        tmp_mat = []
        obj_tmp = []
        total_ngons = 0
    
        for ob in objects:
            inte_mat, obj_tmp, ngons = exp_obj(op, obj_tmp, ob, rot90, invert, no_ngons, edge, uv_exp, uv_cor, scale, mat_exp, inte_mat, tmp_mat, mod_exp)
        
        total_ngons += ngons
        if no_ngons:
            version = 1.0
        else:
            if total_ngons > 0:
                version = 1.1
            else:
                version = 1.0        
        fw("Metasequoia Document\nFormat Text Ver %.1f\n\nScene {\n    pos 0.0000 0.0000 1500.0000\n    lookat 0.0000 0.0000 0.0000\n    head -0.5236\n    pich 0.5236\n    bank 0.0000\n    ortho 0\n    zoom2 5.0000\n    amb 0.250 0.250 0.250\n    dirlights 1 {\n        light {\n            dir 0.408 0.408 0.816\n            color 1.000 1.000 1.000\n        }\n    }\n}\n" % (version))

        if mat_exp:        
            mat_fw(fw, tmp_mat)
        else: # create default material
            fw("Material 1 {\n\t\"mat1\" shader(3) col(1.000 1.000 1.000 1.000) dif(0.800) amb(0.600) emi(0.000) spc(0.000) power(5.00)\n}\n")
   
        for data in obj_tmp:
            fw(data)
    
        fw("Eof\n")
        msg = ".mqo export: Export finished. Created %s" % filepath
        print(msg,"\n")
        op.report({'INFO'}, msg)
    return
    
def exp_obj(op, fw, ob, rot90, invert, no_ngons, edge, uv_exp, uv_cor, scale, mat_exp, inte_mat, tmp_mat, mod_exp):
    me = ob.data
    facecount, ngons = getFacesCount(me)
    if facecount == 0 and not edge:
        return inte_mat, fw, ngons
    if mod_exp:
        mod = modif(op, ob.modifiers)
    #fw("Object \"%s\" {\n\tdepth 0\n\tfolding 0\n\tscale %.6f %.6f %.6f\n\trotation %.6f %.6f %.6f\n\ttranslation %.6f %.6f %.6f\n\tvisible 15\n\tlocking 0\n\tshading 1\n\tfacet 59.5\n\tcolor 0.898 0.498 0.698\n\tcolor_type 0\n" % (me.name, scale[0], scale[1], scale[2], 180*rotat.x/pi, 180*rotat.y/pi, 180*rotat.z/pi, loca[0], loca[1], loca[2]))
    fw.append("Object \"%s\" {\n\tdepth 0\n\tfolding 0\n\tscale 1.0 1.0 1.0\n\trotation 1.0 1.0 1.0\n\ttranslation 1.0 1.0 1.0\n\tvisible 15\n\tlocking 0\n\tshading 1\n\tfacet 59.5\n\tcolor 0.898 0.498 0.698\n\tcolor_type 0\n" % (ob.name))
    for mod_fw in mod:
        fw.append(mod_fw)
    
    msg = ".mqo export: Exporting obj=\"%s\" inte_mat=%i" %(ob.name, inte_mat)
    print(msg)
    op.report({'INFO'}, msg)
    inte_mat_obj = inte_mat
    if mat_exp:
        for mat in me.materials:
            inte_mat = mat_extract(op, mat, tmp_mat, inte_mat)
                
    fw.append("\tvertex %i {\n"% (len(me.vertices)))
    e = mathutils.Euler()
    e.rotate_axis('X', math.radians(-90))
    m = e.to_matrix()
    for v in me.vertices:
        if rot90:
            # rotate -90 degrees about X axis
            vv = m @ v.co #new syntax, was m*v.co
            fw.append("\t\t%.5f %.5f %.5f\n" % (vv[0]*scale, vv[1]*scale, vv[2]*scale))
        else:
            fw.append("\t\t%.5f %.5f %.5f\n" % (v.co[0]*scale, v.co[1]*scale, v.co[2]*scale))
    fw.append("\t}\n")
    
    #me.update(False, True)
    me.update(calc_edges_loose=True)
    #faces = me.tessfaces #Mesh.tessfaces not exist in 2.80 api
    lostEdges = 0
    for e in me.edges:
        if e.is_loose:
            lostEdges+=1
    if edge and lostEdges > 0:
        fw.append("\tface %i {\n" % (facecount+lostEdges))
        for e in me.edges:
            if e.is_loose:
                fw.append("\t\t2 V(%i %i)\n" % (e.vertices[0], e.vertices[1]))
    else:
        fw.append("\tface %i {\n" % (facecount))
    
    #me.update(False, True)
    me.update(calc_edges_loose=True)
    me.calc_loop_triangles()
    if (no_ngons==False) or (ngons==0):
        faces = me.polygons
    else:
        faces = []
        for f in me.polygons:
            if len(f.vertices) < 5:
                faces.append(f)
            else:
                tris = [tri for tri in me.loop_triangles if tri.polygon_index == f.index]
                faces.extend(tris)

    for f in faces:
        vs = f.vertices
        if len(f.vertices) == 3:
            if invert:
                fw.append("\t\t3 V(%d %d %d)" % (vs[0], vs[2], vs[1]))
            else:
                fw.append("\t\t3 V(%d %d %d)" % (vs[0], vs[1], vs[2]))
        if len(f.vertices) == 4:
            if invert:
                fw.append("\t\t4 V(%d %d %d %d)" % (vs[0], vs[3], vs[2], vs[1]))
            else:
                fw.append("\t\t4 V(%d %d %d %d)" % (vs[0], vs[1], vs[2], vs[3]))
        if len(f.vertices) > 4:
            count = len(f.vertices)  
            if invert:
                vs=[idx for idx in vs]
                vs.reverse()
                vs.insert(0,vs.pop())
            fw.append("\t\t%d V(" % (count))
            for i in range(count):
                fw.append("%d" % vs[i])
                if i < count:
                    fw.append(" ")
            fw.append(")")
        fw.append(" M(%d)" % (f.material_index+inte_mat_obj))
        
        try:
            #data = me.tessface_uv_textures.active.data[f.index]
            uv_layer = me.uv_layers.active.data
            uvs =[]
            if hasattr(f,"loop_indices"): #polygons
                for loop_index in f.loop_indices:
                    uvs.append(uv_layer[loop_index].uv)
            else:
                for loop_index in f.loops: #loop_triangles
                    uvs.append(uv_layer[loop_index].uv)
            if (uv_exp) and (uvs):
                if not invert:
                    if len(f.vertices) == 3:
                        if uv_cor:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], 1-uvs[0][1], uvs[1][0], 1-uvs[1][1], uvs[2][0], 1-uvs[2][1]))
                        else:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], uvs[0][1], uvs[1][0], uvs[1][1], uvs[2][0], uvs[2][1]))
                    if len(f.vertices) == 4:
                        if uv_cor:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], 1-uvs[0][1], uvs[1][0], 1-uvs[1][1], uvs[2][0], 1-uvs[2][1], uvs[3][0], 1-uvs[3][1]))
                        else:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], uvs[0][1], uvs[1][0], uvs[1][1], uvs[2][0], uvs[2][1], uvs[3][0], uvs[3][1]))
                    if len(f.vertices) > 4:
                        fw.append(" UV(")
                        for uv in uvs:
                            if uv != uvs[-1]:
                                s=" "
                            else:
                                s=""
                            if uv_cor:
                                fw.append("%.5f %.5f%s"%(uv[0],1-uv[1],s))
                            else:
                                fw.append("%.5f %.5f%s"%(uv[0],uv[1],s))
                        fw.append(")")
                else:
                    if len(f.vertices) == 3:
                        if uv_cor:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], 1-uvs[0][1], uvs[2][0], 1-uvs[2][1], uvs[1][0], 1-uvs[1][1]))
                        else:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], uvs[0][1], uvs[2][0], uvs[2][1], uvs[1][0], uvs[1][1]))
                    if len(f.vertices) == 4:
                        if uv_cor:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], 1-uvs[0][1], uvs[3][0], 1-uvs[3][1], uvs[2][0], 1-uvs[2][1], uvs[1][0], 1-uvs[1][1]))
                        else:
                            fw.append(" UV(%.5f %.5f %.5f %.5f %.5f %.5f %.5f %.5f)" % (uvs[0][0], uvs[0][1], uvs[3][0], uvs[3][1], uvs[2][0], uvs[2][1], uvs[1][0], uvs[1][1]))
                    if len(f.vertices) > 4:
                        uvs.reverse()
                        uvs.insert(0,uvs.pop())
                        fw.append(" UV(")
                        for uv in uvs:
                            if uv != uvs[-1]:
                                s=" "
                            else:
                                s=""
                            if uv_cor:
                                fw.append("%.5f %.5f%s"%(uv[0],1-uv[1],s))
                            else:
                                fw.append("%.5f %.5f%s"%(uv[0],uv[1],s))
                        fw.append(")")                   
        except AttributeError:
            #pass
            msg="No UVs exported due AttributeError exception"
            print(msg)
            op.report({'INFO'}, msg)
        
        fw.append("\n")
    fw.append("\t}\n")

    fw.append("}\n")
    return inte_mat, fw, ngons
    
    
def mat_extract(op, mat, tmp, index):
    #FIXME: bit of a hack, I don't know enough about materials in Blender
    #FIXME: should probably use bpy_extras.node_shader_utils but module not documented in current api docs!!!!
    # assumes at most one diffuse texture node ("Color" socket) connected to shader node or output node
    # assumes at most one bump texture node ("Color" socket) connected to output node "Displacement" socket
    # assumes at most one alpha texture node ("alpha" socket) connected to shader node "alpha" socket 
    
    alpha = ''
    diffuse = ''
    bump = ''
    msg = ".mqo export: added mat %s / index #%i" % (mat.name,index)
    print(msg)
    op.report({'INFO'}, msg)

#   l = "\t\"%s\" col(%.3f %.3f %.3f %.3f) dif(%.3f) amb(%.3f) emi(%.3f) spc(%.3f) power(5)" % (mat.name, mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], mat.alpha, mat.diffuse_intensity, mat.ambient, mat.emit, mat.specular_intensity)
    l = "\t\"%s\" col(%.3f %.3f %.3f %.3f) dif(0.800) amb(0.600) emi(0.000) spc(%.3f) power(5)" % (mat.name, mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], mat.diffuse_color[3], mat.specular_intensity)
    if not mat.use_nodes:
        tmp.append(l+"\n")
        return index + 1
    
    nodes = mat.node_tree.nodes
    output_nodes = [n for n in nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n.inputs["Surface"].is_linked]
    if not output_nodes:
        tmp.append(l+"\n")
        return index + 1

    tex_nodes = [n for n in nodes if n.bl_idname == "ShaderNodeTexImage" and n.outputs["Color"].is_linked]
    for tn in tex_nodes:
        if tn.outputs["Color"].links[0].to_node.bl_idname != "ShaderNodeOutputMaterial":
            diffuse = bpy.path.basename(tn.image.filepath)
            break

    alpha_nodes = [n for n in nodes if n.bl_idname == "ShaderNodeTexImage" and n.outputs["Alpha"].is_linked]
    if len(alpha_nodes)==1:
        alpha = bpy.path.basename(alpha_nodes[0].image.filepath)

    #assume one only output node
    if output_nodes[0].inputs["Displacement"].is_linked:
        if output_nodes[0].inputs["Displacement"].links[0].from_node.bl_idname == "ShaderNodeTexImage":
            bump = bpy.path.basename(output_nodes[0].inputs["Displacement"].links[0].from_node.image.filepath)

    if diffuse: 
        l = l + " tex(\"" + diffuse + "\")"
    if alpha:
        l = l + " aplane(\"" + alpha + "\")"
    if bump:
        l = l + " bump(\"" + bump + "\")"    
    tmp.append(l+"\n")
    return index + 1
    
    
def mat_fw(fw, tmp):
    fw("Material  %d {\n" % (len(tmp)))
    for mat in tmp:
        fw("%s" % (mat))
    fw("}\n")
    
def modif(op, modifiers):
    tmp = []
    axis = 0
    for mod in modifiers.values():
        if mod.type == "MIRROR":
            msg = ".mqo export: exporting mirror"
            print(msg)
            op.report({'INFO'}, msg)
            if mod.use_mirror_merge:
                tmp.append("\tmirror 2\n\tmirror_dis %.3f\n" % mod.merge_threshold)
            else:
                tmp.append("\tmirror 1\n")
            if mod.use_x:
                axis = 1
            if mod.use_y:
                axis = axis + 2
            if mod.use_z:
                axis = axis + 4
        if mod.type == "SUBSURF":
            msg = ".mqo export: exporting subsurf" 
            print(msg)
            op.report({'INFO'}, msg)
            tmp.append("\tpatch 3\n\tpatchtri 0\n\tsegment %i\n" % mod.render_levels)
    return tmp

def getFacesCount(msh):
    quads=0
    tris=0
    ngons=0
    for f in msh.polygons:
        vcount = len(f.vertices)
        if vcount==3:
            tris += 1
        elif vcount==4:
            quads += 1
        else:
            ngons += 1
    if ngons==0:
        return len(msh.polygons), ngons
    msh.calc_loop_triangles()
    ngon_tris = len(msh.loop_triangles) - (2*quads) - tris
    return quads + tris + ngon_tris, ngons
