import FreeCAD
import ARTools
if FreeCAD.GuiUp:
    import FreeCADGui
    from pivy import coin
    from PySide import QtCore, QtGui, QtSvg
    import Part
    import os

__title__ = "ARFrames"
__author__ = "Mathias Hauan Arbo"
__workbenchname__ = "ARBench"
__version__ = "0.1"
__url__ = "https://github.com/mahaarbo/ARBench"
__doc__ = """"""


############################################################
# Frame Objects
############################################################
class Frame(object):
    """Basic freestanding frame"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyPlacement",
                        "Placement", "Base",
                        "Placement of the frame")
        obj.Placement = FreeCAD.Placement()
        obj.Proxy = self
        self.obj = obj
        self.additional_data = {}

    def onChanged(self, fp, prop):
        pass

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def getDict(self):
        d = {}
        d["label"] = str(self.obj.Label)
        d["placement"] = ARTools.placement2axisvec(self.obj.Placement)
        d.update(self.additional_data)
        return d


class PartFrame(Frame):
    """Frame rigidly attached to a part frame.
    Inherits the base placement from the part's frame, and placement is
    relative to the part frame.
    """
    def __init__(self, obj, partobj):
        Frame.__init__(self, obj)
        obj.addProperty("App::PropertyPlacementLink",
                        "Part", "Parent",
                        "The part to attach to.")
        obj.Part = partobj
        obj.setEditorMode("Part", 1)

    def execute(self, obj):
        if FreeCAD.GuiUp:
            obj.ViewObject.Proxy.updateData(obj, "Placement")

    def getDict(self):
        d = Frame.getDict(self)
        d["part"] = str(self.obj.Part.Label)
        return d


class FeatureFrame(PartFrame):
    """Frame rigidly attached to a feature.
    The feature frame is attached to a feature on a part. It gives both the
    placement of the feature w.r.t. the part, and the placement from the
    feature."""
    def __init__(self, obj, partobj, featurePlacement):
        PartFrame.__init__(self, obj, partobj)
        obj.addProperty("App::PropertyPlacement",
                        "FeaturePlacement", "Feature",
                        "The frame attached to the feature.")
        obj.addProperty("App::PropertyString",
                        "PrimitiveType", "Feature",
                        "The primitive type of the feature.")
        obj.addProperty("App::PropertyString",
                        "ShapeType", "Feature",
                        "The shape type of the feature.")
        obj.addProperty("App::PropertyString",
                        "Positioning", "Feature",
                        "The type of positioning used during creation.")
        obj.FeaturePlacement = featurePlacement

    def getDict(self):
        d = PartFrame.getDict(self)
        d["featureplacement"] = ARTools.placement2axisvec(self.obj.FeaturePlacement)
        d["shapetype"] = str(self.obj.ShapeType)
        d["positioning"] = str(self.obj.Positioning)
        return d


############################################################
# ViewProvider to the frames
############################################################
class ViewProviderFrame(object):
    """ViewProvider for the basic frame.
    Uses the SOAxiscrosskit to create axises with constant length regardless
    of zoom. Updates position when placement is changed.
    """
    def __init__(self, vobj):
        vobj.addProperty("App::PropertyFloat", "Scale")
        vobj.Scale = 0.12
        vobj.addProperty("App::PropertyFloat", "HeadSize")
        vobj.HeadSize = 3.0
        vobj.addProperty("App::PropertyFloat", "LineWidth")
        vobj.LineWidth = 2.0
        vobj.Proxy = self

    def attach(self, vobj):
        # We only have a shaded visual group
        self.shaded = coin.SoGroup()

        # Takes heavily from SoAxisCrosskit.h,
        # and Toggle_DH_Frames by galou_breizh on the forums
        self.vframe = coin.SoType.fromName("SoShapeScale").createInstance()
        self.vframe.setPart("shape", coin.SoType.fromName("SoAxisCrossKit").createInstance())
        self.vframe.scaleFactor.setValue(0.1)
        ax = self.vframe.getPart("shape", 0)
        cone = ax.getPart("xHead.shape", 0)
        cone.bottomRadius.setValue(vobj.HeadSize)
        cone = ax.getPart("yHead.shape", 0)
        cone.bottomRadius.setValue(vobj.HeadSize)
        cone = ax.getPart("zHead.shape", 0)
        cone.bottomRadius.setValue(vobj.HeadSize)
        lwstring = "lineWidth {0}".format(vobj.LineWidth)
        ax.set("xAxis.appearance.drawStyle", lwstring)
        ax.set("yAxis.appearance.drawStyle", lwstring)
        ax.set("zAxis.appearance.drawStyle", lwstring)
        ax.set("xAxis.pickStyle", "style SHAPE")
        ax.set("yAxis.pickStyle", "style SHAPE")
        ax.set("zAxis.pickStyle", "style SHAPE")

        # Then remember to make it selectable in the viewer
        selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        selectionNode.objectName.setValue(vobj.Object.Name)
        selectionNode.subElementName.setValue("Frame")
        selectionNode.addChild(self.vframe)

        # We would like to place it where we want
        self.transform = coin.SoTransform()
        self.shaded.addChild(self.transform)
        self.shaded.addChild(self.vframe)
        self.shaded.addChild(selectionNode)
        vobj.addDisplayMode(self.shaded, "Shaded")

    def updateData(self, fp, prop):
        if prop == "Placement":
            pl = fp.getPropertyByName("Placement")
            self.transform.translation = (pl.Base.x,
                                          pl.Base.y,
                                          pl.Base.z)
            self.transform.rotation = pl.Rotation.Q

    def getDisplayModes(self, vobj):
        modes = ["Shaded"]
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def getIcon(self):
        icondir = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", __workbenchname__, "UI", "icons")
        return str(os.path.join(icondir, "frame.svg"))

    def onChanged(self, vp, prop):
        if prop == "Scale":
            s = vp.getPropertyByName("Scale")
            self.vframe.scaleFactor.setValue(float(s))
        elif prop == "HeadSize":
            hs = vp.getPropertyByName("HeadSize")
            xcone = self.vframe.getPart("shape", 0).getPart("xHead.shape", 0)
            xcone.bottomRadius.setValue(float(hs))
            ycone = self.vframe.getPart("shape", 0).getPart("yHead.shape", 0)
            ycone.bottomRadius.setValue(float(hs))
            zcone = self.vframe.getPart("shape", 0).getPart("zHead.shape", 0)
            zcone.bottomRadius.setValue(float(hs))
        elif prop == "LineWidth":
            lw = vp.getPropertyByName("LineWidth")
            lwstring = "lineWidth {0}".format(lw)
            ax = self.vframe.getPart("shape", 0)
            ax.set("xAxis.appearance.drawStyle", lwstring)
            ax.set("yAxis.appearance.drawStyle", lwstring)
            ax.set("zAxis.appearance.drawStyle", lwstring)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass


class ViewProviderPartFrame(ViewProviderFrame):
    """View provider to the part frame."""
    def updateData(self, fp, prop):
        if prop == "Placement":
            parentpl = fp.getPropertyByName("Part").Placement
            localpl = fp.Placement
            pl = parentpl.multiply(localpl)
            self.transform.translation = (pl.Base.x,
                                          pl.Base.y,
                                          pl.Base.z)
            self.transform.rotation = pl.Rotation.Q


class ViewProviderFeatureFrame(ViewProviderFrame):
    """View provider to the feature frames."""
    def updateData(self, fp, prop):
        if prop == "Placement":
            parentpl = fp.getPropertyByName("Part").Placement
            featurepl = fp.getPropertyByName("FeaturePlacement")
            localpl = fp.Placement
            pl = parentpl.multiply(featurepl.multiply(localpl))
            self.transform.translation = (pl.Base.x,
                                          pl.Base.y,
                                          pl.Base.z)
            self.transform.rotation = pl.Rotation.Q


###################################################################
# Base functions
###################################################################

def makeFrame(placement=FreeCAD.Placement()):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Frame")
    Frame(obj)
    if FreeCAD.GuiUp:
        ViewProviderFrame(obj.ViewObject)
    return obj


def makePartFrame(part):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "PartFrame")
    PartFrame(obj, part)
    if FreeCAD.GuiUp:
        ViewProviderPartFrame(obj.ViewObject)
    return obj


def makeFeatureFrame(part, featurepl):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "FeatureFrame")
    FeatureFrame(obj, part, featurepl)
    if FreeCAD.GuiUp:
        ViewProviderFeatureFrame(obj.ViewObject)
    return obj


def makeAllPartFrames():
    dc = FreeCAD.activeDocument()
    for part in dc.Objects:
        if isinstance(part, Part.Feature):
            pf = makePartFrame(part)
            pf.Label = "Frame"+str(part.Label)


def spawnFeatureFrameCreator():
    ffpanel = FeatureFramePanel()
    FreeCADGui.Control.showDialog(ffpanel)


###################################################################
# GUI Related
###################################################################
uidir = os.path.join(FreeCAD.getUserAppDataDir(),
                     "Mod", __workbenchname__, "UI")
icondir = os.path.join(uidir, "icons")

ARTools.spawnClassCommand("FrameCommand",
                          makeFrame,
                          {"Pixmap": str(os.path.join(icondir, "frame.svg")),
                           "MenuText": "Make a free frame",
                           "ToolTip": "Make a freestanding reference frame."})

ARTools.spawnClassCommand("AllPartFramesCommand",
                          makeAllPartFrames,
                          {"Pixmap": str(os.path.join(icondir, "allpartframes.svg")),
                           "MenuText": "All part frames",
                           "ToolTip": "Make all part frames."})
ARTools.spawnClassCommand("FeatureFrameCommand",
                          spawnFeatureFrameCreator,
                          {"Pixmap": str(os.path.join(icondir, "featureframecreator.svg")),
                           "MenuText": "Feature frame creator",
                           "ToolTip": "Create a feature frame on selected primitive."})


###################################################################
# GUI buttons
###################################################################
class FeatureFramePanel:
    """Spawn panel choices for a feature."""
    def __init__(self):
        selected = FreeCADGui.Selection.getSelectionEx()
        # Check selection
        if len(selected) == 1:
            selected = selected[0]
            self.selected = selected
        else:
            FreeCAD.Console.PrintError("Multipart selection not available.")
            self.reject()

        if not selected.HasSubObjects:
            FreeCAD.Console.PrintError("Part selected not feature.")
            self.reject()
        elif not len(selected.SubObjects) == 1:
            FreeCAD.Console.PrintError("Multifeature selection not available")
            self.reject()

        # Choices related to selection
        so_desc = ARTools.describeSubObject(selected.SubObjects[0])
        self.so_desc = so_desc
        shape_choices = {
            "Vertex": [],
            "Edge": ["PointOnEdge"],
            "Face": ["PointOnSurface"]
        }
        prim_choices = {
            "ArcOfCircle": ["Center"],
            "ArcOfEllipse": ["Center"],
            "ArcOfHyperBola": ["Center"],
            "ArcOfParabola": ["Center"],
            "BSplineCurve": ["Center"],
            "BezierCurve": ["Center"],
            "Circle": ["Center"],
            "Ellipse": ["Center"],
            "Hyperbola": ["Center"],
            "Parabola": ["Center"],
            "Line": [],
            "BSplineSurface": ["Center"],
            "BezierSurface": ["Center"],
            "Cylinder": ["PointOnCenterline"],
            "Plane": ["Center"],
            "Sphere": ["Center"],
            "Toroid": ["Center"],
            "Cone": ["PointOnCenterline"]
        }
        self.choices = ["PickedPoint"]
        self.choices = self.choices + shape_choices[so_desc[1]]
        self.choices = self.choices + prim_choices[so_desc[0]]
        # Setting up QT form
        uiform_path = os.path.join(uidir, "FeatureFrameCreator.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiform_path)
        self.form.ChoicesBox.addItems(self.choices)
        self.form.PickedTypeLabel.setText(so_desc[0])
        QtCore.QObject.connect(self.form.ChoicesBox,
                               QtCore.SIGNAL("currentIndexChanged(QString)"),
                               self.choiceChanged)
        # Setting up relevant illustrations
        self.scenes = {}
        for choice in self.choices:
            sc = QtGui.QGraphicsScene()
            icon = str(os.path.join(icondir, choice+".svg"))
            sc.addItem(QtSvg.QGraphicsSvgItem(icon))
            self.scenes[choice] = sc
        self.choiceChanged(self.form.ChoicesBox.currentText())

    def choiceChanged(self, choice):
        if choice in self.scenes.keys():
            self.form.Preview.setScene(self.scenes[choice])

    def accept(self):
        sel_choice = self.form.ChoicesBox.currentText()
        paneldict = {"PickedPoint": PickedPointPanel,
                     "PointOnEdge": PointOnEdgePanel,
                     "PointOnSurface": PointOnSurfacePanel,
                     "Center": CenterPanel,
                     "PointOnCenterline": PointOnCenterlinePanel}
        new_panel = paneldict[sel_choice](self.selected, self.so_desc)
        ############## PROBLEM HERE ##################
        FreeCADGui.Control.closeDialog()
        FreeCADGui.Control.showDialog(new_panel)

    def reject(self):
        FreeCADGui.Control.closeDialog()


class BaseFeaturePanel(object):
    """Base feature panel to be inherited from."""
    def __init__(self, selected, so_desc):
        # Handle selected and FF placement
        self.selected = selected
        self.so_desc = so_desc
        # Connect offset to spinboxes
        QtCore.QObject.connect(self.form.XBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.offsetChanged)
        QtCore.QObject.connect(self.form.YBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.offsetChanged)
        QtCore.QObject.connect(self.form.ZBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.offsetChanged)
        QtCore.QObject.connect(self.form.RollBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.offsetChanged)
        QtCore.QObject.connect(self.form.PitchBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.offsetChanged)
        QtCore.QObject.connect(self.form.YawBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.offsetChanged)
        QtCore.QObject.connect(self.form.ScaleBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.scaleChanged)

    def createFrame(self):
        self.fframe = makeFeatureFrame(self.selected.Object, self.local_ffpl)
        self.fframe.PrimitiveType = self.so_desc[0]
        self.fframe.ShapeType = self.so_desc[1]
        ad = ARTools.getPrimitiveInfo(self.so_desc[0],
                                      self.selected.SubObjects[0])
        self.fframe.Proxy.additional_data.update(ad)

    def scaleChanged(self):
        scale = self.form.ScaleBox.value()
        self.fframe.ViewObject.Scale = scale

    def offsetChanged(self):
        disp = FreeCAD.Vector(self.form.XBox.value(),
                              self.form.YBox.value(),
                              self.form.ZBox.value())
        rot = FreeCAD.Rotation(self.form.YawBox.value(),
                               self.form.PitchBox.value(),
                               self.form.RollBox.value())
        offset = FreeCAD.Placement(disp, rot)
        self.fframe.Placement = offset

    def accept(self):
        framelabel = self.form.FrameLabelField.toPlainText()
        if not len(framelabel) == 0:
            self.fframe.Label = framelabel
        FreeCADGui.Control.closeDialog()

    def reject(self):
        FreeCAD.activeDocument().removeObject(self.fframe.Name)
        FreeCADGui.Control.closeDialog()


class PickedPointPanel(BaseFeaturePanel):
    """Create a feature frame at the picked point."""
    # Not very clever. It just places the frame with default rotation.
    def __init__(self, selected, so_desc):
        uiform_path = os.path.join(uidir, "FramePlacer.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiform_path)
        BaseFeaturePanel.__init__(self, selected, so_desc)
        parent_pl = selected.Object.Placement
        abs_pl = FreeCAD.Placement(selected.PickedPoints[0],
                                   FreeCAD.Rotation())
        self.local_ffpl = parent_pl.inverse().multiply(abs_pl)
        self.createFrame()
        self.fframe.Positioning = "PickedPoint"


class PointOnEdgePanel(BaseFeaturePanel):
    """Create a feature frame on an edge."""
    def __init__(self, selected, so_desc):
        uiform_path = os.path.join(uidir, "FramePlacer.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiform_path)
        # Enable the first parameter
        self.form.VLabel.setEnabled(True)
        self.form.VLabel.setVisible(True)
        self.form.VLabel.setText("u")
        self.form.VBox.setEnabled(True)
        self.form.VBox.setVisible(True)
        QtCore.QObject.connect(self.form.VBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.parameterChanged)

        # Enable percentage or param selection
        self.form.OptionsLabel.setEnabled(True)
        self.form.OptionsLabel.setVisible(True)
        self.form.OptionsLabel.setText("Arc param.")
        self.form.OptionsBox.setEnabled(True)
        self.form.OptionsBox.setVisible(True)
        self.form.OptionsBox.addItems(["mm", "%"])
        QtCore.QObject.connect(self.form.OptionsBox,
                               QtCore.SIGNAL("currentIndexChanged(QString)"),
                               self.choiceChanged)
        BaseFeaturePanel.__init__(self, selected, so_desc)

        # Place the frame wherever the values are atm
        self.local_ffpl = FreeCAD.Placement()
        self.createFrame()
        self.fframe.Positioning = "PointOnEdge"
        self.choiceChanged(self.form.OptionsBox.currentText())
        self.parameterChanged()

    def parameterChanged(self):
        value = self.form.VBox.value()
        if self.form.OptionsBox.currentText() == "%":
            value = self.p2mm(value)
        edge = self.selected.SubObjects[0]
        point = edge.valueAt(value)
        tangentdir = edge.tangentAt(value)
        rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0),
                               tangentdir)
        abs_ffpl = FreeCAD.Placement(point, rot)
        parent_pl = self.selected.Object.Placement
        self.local_ffpl = parent_pl.inverse().multiply(abs_ffpl)
        self.fframe.FeaturePlacement = self.local_ffpl
        # force recompute of placement?
        self.fframe.Placement = self.fframe.Placement

    def choiceChanged(self, choice):
        value = self.form.VBox.value()
        if choice == "mm":
            value = self.p2mm(value)
            self.form.VBox.setSuffix("mm")
            parameter_range = self.selected.SubObjects[0].ParameterRange
            self.form.VBox.setRange(*parameter_range)
            self.form.VBox.setSingleStep(0.1)
        elif choice == "%":
            value = self.mm2p(value)
            self.form.VBox.setSuffix("%")
            self.form.VBox.setRange(0, 100.0)
            self.form.VBox.setSingleStep(1.0)
        self.form.VBox.setValue(value)

    def p2mm(self, value):
        parameter_range = self.selected.SubObjects[0].ParameterRange
        delta = parameter_range[1] - parameter_range[0]
        return 0.01*value*delta + parameter_range[0]

    def mm2p(self, value):
        parameter_range = self.selected.SubObjects[0].ParameterRange
        delta = parameter_range[1] - parameter_range[0]
        return 100.0*(value - parameter_range[0])/delta


class PointOnSurfacePanel(BaseFeaturePanel):
    """Create a feature on a surface."""
    def __init__(self, selected, so_desc):
        uiform_path = os.path.join(uidir, "FramePlacer.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiform_path)
        # Enable both parameters
        self.form.ULabel.setVisible(True)
        self.form.VLabel.setVisible(True)
        self.form.UBox.setVisible(True)
        self.form.VBox.setVisible(True)
        QtCore.QObject.connect(self.form.VBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.parameterChanged)
        QtCore.QObject.connect(self.form.UBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.parameterChanged)
        # Enable percentage or param selection
        self.form.OptionsLabel.setEnabled(True)
        self.form.OptionsLabel.setVisible(True)
        self.form.OptionsLabel.setText("Surf. param.")
        self.form.OptionsBox.setEnabled(True)
        self.form.OptionsBox.setVisible(True)
        self.form.OptionsBox.addItems(["mm", "%"])
        QtCore.QObject.connect(self.form.OptionsBox,
                               QtCore.SIGNAL("currentIndexChanged(QString)"),
                               self.choiceChanged)
        BaseFeaturePanel.__init__(self, selected, so_desc)

        # Place the frame wherever the values are atm
        self.local_ffpl = FreeCAD.Placement()
        self.createFrame()
        self.fframe.Positioning = "PointOnSurface"
        self.choiceChanged(self.form.OptionsBox.currentText())
        self.parameterChanged()

    def parameterChanged(self):
        value = (self.form.UBox.value(), self.form.VBox.value())
        if self.form.OptionsBox.currentText() == "%":
            value = self.p2mm(value)
        face = self.selected.SubObjects[0]
        point = face.valueAt(*value)
        normaldir = face.normalAt(*value)
        rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1),
                                    normaldir)
        abs_ffpl = FreeCAD.Placement(point, rotation)
        parent_pl = self.selected.Object.Placement
        self.local_ffpl = parent_pl.inverse().multiply(abs_ffpl)
        self.fframe.FeaturePlacement = self.local_ffpl
        # Force recompute of placement
        self.fframe.Placement = self.fframe.Placement

    def choiceChanged(self, choice):
        value = (self.form.UBox.value(), self.form.VBox.value())
        if choice == "mm":
            value = self.p2mm(value)
            parameter_range = self.selected.SubObjects[0].ParameterRange
            self.form.UBox.setRange(parameter_range[0], parameter_range[1])
            self.form.UBox.setSuffix("mm")
            self.form.UBox.setSingleStep(0.1)
            self.form.VBox.setRange(parameter_range[2], parameter_range[3])
            self.form.VBox.setSuffix("mm")
            self.form.VBox.setSingleStep(0.1)
        elif choice == "%":
            value = self.mm2p(value)
            self.form.UBox.setRange(0.0, 100.0)
            self.form.UBox.setSuffix("%")
            self.form.VBox.setRange(0.0, 100.0)
            self.form.UBox.setSingleStep(1.0)
            self.form.VBox.setSuffix("%")
            self.form.VBox.setSingleStep(1.0)
        self.form.UBox.setValue(value[0])
        self.form.VBox.setValue(value[1])


    def p2mm(self, value):
        parameter_range = self.selected.SubObjects[0].ParameterRange
        delta = [parameter_range[1] - parameter_range[0],
                 parameter_range[3] - parameter_range[2]]
        u = 0.01*value[0]*delta[0] + parameter_range[0]
        v = 0.01*value[1]*delta[1] + parameter_range[2]
        return (u, v)

    def mm2p(self, value):
        parameter_range = self.selected.SubObjects[0].ParameterRange
        delta = [parameter_range[1] - parameter_range[0],
                 parameter_range[3] - parameter_range[2]]
        u = 100.0*(value[0] - parameter_range[0])/delta[0]
        v = 100.0*(value[1] - parameter_range[2])/delta[1]
        return (u, v)


class CenterPanel(BaseFeaturePanel):
    """Create a feature frame on center."""
    def __init__(self, selected, so_desc):
        uiform_path = os.path.join(uidir, "FramePlacer.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiform_path)
        BaseFeaturePanel.__init__(self, selected, so_desc)
        edge_curve_list = ["ArcOfCircle",
                           "ArcOfEllipse",
                           "ArcOfHyperbola",
                           "ArcOfParabola",
                           "Circle",
                           "Ellipse",
                           "Hyperbola",
                           "Parabola"]
        face_surf_list = ["Sphere",
                          "Toroid"]
        if so_desc[0] in edge_curve_list:
            edge = selected.SubObjects[0]
            axis = edge.Curve.Axis
            rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1),
                                        axis)
            center_point = edge.Curve.Center
        elif so_desc[0] in face_surf_list:
            face = selected.SubObjects[0]
            axis = face.Surface.Axis
            rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1),
                                        axis)
            center_point = face.Surface.Center
        else:
            rotation = FreeCAD.Rotation()
            center_point = selected.SubObjects[0].CenterOfMass
        parent_pl = selected.Object.Placement
        abs_pl = FreeCAD.Placement(center_point,
                                   rotation)
        self.local_ffpl = parent_pl.inverse().multiply(abs_pl)
        self.createFrame()
        self.fframe.Positioning = "Center"


class PointOnCenterlinePanel(BaseFeaturePanel):
    """Create a point on centerline of primitive."""
    def __init__(self, selected, so_desc):
        uiform_path = os.path.join(uidir, "FramePlacer.ui")
        self.form = FreeCADGui.PySideUic.loadUi(uiform_path)
        BaseFeaturePanel.__init__(self, selected, so_desc)
        # Enable the along line parameter
        self.form.VLabel.setVisible(True)
        self.form.VLabel.setText("u")
        self.form.VBox.setVisible(True)
        QtCore.QObject.connect(self.form.VBox,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.parameterChanged)
        # Enable percentage of param selection
        self.form.OptionsLabel.setVisible(True)
        self.form.OptionsLabel.setText("Line param.")
        self.form.OptionsBox.setVisible(True)
        self.form.OptionsBox.addItems(["mm", "%"])
        QtCore.QObject.connect(self.form.OptionsBox,
                               QtCore.SIGNAL("currentIndexChanged(QString)"),
                               self.choiceChanged)
        # Place the frame wherever the values are atm
        self.local_ffpl = FreeCAD.Placement()
        self.createFrame()
        self.fframe.Positioning = "PointOnCenterline"
        self.parameterChanged()

    def parameterChanged(self):
        value = self.form.VBox.value()
        if self.form.OptionsBox.currentText() == "%":
            value = self.p2mm(value)
        displacement_pl = FreeCAD.Placement(FreeCAD.Vector(0, 0, value),
                                            FreeCAD.Rotation())
        # Find the center
        axis = self.selected.SubObjects[0].Surface.Axis
        rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1),
                                    axis)
        center_point = self.selected.SubObjects[0].Surface.Center
        center_pl = FreeCAD.Placement(center_point, rotation)
        abs_ffpl = center_pl.multiply(displacement_pl)
        parent_pl = self.selected.Object.Placement
        self.local_ffpl = parent_pl.inverse().multiply(abs_ffpl)
        self.fframe.FeaturePlacement = self.local_ffpl
        # force recompute of placement
        self.fframe.Placement = self.fframe.Placement

    def choiceChanged(self, choice):
        FreeCAD.Console.PrintMessage("choiceChanged\n")
        value = self.form.VBox.value()
        FreeCAD.Console.PrintMessage("preval:"+str(value)+"\n")
        if choice == "mm":
            value = self.p2mm(value)
            self.form.VBox.setSuffix("mm")
            parameter_range = self.selected.SubObjects[0].ParameterRange[2:]
            self.form.VBox.setRange(*parameter_range)
            self.form.VBox.setSingleStep(0.1)
        elif choice == "%":
            value = self.mm2p(value)
            self.form.VBox.setSuffix("%")
            self.form.VBox.setRange(0, 100)
            self.form.VBox.setSingleStep(1.0)
        self.form.VBox.setValue(value)
        FreeCAD.Console.PrintMessage("postval:"+str(value)+"\n")

    def p2mm(self, value):
        parameter_range = self.selected.SubObjects[0].ParameterRange[2:]
        delta = parameter_range[1] - parameter_range[0]
        return 0.01*value*delta + parameter_range[0]

    def mm2p(self, value):
        parameter_range = self.selected.SubObjects[0].ParameterRange[2:]
        delta = parameter_range[1] - parameter_range[0]
        return 100.0*(value - parameter_range[0])/delta
