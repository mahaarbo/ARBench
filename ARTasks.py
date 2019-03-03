import FreeCAD
import ARTools
import ARFrames
if FreeCAD.GuiUp:
    import os
    import FreeCADGui
    from PySide import QtCore, QtGui, QtSvg
__title__ = "ARTasks"
__author__ = "Mathias Hauan Arbo"
__workbenchname__ = "ARBench"
__version__ = "0.1"
__url__ = "https://github.com/mahaarbo/ARBench"
__doc__ = """"""

# Ideally tasks inherit from base task, and are constructed based on what is
# available in the expert system


###################################################################
## Module objects
###################################################################
class BaseTask(object):
    """
    Base task object that new tasks inherit from.
    """
    def __init__(self, obj):
        obj.Proxy = self

    def onChanged(self, fp, prop):
        pass

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self):
        return None


class InsertTask(BaseTask):
    def __init__(self, obj, holeface, pegface):
        BaseTask.__init__(self, obj)

        # Hole info
        obj.addProperty("App::PropertyLinkSub", "HoleFace",
                        "Feature", "The inner face of the hole.").HoleFace = holeface
        obj.addProperty("App::PropertyString", "HolePart",
                        "Feature", "The part that the holeface is on.").HolePart = holeface[0].Label
        obj.setEditorMode("HolePart", 1)
        obj.addProperty("App::PropertyString", "HoleFaceID",
                        "Feature", "The FaceID associated with the hole.").HoleFaceID = holeface[1]
        obj.setEditorMode("HoleFaceID", 1)
        obj.setEditorMode("HoleFaceID", 1)
        holeface_subelem = holeface[0].Shape.getElement(holeface[1])
        holefeature, temp = ARTools.describeSubObject(holeface_subelem)
        obj.addProperty("App::PropertyString", "HoleFeature",
                        "Feature", "The type of feature of the hole.").HoleFeature = holefeature
        obj.setEditorMode("HoleFeature", 1)

        # Peg info
        obj.addProperty("App::PropertyLinkSub", "PegFace",
                        "Feature", "The outer face of the peg.").PegFace = pegface
        obj.addProperty("App::PropertyString", "PegPart",
                        "Feature", "The part that the pegface is on.").PegPart = pegface[0].Label
        obj.setEditorMode("PegPart", 1)
        pegface_subelem = pegface[0].Shape.getElement(pegface[1])
        pegfeature, temp = ARTools.describeObject(pegface_subelem)
        obj.addProperty("App::PropertyString", "PegPart",
                        "Feature", "The type of feature of the peg.").PegFeature = pegfeature
        obj.setEditorMode("PegFeature", 1)

        # Create Task Frame
        # For now it is set to be pointing down the hole axis.
        if holeface_subelem.Surface.Axis.dot(pegface_subelem.Surface.Axis) < 0:
            p_dist = pegface_subelem.ParameterRange[3]
            v = FreeCAD.Vector(0, 0, 1)
        else:
            p_dist = pegface_subelem.ParameterRange[2]
            v = FreeCAD.Vector(0, 0, -1)
        axis_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), pegface_subelem.Surface.Axis)
        task_frame_rot = FreeCAD.Rotation(v, pegface_subelem.Surface.Axis)

        # pegface can be anywhere on the object, so define it wrt origo from the local
        center_point = pegface_subelem.Surface.Center
        center_placement = FreeCAD.Placement(center_point, axis_rot)
        abs_taskframe_point = center_placement.multVec(FreeCAD.Vector(0, 0, p_dist))
        abs_taskframe_placement = FreeCAD.Placement(abs_taskframe_point, task_frame_rot)
        inv_pegobject_placement = pegface[0].Placement.inverse()

        peglocal_taskframe_placement = inv_pegobject_placement.multiply(abs_taskframe_placement)
        taskframe = ARFrames.makeFeatureFrame(pegface[0], peglocal_taskframe_placement)
        taskframe.Label = obj.Label+"_task_frame"
        obj.addProperty("App::PropertyLink", "TaskFrame", "Process", "The task frame for the insertion task.").TaskFrame = taskframe


