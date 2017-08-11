import bpy
import os
import shutil

## Set initial Parameters ##
CRS = "EPSG:3358"
watchFolder = os.path.dirname(bpy.path.abspath("//")) + "/" + "Watch"
scratchFolder = os.path.dirname(bpy.path.abspath("//")) + "/" + "scratch"

class adapt:
    ''' Adapt the scene objects based on viewpoint and texture files'''
    
    def __init__(self):
        self.terrain = "DSM"
        self.viewpoint = "Torus"
        filePath = os.path.dirname(bpy.path.abspath("//"))
        fileName = os.path.join(filePath,'vpoints.shp')

    def viewshed(self,texture,vpoint):
        ''' Recieve and process viewshed point shape file and texture '''

        ## import the shapefile, move viewmarker and delete the shapefile ##
        vpointDir = os.path.join (watchFolder,vpoint)
        vpointFile = vpointDir + "/" + vpoint + ".shp"
        if not bpy.data.objects.get(vpoint):
            bpy.ops.importgis.shapefile(filepath=vpointFile,fieldElevName="elev",
            shpCRS='EPSG:3358')
            
        bpy.data.objects[self.viewpoint].location = bpy.data.objects[vpoint].location
        shutil.rmtree(vpointDir)
        
        ## assign change terrain's texture file ##
        if bpy.data.objects.get(self.terrain):
            bpy.data.objects[self.terrain].select = True
            # remove the texture file from the directory 
            os.remove(os.path.join(watchFolder,texture))

        # Change the material emmission shader texture # 
        
        if not bpy.data.images.get(texture):
            texpath = os.path.join(scratchFolder,texture)
            bpy.data.images.load(texpath)
    
        # get the active object material #
        mat = bpy.data.materials.get("Material")
        # Get material tree , nodes and links #
        nodes = mat.node_tree.nodes
        nodes.active = nodes[5]
        #Replace the texture #
        nodes[5].image = bpy.data.images[texture]
        

class Modal_watch(bpy.types.Operator):
        """Operator which interatively runs from a timer"""

        bl_idname = "wm.loose_coupling_timer"
        bl_label = "loose coupling timer"
        _timer = 0
        _timer_count = 0

        def modal(self, context, event):
            if event.type in {"RIGHTMOUSE", "ESC"}:
                return {"CANCELLED"}

            # this condition encomasses all the actions required for watching
            # the folder and related file/object operations

            if event.type == "TIMER":

                if self._timer.time_duration != self._timer_count:
                    self._timer_count = self._timer.time_duration
                    fileList = (os.listdir(watchFolder))
                    # Tree patches #
                    for fileName in fileList:
                        if ".png" in fileName:
                            vpoint = "viewpoint_" + fileName.split(".")[0]
                            if vpoint in fileList:
                                adapt().viewshed(fileName,vpoint)
                                self.adaptMode = "VIEWSHED"
            return {"PASS_THROUGH"}

        def execute(self, context):

            bpy.context.space_data.show_manipulator = False
            wm = context.window_manager
            wm.modal_handler_add(self)
            self._timer = wm.event_timer_add(1, context.window)
            self.adaptMode = None

            return {"RUNNING_MODAL"}

        def cancel(self, context):
            wm = context.window_manager
            wm.event_timer_remove(self._timer)


class Modal_copy(bpy.types.Operator):
        """Operator which interatively runs from a timer"""

        bl_idname = "wm.copy_files"
        bl_label = "copy files to watch folder"
        _timer = 0
        _timer_count = 0
        _index = 0


        def modal(self, context, event):
            if event.type in {"RIGHTMOUSE", "ESC"}:
                return {"CANCELLED"}

            if event.type == "TIMER":
                if self._index == len(self.copyList):
                    self._index = 0
                if self._timer.time_duration != self._timer_count:

                    if self.copyList and not os.listdir(watchFolder):
                        item = self.copyList[self._index]
                        if item not in self._copiedList:
                            fileSrc = os.path.join(scratchFolder, item[1])
                            fileDst = os.path.join(watchFolder, item[1])
                            dirSrc = os.path.join(scratchFolder, item[2])
                            dirDst = os.path.join(watchFolder, item[2])
                            shutil.copytree(dirSrc, dirDst)
                            shutil.copyfile(fileSrc, fileDst)
                            self._copiedList.append(item)
                            self._index += 1
            return {"PASS_THROUGH"}

        def execute(self, context):

            wm = context.window_manager
            wm.modal_handler_add(self)
            self._timer = wm.event_timer_add(1, context.window)
            fileList = os.listdir(scratchFolder)
            self._copiedList = []
            self.copyList = []
            for f in fileList:
                if ".png" in f:
                    vpointDir = "viewpoint_" + f.split(".")[0]

                    if vpointDir in fileList:
                        self.copyList.append((int(f.split(".")[0]),f,vpointDir))

            self.copyList = sorted(self.copyList)

            return {"RUNNING_MODAL"}

        def cancel(self, context):

            wm = context.window_manager
            wm.event_timer_remove(self._timer)


class Panel(bpy.types.Panel):
    # Create a Panel in the Tool Shelf
    bl_category = "Coupling"
    bl_label = "Coupling widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    # Draw
    def draw(self, context):

        layout = self.layout
        wm = context.window_manager

        row = layout.row(align=True)
        row.operator("wm.loose_coupling_timer",
                     text="WatchMode",
                     icon="GHOST_ENABLED")

        row.operator("wm.copy_files",
                     text="Copy_files",
                     icon="NLA")

# Register
def register(module):
    bpy.utils.register_module(module)

def unregister(module):
    bpy.utils.unregister_module(module)

if __name__ == "__main__":
    # register all Classes
    register(__name__)
