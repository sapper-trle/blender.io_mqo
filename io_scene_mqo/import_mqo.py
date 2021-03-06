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

# <pep8 compliant>

# Script copyright (C) Thomas PORTASSAU (50thomatoes50)
# Contributors: Campbell Barton, Jiri Hnidek, Paolo Ciccone, Thomas Larsson, http://blender.stackexchange.com/users/185/adhi
#http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Multi-File_packages#Simple_obj_importer_and_exporter

"""
This script imports a Metasequoia(*.mqo) files to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired MQO file.

NO WIKI FOR THE MOMENT
http://wiki.blender.org/index.php/Scripts/Manual/Import/MQO


base source from : 
http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Multi-File_packages#Simple_obj_import
"""

import bpy, os, math, mathutils, struct

def dprint(string, debug=False):
    if debug:
        print("\t",string)
    return

def open_mqo(op, filepath, rot90, scale, debug):
    if filepath.suffix.lower() in [".mqo"]:
        name = os.path.basename(filepath)
        realpath = os.path.realpath(os.path.expanduser(filepath))
        with open(realpath, 'rb') as fp:
            dprint('Importing %s' % realpath, debug) 
            import_mqo(op, fp, rot90, scale, debug)
    else:
        mqo_file = None
        import zipfile
        # from io import TextIOWrapper as tw
        with zipfile.ZipFile(filepath) as zfile:
            for zinfo in zfile.infolist():
                f, ext = os.path.splitext(zinfo.filename)
                if ext.lower() in [".mqo"]:
                    mqo_file = zinfo
                    break
            if mqo_file:
                with zfile.open(mqo_file) as fp:
                    dprint('Importing %s' % filepath, debug)
                    import_mqo(op, fp, rot90, scale, debug)
                    # import_mqo(op, tw(fp), rot90, scale, debug)
            else:
                msg = ".mqo Import: No mqo file in mqoz file"
                dprint(msg, debug)
                op.report({'ERROR', msg})
    