class ScrewTask(InsertTask):
    def __init__(self, obj, holeface, screwface):
        BaseTask.__init__(self, obj)
        # Hole info
        obj.addProperty("App::PropertyLinkSub", "HoleFace", "Feature", "The inner face of the screw.").HoleFace = holeface
        obj.addProperty("App::PropertyString", "HolePart", "Feature", "The part that the holeface is on.").HolePart = holeface[0].Label
        obj.setEditorMode("HolePart", 1)
        obj.addProperty("App::PropertyString", "HoleFaceID", "Feature", "The FaceID associated with the hole.").HoleFaceID = holeface[1]
        obj.setEditorMode("HoleFaceID", 1)
        holeface_subelem = holeface[0].Shape.getElement(holeface[1])
        holefeature, temp = ARTools.describeSubObject(holeface_subelem)
        obj.addProperty("App::PropertyString", "HoleFeature", "Feature", "The type of feature of the hole.").HoleFeature = holefeature
        obj.setEditorMode("HoleFaceID", 1)

        # Screw info
        obj.addProperty("App::PropertyLinkSub", "ScrewFace", "Feature", "The outer face of the screw.").ScrewFace = screwface
        obj.addProperty("App::PropertyString", "ScrewPart", "Feature", "The part that the screwface is on").ScrewPart = screwface[0].Label
        obj.setEditorMode("ScrewPart", 1)
        obj.addProperty("App::PropertyString", "ScrewFaceID", "Feature", "The FaceID associated with the screw.").ScrewFaceID = screwface[1]
        obj.setEditorMode("ScrewFaceID", 1)
        screwface_subelem = screwface[0].Shape.getElement(screwface[1])
        screwfeature, temp = ARTools.describeSubObject(screwface_subelem)
        
        # Create Task Frame
        # For now we set the task frame to be pointing down the hole axis.
        if holeface_subelem.Surface.Axis.dot(screwface_subelem.Surface.Axis) < 0:
            p_dist = screwface_subelem.ParameterRange[3]
            v = FreeCAD.Vector(0, 0, 1)
        else:
            p_dist = screwface_subelem.ParameterRange[2]
            v = FreeCAD.Vector(0, 0, -1)
        axis_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), screwface_subelem.Surface.Axis)
        task_frame_rot = FreeCAD.Rotation(v, screwface_subelem.Surface.Axis)

        # Screface can be anywhere on screw object so define it wrt origo then find local
        center_point = screwface_subelem.Surface.Center
        center_placement = FreeCAD.Placement(center_point, axis_rot)
        abs_taskframe_point = center_placement.multVec(FreeCAD.Vector(0, 0, p_dist))
        abs_taskframe_placement = FreeCAD.Placement(abs_taskframe_point, task_frame_rot)
        inv_screwobject_placement = screwface[0].Placement.inverse()

        screwlocal_taskframe_placement = inv_screwobject_placement.multiply(abs_taskframe_placement)
        taskframe = ARFrames.makeFeatureFrame(screwface[0], screwlocal_taskframe_placement)
        taskframe.Label = obj.Label+"_task_frame"
        obj.addProperty("App::PropertyLink", "TaskFrame", "Process", "The task frame for the insertion task.").TaskFrame = taskframe


class PlaceTask(BaseTask):
    def __init__(self, obj, partA, partB):
        BaseTask.__init__(self, obj)
        obj.addProperty("App::PropertyLink", "PartA",
                        "Feature", "The first face.").PartA = partA
        obj.addProperty("App::PropertyLink", "PartB",
                        "Feature", "The second face.").PartB = partB
        obj.setEditorMode("PartA", 1)
        obj.setEditorMode("PartB", 1)
        obj.addProperty("App::PropertyVector", "AssemblyAxis",
                        "Process", "The linear axis to move A onto B.").AssemblyAxis = FreeCAD.Vector()


class CustomTask(BaseTask):
    def __init__(self, obj, partA, partB):
        BaseTask.__init__(self, obj)
        obj.addProperty("App::PropertyLink", "PartA",
                        "Parts", "The first part.").PartA = partA
        obj.addProperty("App::PropertyLink", "PartB",
                        "Parts", "The second part.").PartB = partB
        obj.addProperty("App::PropertyString", "TaskDescription",
                        "Process", "The description of the custom task.").TaskDescription = ""


