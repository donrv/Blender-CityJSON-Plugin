bl_info = {
    "name": "Import CityJSON files",
    "author": "Konstantinos Mastorakis",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > CityJSON (.json)",
    "description": "Visualize 3D City Models encoded in CityJSON format",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy
import json
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


def assign_properties(obj, props, prefix=[]):
    """Assigns the custom properties to obj based on the props"""
    for prop, value in props.items():
        if prop in ["geometry", "children", "parents"]:
            continue

        if isinstance(value, dict):
            obj = assign_properties(obj, value, prefix + [prop])
        else:
            obj[".".join(prefix + [prop])] = value

    return obj


def cityjson_parser(context, filepath, cityjson_import_settings):
    
    print("Importing CityJSON file...")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=True)
    
    
    #Open CityJSON file
    with open(filepath) as json_file:
        data = json.load(json_file)
        vertices=list() 
           
        #Checking if coordinates need to be transformed and transforming if necessary 
        if 'transform' not in data:
            for vertex in data['vertices']:
                vertices.append(tuple(vertex))
        else:
            trans_param = data['transform']
            #Transforming coords to actual real world coords
            for vertex in data['vertices']:
                x=vertex[0]*trans_param['scale'][0]+trans_param['translate'][0]
                y=vertex[1]*trans_param['scale'][1]+trans_param['translate'][1]
                z=vertex[2]*trans_param['scale'][2]+trans_param['translate'][2]
                vertices.append((x,y,z))
                        
        #Parsing the boundary data of every object
        for theid in data['CityObjects']:
            for geom in data['CityObjects'][theid]['geometry']:
                
                bound=list()                
                #Checking how nested the geometry is i.e what kind of 3D geometry it contains
                if((geom['type']=='MultiSurface') or (geom['type'] == 'CompositeSurface')):
                    
                    for face in geom['boundaries']:
                        for verts in face:
                            bound.append(tuple(verts))
                            
                elif (geom['type']=='Solid'):
                    
                    for shell in geom['boundaries']:
                        for face in shell:
                            for verts in face:
                                bound.append(tuple(verts)) 
                                                                   
                elif (geom['type']=='MultiSolid'):
                    
                    for solid in geom['boundaries']:
                        for shell in solid:
                            for face in shell:
                                for verts in face:
                                    bound.append(tuple(verts))
                                    
            #Visualization part
            mesh_data = bpy.data.meshes.new("mesh")
            mesh_data.from_pydata(vertices, [], bound)
            mesh_data.update()
            obj = bpy.data.objects.new(theid, mesh_data)
            scene = bpy.context.scene
            scene.collection.objects.link(obj)
            
            #If you want the objects selected upon loading uncomment the next line
            #bpy.data.objects[child].select_set(True)
            
            #Assigning attributes to chilren objects
            obj = assign_properties(obj, data["CityObjects"][theid])
        
        #Creating parent-child relationship 
        objects = bpy.data.objects  
        for theid in data['CityObjects']:
            
            if 'children' in data['CityObjects'][theid]:
                # Storing parent's ID
                parent_obj = objects[theid]
                
                for child in data['CityObjects'][theid]['children']:
                    #Assigning parent to child
                    objects[child].parent = parent_obj
            elif 'parents' in data['CityObjects'][theid]: 
                #Assigning child to parent
                objects[theid].parent = objects[data['CityObjects'][theid]['parents'][0]]
                
        print("CityJSON file successfully imported.")
        
    return {'FINISHED'}


class ImportCityJSON(Operator, ImportHelper):
    bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import CityJSON"

    # ImportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    #type: EnumProperty(
    #    name="Example Enum",
    #    description="Choose between two items",
    #    items=(
    #        ('OPT_A', "First Option", "Description one"),
    #        ('OPT_B', "Second Option", "Description two"),
    #    ),
    #    default='OPT_A',
    #)

    def execute(self, context):
        return cityjson_parser(context, self.filepath, self.use_setting)


data="CityJSON"

def write_cityjson(context, filepath, cityjson_export_settings):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    #print("running write_some_data...")
    #f = open(filepath, 'w', encoding='utf-8')
    #f.write("Hello World %s" % use_some_setting)
    #f.close()

    return {'FINISHED'}


#data ="Hello World"


class ExportCityJSON(Operator, ExportHelper):
    bl_idname = "export_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export CityJSON"

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    #type: EnumProperty(
    #    name="Example Enum",
    #    description="Choose between two items",
    #    items=(
    #        ('OPT_A', "First Option", "Description one"),
    #        ('OPT_B', "Second Option", "Description two"),
    #    ),
    #    default='OPT_A',
    #)

    def execute(self, context):
        return write_cityjson(context, self.filepath, self.use_setting)




# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportCityJSON.bl_idname, text="CityJSON (.json)")


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportCityJSON.bl_idname, text="CityJSON (.json)")
    
def register():
    bpy.utils.register_class(ImportCityJSON)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    bpy.utils.register_class(ExportCityJSON)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportCityJSON)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    bpy.utils.unregister_class(ExportCityJSON)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