def import_mqo(op, fp, rot90, scale, debug):
    e = mathutils.Euler()
    e.rotate_axis('X', math.radians(90))
    m = e.to_matrix()
    verts = []
    faces = []
    edges = []
    texverts = []
    texfaces = []
    obj = False
    mat = False
    mat_nb = 0
    v = False
    v_nb = 0
    vb = False
    obj_name = ""
    obj_count = 0
    f = False
    f_nb = 0
    shift_jis = False

    for bytesline in fp:
        try:
            line = bytesline.decode()
        except UnicodeDecodeError:
            try:
                # dprint(bytesline, debug)
                msg = ".mqo import: Unknown character encoding found. Trying shift_jis. Import may be unsuccessful"
                print(msg)
                op.report({'WARNING'}, msg)
                shift_jis = True
                line = bytesline.decode(encoding='shift_jis')
            except UnicodeDecodeError:
                msg = ".mqo import: Character encoding not 'shift_jis'. Trying ignoring errors. Import may be unsuccessful"
                print(msg)
                op.report({'WARNING'}, msg)
                shift_jis = False
                line = bytesline.decode(errors = 'replace')
        words = line.split()
        if len(words) == 0:                     ##Nothing
            pass    
        elif words[0] == "}":                       ##end of mat or obj
            dprint('end something', debug)
            if obj:                             ##if end of obj import it in blender
                if v:
                    v=False
                    dprint('end of vertex', debug)
                elif vb:
                    vb=False
                    dprint('end of Bvertex', debug)
                elif f:
                    f=False
                    dprint('end of face', debug)
                else:
                    dprint('end of obj. importing :"%s"' % obj_name, debug)
                    if verts and faces:
                        nm = obj_name
                        if shift_jis:
                            nm = "obj" # need to rename object and mesh since shift_jis chars not supported in my Blender!
                        me = bpy.data.meshes.new(nm)
                        me.from_pydata(verts, [], faces)
                        me.update()
                        # scn = bpy.context.scene
                        ob = bpy.data.objects.new(nm, me)
                        view_layer = bpy.context.view_layer
                        collection = view_layer.active_layer_collection.collection
                        collection.objects.link(ob)
                        obj_count += 1
                        view_layer.update()
                        # scn.collection.objects.link(ob)
                        #TODO replace following line with 2.80 api
                        #scn.objects.active = ob
                    else:
                        if not verts and not faces:
                            s = "vertices or faces"
                        elif not verts:
                            s = "vertices"
                        else:
                            s = "faces"
                        msg = ".mqo import: Object \"%s\" ignored. No %s found" % (obj_name, s)
                        print(msg)
                        op.report({'WARNING'}, msg)

                    obj = False
                    v = False
                    v_nb = 0
                    obj_name = ""
                    f = False
                    f_nb = 0
                    verts = []
                    faces = []
                    texverts = []
                    texfaces = []
            if mat:                             ##if end of mat import later in obj
                dprint('end of mat', debug)
                mat = False
                
        elif words[0] == 'Object':              ##detect an object
            dprint('begin of obj :%s' % words[1], debug)
            obj = True
            obj_name = words[1].strip('"')
        elif words[0] == 'Material':            ##detect materials
            dprint('begin of mat', debug)
            mat = True
            mat_nb = int(words[1].strip('"'))
        elif obj and words[0] == "vertex":      ##detect vertex when obj
            dprint('begin of ver', debug)
            v = True
            v_nb = int(words[1])
        elif obj and words[0] == "BVertex":
            vb = True
            v_nb = int(words[1])
            v_bytes = int(fp.readline().decode().split()[-1].strip("[]"))
            #dprint('nl=%s' % fp.readline(), debug)
            for i in range(v_nb):
                tmp = struct.unpack("<fff", fp.read(4*3))
                dprint('tmp = %s' % str(tmp), debug)
                if rot90:
                    V = mathutils.Vector(tmp)
                    vv = m @ V
                    verts.append( (scale*vv.x, scale*vv.y, scale*vv.z) )
                else:
                    verts.append( (scale*tmp[0], scale*tmp[1], scale*tmp[2]) )
                v_nb -= 1 
                if v_nb == 0:
                    #v = False
                    dprint('end of vertex?', debug)
        elif obj and (words[0] =="weit" or words[0] =="color") and (v or vb):
            bracecount=1
            while bracecount > 0:
                tmp = fp.readline()
                if tmp.find(b"{") != -1:
                    bracecount += 1
                if tmp.find(b"}") != -1:
                    bracecount -= 1
        elif obj and words[0] == "vertexattr":
            bracecount=1
            for aline in fp:
                if aline.find(b"{") !=-1:
                    bracecount +=1
                if aline.find(b"}") !=-1:
                    bracecount -=1
                if bracecount == 0:
                    break
        elif obj and v and v_nb != 0:           ##get vertex coor when vertex and obj
            dprint('found a vertex', debug)
            (x,y,z) = (float(words[0]), float(words[1]), float(words[2]))
            if rot90:
                V = mathutils.Vector((x,y,z))
                vv = m @ V #m*V new syntax
                verts.append( (scale*vv.x, scale*vv.y, scale*vv.z) )
            else:
                verts.append( (scale*x, scale*y, scale*z) )
            v_nb = v_nb -1
            if v_nb == 0:                       
                #v = False
                dprint('end of vertex?', debug)
        elif obj and words[0] == "face":        ##detect face when obj
            dprint('begin of face', debug)
            f = True
            f_nb = int(words[1])
        elif obj and f and f_nb != 0:           ##get face vertex
            dprint('found a face', debug)
            if int(words[0]) == 2:
                edges.append((int(words[1].strip('V(')), int(words[2].strip(')'))))
            elif int(words[0]) == 3:
                faces.append((int(words[1].strip('V(')), int(words[2]), int(words[3].strip(')'))))
            elif int(words[0]) == 4:
                faces.append((int(words[1].strip('V(')), int(words[2]), int(words[3]), int(words[4].strip(')'))))
            else:
                dprint('face with %s vertex' % words[0], debug)
                num = int(words[0])
                v_indices = []
                for idx in range(1, num+1):
                    if idx == 1:
                        v_indices.append(int(words[idx].strip('V(')))
                    elif idx == num:
                        v_indices.append(int(words[idx].strip(')')))
                    else:
                        v_indices.append(int(words[idx]))
                faces.append(tuple(v_indices))
            f_nb = f_nb -1
            if f_nb ==0:
                #f= False
                dprint('end of face?', debug)
        else:
            dprint('don\'t know what is it', debug)          
    
    msg = ".mqo import: Import finished"
    print(msg, "\n")
    op.report({'INFO'}, msg)
    if obj_count == 0:
        msg = ".mqo import: Unsuccessful. No objects imported"
        print(msg, "\n")
        op.report({'ERROR'}, msg)

    return
 