###################################################################
## ViewProviders to the objects
###################################################################
class ViewProviderBaseTask(object):
    """
    View provider for the base task.
    """
    def __init__(self, vobj):
        vobj.Proxy = self
        col = (0.64, 0., 0., 0.)
        vobj.addProperty("App::PropertyColor", "Color").Color = col

    def attach(self, vobj):
        pass

    def updateData(self, fp, prop):
        pass

    def getDisplayModes(self, vobj):
        modes = []
        return []

    def getDefaultDisplayMode(self):
        return None

    def setDisplayMode(self, mode):
        return mode

    def onChanged(self, vp, prop):
        pass

    def getIcon(self):
        return """"""

    def __getstate__(self):
        return None

    def __setstate__(self):
        return None


###################################################################
## Module functions
###################################################################
def createInsertTask(holeface, pegface):
    a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Task")
    InsertTask(a, holeface, pegface)
    # if FreeCAD.GuiUp:
    #     ViewProviderBaseTask(a.ViewObject)
    return a


def createScrewTask(holeface, screwface):
    a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Task")
    ScrewTask(a, holeface, screwface)
    # if FreeCAD.GuiUp:
    #     ViewProviderBaseTask(a.ViewObject)
    return a


def createCustomTask(partA, partB):
    a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Task")
    CustomTask(a, partA, partB)
    if FreeCAD.GuiUp:
        ViewProviderBaseTask(a.ViewObject)
    return a


def spawnTaskCreator():
    taskpanel = TaskSelectionPanel()
    FreeCADGui.Control.showDialog(taskpanel)


###################################################################
## GUI Commands
###################################################################
if FreeCAD.GuiUp:
    icondir = os.path.join(FreeCAD.getUserAppDataDir(),
                           "Mod", __workbenchname__, "UI", "icons")

    def spawnClassCommand(command_classname,
                          command_function,
                          command_resources):
        """
        Commands, or buttons, are tedious to write. So this function spawns one if the command_function to be executed takes no arguments.
        Example:
        spawnClassCommand("testCommand",testfunc, {"Pixmap":"","MenuText":"test","ToolTip":"Test tooltip"
        then add "testcommand" to commandlist in InitGui.py
        """
        def Activated(s):
            command_function()
        def GetResources(s):
            return command_resources
        commandClass = type("command_classname", (object,), {"Activated":Activated,"GetResources":GetResources})
        FreeCADGui.addCommand(command_classname,commandClass())

    spawnClassCommand("spawnTaskCreatorCommand",spawnTaskCreator, {"Pixmap":str(os.path.join(icondir, "taskcreator.svg")),
                                                                   "MenuText": "Spawn task creator",
                                                                   "ToolTip": "Spawn task creator."})

###################################################################
## GUI widgets
###################################################################
if FreeCAD.GuiUp:
    uidir = os.path.join(FreeCAD.getUserAppDataDir(),"Mod",__workbenchname__, "UI")
    icondir = os.path.join(uidir,"icons")

    class TaskSelectionPanel:
        """Choose appropriate skill"""
        def __init__(self):
            self.form = FreeCADGui.PySideUic.loadUi(os.path.join(uidir,"FeatureFrameCreator.ui"))
            self.choices = ("Insert","Place","Screw")
            self.picked_type = "Insert"
            self.form.ChoicesBox.addItems(self.choices)
            QtCore.QObject.connect(self.form.ChoicesBox,
                                   QtCore.SIGNAL("currentIndexChanged(QString)"),
                                   self.ChoiceChanged)
            self.form.PickedTypeLabel.setText(self.picked_type)
            self.scenes = {}
            iscene = QtGui.QGraphicsScene()
            iscene.addItem(QtSvg.QGraphicsSvgItem(str(os.path.join(icondir, "inserttask.svg"))))
            self.scenes["Insert"] = iscene
            pscene = QtGui.QGraphicsScene()
            pscene.addItem(QtSvg.QGraphicsSvgItem(str(os.path.join(icondir, "placetask.svg"))))
            self.scenes["Place"] = pscene
            sscene = QtGui.QGraphicsScene()
            sscene.addItem(QtSvg.QGraphicsSvgItem(str(os.path.join(icondir, "screwtask.svg"))))
            self.scenes["Screw"] = sscene
            self.ChoiceChanged(self.picked_type)
            
        def ChoiceChanged(self, choice):
            if choice in self.scenes.keys():
                self.picked_type = choice
                self.form.Preview.setScene(self.scenes[choice])
                self.form.PickedTypeLabel.setText(self.picked_type)
        def accept(self):
            paneldict = {"Insert":InsertPanel,
                         "Place":PlacePanel,
                         "Screw":ScrewPanel}
            picked_type = self.form.ChoicesBox.currentText()
            new_panel = paneldict[picked_type]()
            FreeCADGui.Control.closeDialog()
            QtCore.QTimer.singleShot(0,
                                 lambda: FreeCADGui.Control.showDialog(new_panel))

        def reject(self):
            FreeCADGui.Control.closeDialog()


    class InsertPanel(object):
        """Selection panel for the insertion task."""
        def __init__(self):
            self.form = FreeCADGui.PySideUic.loadUi(os.path.join(uidir, "InsertTaskCreator.ui"))
            self.pegsel = None
            self.holesel = None
            QtCore.QObject.connect(self.form.SelectButton,
                                   QtCore.SIGNAL("released()"),
                                   self.FromSelection)
            QtCore.QObject.connect(self.form.AnimateButton,
                                   QtCore.SIGNAL("released()"),
                                   self.Animate)

        def FromSelection(self):
            s = FreeCADGui.Selection.getSelectionEx()
            #Nothing selected, do nothing
            if len(s) == 0:
                FreeCAD.Console.PrintWarning("No part selected.\n")
                return
            #One selected
            elif len(s) == 1:
                if not s[0].HasSubObjects:
                    FreeCAD.Console.PrintWarning("Selection has no subobject.\n")
                if s[0].SubObjects[0].Orientation == "Forward":
                    FreeCAD.Console.PrintMessage("Pegface selected.\n")
                    self.SetPeg(s[0])
                elif s[0].SubObjects[0].Orientation == "Reversed":
                    FreeCAD.Console.PrintMessage("Holeface selected.\n")
                    self.SetHole(s[0])
                else:
                    FreeCAD.Console.PrintWarning("Only handles Forward and Reversed oriented faces.\n")
            else:
                FreeCAD.Console.PrintError("Too many parts involved, undefined behavior.\n")
            return
            
        def ClearPeg(self):
            self.pegsel = None
            self.form.PegPartField.setText("PartLabel")
            self.form.PegFaceIDField.setText("FaceID")
            self.form.PegFeatureSummary.setText("Feature Description")
            return

        def ClearHole():
            self.holesel = None
            self.form.HolePartField.setText("PartLabel")
            self.form.HoleFaceIDField.setText("FaceID")
            self.form.HoleFeatureSummary.setText("Feature Description")
            return
        
        def SetPeg(self,sel):
            self.pegsel = sel
            self.form.PegPartField.setText(sel.Object.Label)
            self.form.PegFaceIDField.setText(sel.SubElementNames[0])
            class_name, prim_class_name = ARTools.describeSubObject(sel.SubObjects[0])
            self.form.PegFeatureSummary.setText(class_name)
            return
        
        def SetHole(self,sel):
            self.holesel = sel
            self.form.HolePartField.setText(sel.Object.Label)
            self.form.HoleFaceIDField.setText(sel.SubElementNames[0])
            class_name, prim_class_name = ARTools.describeSubObject(sel.SubObjects[0])
            self.form.HoleFeatureSummary.setText(class_name)
            return

        def Animate(self):
            FreeCAD.Console.PrintWarning("Not available yet.\n")
            pass

        def accept(self):
            if self.pegsel is None:
                FreeCAD.Console.PrintError("No pegface selected.\n")
                return
            if self.holesel is None:
                FreeCAD.Console.PrintError("No holeface selected.\n")
                return
            holeface = self.holesel.Object, self.holesel.SubElementNames[0]
            pegface = self.pegsel.Object, self.pegsel.SubElementNames[0]
            ins_task = createInsertTask(holeface, pegface)
            txtlabel = self.form.TaskLabelField.text()
            if txtlabel == "":
                txtlabel = "Task"+self.holesel.Object.Label+self.pegsel.Object.Label
            ins_task.Label = txtlabel
            ins_task.TaskFrame.Label = txtlabel+"_task_frame"
            FreeCADGui.Control.closeDialog()
        
        def reject(self):
            FreeCADGui.Control.closeDialog()

    class PlacePanel(object):
        def __init__(self):
            pass
        def SetFaceA(self,sel):
            pass
        def SetFaceB(self,sel):
            pass
        
        def accept(self):
            pass
        def reject(self):
            FreeCADGui.Control.closeDialog()
        
    class ScrewPanel(object):
        def __init__(self):
            self.form = FreeCADGui.PySideUic.loadUi(os.path.join(uidir, "ScrewTaskCreator.ui"))
            self.screwsel = None
            self.holesel = None
            QtCore.QObject.connect(self.form.SelectButton,
                                   QtCore.SIGNAL("released()"),
                                   self.FromSelection)
            QtCore.QObject.connect(self.form.AnimateButton,
                                   QtCore.SIGNAL("released()"),
                                   self.Animate)
        def FromSelection(self):
            s = FreeCADGui.Selection.getSelectionEx()
            #Nothing selected, do nothing
            if len(s) == 0:
                FreeCAD.Console.PrintWarning("No face selected.\n")
            #One selected
            elif len(s) == 1:
                if not s[0].HasSubObjects:
                    FreeCAD.Console.PrintError("Selection has no subobject.\n")
                elif s[0].SubObjects[0].Orientation == "Forward":
                    FreeCAD.Console.PrintMessage("Screwface selected.\n")
                    self.SetScrew(s[0])
                elif s[0].SubObjects[0].Orientation == "Reversed":
                    FreeCAD.Console.PrintMessage("Holeface selected.\n")
                    self.SetHole(s[0])
                else:
                    FreeCAD.Console.PrintError("Only handles Forward and Reversed oriented faces.\n")
            else:
                FreeCAD.Console.PrintError("Too many parts involved, undefined behavior.\n")
            return
        
        def ClearScrew(self):
            self.screwsel = None
            self.form.PegPartField.setText("PartLabel")
            self.form.PegFaceIDField.setText("FaceID")
            self.form.ScrewTypeField.setText("ScrewType")

        def ClearHole(self):
            self.holesel = None
            self.form.HolePartField.setText("PartLabel")
            self.form.HoleFaceIDField.setText("FaceID")
            return
            
        def SetScrew(self,sel):
            self.screwsel = sel
            self.form.PegPartField.setText(sel.Object.Label)
            self.form.PegFaceIDField.setText(sel.SubElementNames[0])
            class_name,  prim_class_name = ARTools.describeSubObject(sel.SubObjects[0])
            self.form.ScrewTypeField.setText("M"+str(int(2*sel.SubObjects[0].Surface.Radius)))
            
            return
        
        def SetHole(self,sel):
            self.holesel = sel
            self.form.HolePartField.setText(sel.Object.Label)
            self.form.HoleFaceIDField.setText(sel.SubElementNames[0])
            return
        
        def Animate(self):
            FreeCAD.Console.PrintWarning("Not available yet.\n")
            pass

        def accept(self):
            if self.screwsel is None:
                FreeCAD.Console.PrintError("No screwface selected.\n")
                return
            if self.holesel is None:
                FreeCAD.Console.PrintError("No holeface selected.\n")
                return
            holeface = self.holesel.Object, self.holesel.SubElementNames[0]
            screwface = self.screwsel.Object, self.screwsel.SubElementNames[0]
            ins_task = createScrewTask(holeface, screwface)
            txtlabel = self.form.TaskLabelField.text()
            if txtlabel == "":
                txtlabel = "task_"+self.holesel.Object.Label+self.screwsel.Object.Label
            ins_task.Label = txtlabel
            ins_task.TaskFrame.Label = txtlabel+"_task_frame"
            FreeCADGui.Control.closeDialog()

        def reject(self):
            FreeCADGui.Control.closeDialog()
