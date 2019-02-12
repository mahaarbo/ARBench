import FreeCAD
import Part
import json  # For exporting part infos
import os    # for safer path handling
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui

__title__ = "ARTools"
__author__ = "Mathias Hauan Arbo"
__workbenchname__ = "ARBench"
__version__ = "0.1"
__url__ = "https://github.com/mahaarbo/ARBench"
__doc__ = """
Useful tools for the Annotations for Robotics workbench."""


###################################################################
# Module functions
###################################################################
def vector2list(vec, scale=1e-3):
    """Gives the vector as a list, set scale for scaling factor.
    default scale = 1e-3 for units in m."""
    return [vec.x*scale, vec.y*scale, vec.z*scale]


def matrix2list(mat, scale=1e-3):
    """Gives the transformation matrix as a list, set scale 1 to get in mm."""
    return [[mat.A11, mat.A12, mat.A13, mat.A14*scale],
            [mat.A21, mat.A22, mat.A23, mat.A24*scale],
            [mat.A31, mat.A32, mat.A33, mat.A34*scale],
            [mat.A41, mat.A42, mat.A43, mat.A44]]


def placement2axisvec(pl, scale=1e-3):
    """Gives the placement as an dictionary of origin and rotation.
    origin: [x,y,z], rotation:{axis:[ax,ay,az], angle:ang}"""
    return {"origin": vector2list(pl.Base, scale),
            "rotation": {"axis": vector2list(pl.Rotation.Axis, scale=1),
                         "angle": pl.Rotation.Angle}}


def boundingBox2list(bb, scale=1e-3):
    """Gives the bounding box as a list in m instead of mm"""
    return [bb.XMin*scale, bb.XMax*scale,
            bb.YMin*scale, bb.YMax*scale,
            bb.ZMin*scale, bb.ZMax*scale]


def principalProperties2dict(pp, scale=1e-3):
    npp = {}
    for key, value in pp.iteritems():
        if type(value) is FreeCAD.Vector:
            npp[key.lower()] = vector2list(value, scale=1e-3)
        else:
            npp[key.lower()] = value
    return npp


def describeSubObject(subobj):
    """Returns PrimitiveType, ShapeType."""
    if isinstance(subobj, Part.Vertex):
        return "Vertex", "Vertex"
    elif isinstance(subobj, Part.Edge):
        if isinstance(subobj.Curve, Part.Arc):
            return "Arc", "Edge"
        elif isinstance(subobj.Curve, Part.ArcOfCircle):
            return "ArcOfCircle", "Edge"
        elif isinstance(subobj.Curve, Part.ArcOfEllipse):
            return "ArcOfEllipse", "Edge"
        elif isinstance(subobj.Curve, Part.ArcOfHyperbola):
            return "ArcOfHyperbola", "Edge"
        elif isinstance(subobj.Curve, Part.ArcOfParabola):
            return "ArcOfParabola", "Edge"
        elif isinstance(subobj.Curve, Part.BSplineCurve):
            return "BSplineCurve", "Edge"
        elif isinstance(subobj.Curve, Part.BezierCurve):
            return "BezierCurve", "Edge"
        elif isinstance(subobj.Curve, Part.Circle):
            return "Circle", "Edge"
        elif isinstance(subobj.Curve, Part.Ellipse):
            return "Ellipse", "Edge"
        elif isinstance(subobj.Curve, Part.Hyperbola):
            return "Hyperbola", "Edge"
        elif isinstance(subobj.Curve, Part.Line):
            return "Line", "Edge"
        elif isinstance(subobj.Curve, Part.Parabola):
            return "Parabola", "Edge"
        else:
            FreeCAD.Console.PrintError("Unknown edge type")
    elif isinstance(subobj, Part.Face):
        if isinstance(subobj.Surface, Part.BSplineSurface):
            return "BSplineSurface", "Face"
        elif isinstance(subobj.Surface, Part.BezierSurface):
            return "BezierSurface", "Face"
        elif isinstance(subobj.Surface, Part.Cylinder):
            return "Cylinder", "Face"
        elif isinstance(subobj.Surface, Part.Plane):
            return "Plane", "Face"
        elif isinstance(subobj.Surface, Part.Sphere):
            return "Sphere", "Face"
        elif isinstance(subobj.Surface, Part.Toroid):
            return "Toroid", "Face"
        elif isinstance(subobj.Surface, Part.Cone):
            return "Cone", "Face"
        else:
            FreeCAD.Console.PrintError("Unknown surface type")
    # Better strategy desirable for the following:
    elif isinstance(subobj, Part.Wire):
        return "Wire", "Wire"
    elif isinstance(subobj, Part.Shell):
        return "Shell", "Shell"
    elif isinstance(subobj, Part.Solid):
        return "Solid", "Solid"
    elif isinstance(subobj, Part.Compsolid):
        return "Compsolid", "Compsolid"
    elif isinstance(subobj, Part.Compound):
        return "Compound", "Compound"
    else:
        FreeCAD.Console.PrintError("Unable to identify subobject.")


def closeToZero(a, tol=1e-10):
    return abs(a) < tol


def spawnClassCommand(classname, function, resources):
    """
    Commands, or buttons, are tedious to write. So this function spawns
    one if the function to be executed takes no arguments.
    Example usage:
    spawnClassCommand("testcommand", testfunc,
    {"Pixmap":"", "MenuText":"menutext","ToolTip":"tooltiptext"})
    then add "testcommand" to commandlist in InitGui.py
    """
    def Activated(s):
        function()

    def GetResources(s):
        return resources
    CommandClass = type("classname", (object,), {"Activated": Activated,
                                                 "GetResources": GetResources})
    FreeCADGui.addCommand(classname, CommandClass())


def getLocalPartProps(obj):
    old_placement = obj.Placement
    obj.Placement = FreeCAD.Placement()
    # Part properties
    partprops = {
        "label": obj.Label,
        "placement": placement2axisvec(old_placement),
        "boundingbox": boundingBox2list(obj.Shape.BoundBox),
        "volume": obj.Shape.Volume*1e-9,
        "centerofmass": vector2list(obj.Shape.CenterOfMass),
        "principalproperties": principalProperties2dict(obj.Shape.PrincipalProperties)
    }
    obj.Placement = old_placement
    return partprops


###################################################################
# Export functions
###################################################################
def exportPartInfo(obj, ofile):
    """
    Exports part info to a new json file.
    The part info includes:
    Placement relative to world frame, bounding box, volume, center of mass,
    principal properties.
    For more information on principal properties, see TopoShape in OCCT
    documentation.
    """
    # File path stuff
    odir, of = os.path.split(ofile)
    if not os.path.exists(odir):
        os.makedirs(odir)
    if not of.lower().endswith(".json"):
        ofile = ofile + ".json"

    partprops = getLocalPartProps(obj)
    with open(ofile, "wb") as propfile:
        json.dump(partprops, propfile, indent=1, separators=(',', ': '))
    return True


def appendPartInfo(obj, ofile):
    """Rewrites/appends part info to an existing json file.
    The part info includes:
    Placement relative to world frame, bounding box, volume, center of mass,
    principal properties.
    For more information on principal properties, see TopoShape in OCCT
    documentation.
    """
    with open(ofile, "rb") as propfile:
        partprops = json.load(propfile)
    new_props = getLocalPartProps(obj)
    partprops.update(new_props)
    with open(ofile, "wb") as propfile:
        json.dump(partprops, propfile, indent=1, separators=(',', ': '))
    return True


def exportFeatureFrames(obj, ofile):
    """Exports feature frames attached to a part."""
    # Get the feature frames
    import ARFrames
    ff_check = lambda x: isinstance(x.Proxy, ARFrames.FeatureFrame)
    ff_list = filter(ff_check, obj.InList)
    ff_named = {ff.Label: ff.Proxy.getDict() for ff in ff_list}
    feature_dict = {"features": ff_named}

    # File stuff
    odir, of = os.path.split(ofile)
    if not os.path.exists(odir):
        os.makedirs(odir)
    if not of.lower().endswith(".json"):
        ofile = ofile + ".json"
    with open(ofile, "wb") as propfile:
        json.dump(feature_dict, propfile, indent=1, separators=(',', ': '))
    return True


def appendFeatureFrames(obj, ofile):
    """Rewrites/appends featureframes attached to a part to an existing json
    file."""
    # Get the feature frames
    import ARFrames
    with open(ofile, "rb") as propfile:
        partprops = json.load(propfile)
    ff_check = lambda x: isinstance(x.Proxy, ARFrames.FeatureFrame)
    ff_list = filter(ff_check, obj.InList)
    ff_named = {ff.Label: ff.Proxy.getDict() for ff in ff_list}
    feature_dict = {"features": ff_named}
    if "features" not in partprops.keys():
        partprops.update(feature_dict)
    else:
        partprops["features"].update(feature_dict["features"])
    with open(ofile, "wb") as propfile:
        json.dump(partprops, propfile, indent=1, separators=(',', ': '))
    return True


def exportPartInfoDialogue():
    """Spawns a dialogue window for part info exporting"""
    # Select only true parts
    s = FreeCADGui.Selection.getSelection()
    FreeCADGui.Selection.clearSelection()
    if len(s) == 0:
        FreeCAD.Console.PrintError("No part selected.")
        return False
    unique_selected = []
    for item in s:
        if item not in unique_selected and isinstance(item, Part.Feature):
            # Ensuring that we are parts
            unique_selected.append(item)
            FreeCADGui.Selection.addSelection(item)
    # Fix wording
    textprompt = "Save the properties of the part"
    if len(unique_selected) > 1:
        textprompt = textprompt + "s"
    opts = QtGui.QFileDialog.DontConfirmOverwrite
    # Create file dialog
    ofile, filt = QtGui.QFileDialog.getSaveFileName(None, textprompt,
                                                    os.getenv("HOME"),
                                                    "*.json", options=opts)
    if ofile == "":
        # User cancelled
        return False
    if os.path.exists(ofile):
        msgbox = QtGui.QMessageBox()
        msgbox.setText("File already exists. We can overwrite the file, or add the information/rewrite only relevant sections.")
        append_button = msgbox.addButton(unicode("Append"),
                                         QtGui.QMessageBox.YesRole)
        overwrite_button = msgbox.addButton(unicode("Overwrite"),
                                            QtGui.QMessageBox.NoRole)
        msgbox.exec_()
        if msgbox.clickedButton() == append_button:
            NEWFILE = False
        elif msgbox.clickedButton() == overwrite_button:
            NEWFILE = True
        else:
            return False
    else:
        NEWFILE = True
    if NEWFILE:
        exportPartInfo(unique_selected[0], ofile)
    else:
        appendPartInfo(unique_selected[0], ofile)

    if len(unique_selected) > 1:
        FreeCAD.Console.PrintWarning("Multi-part export not yet supported\n")
    FreeCAD.Console.PrintMessage("Properties exported to "+str(ofile)+"\n")


def exportFeatureFramesDialogue():
    """Spawns a dialogue window for a part's feature frames to be exported."""
    # Select only true parts
    s = FreeCADGui.Selection.getSelection()
    FreeCADGui.Selection.clearSelection()
    if len(s) == 0:
        FreeCAD.Console.PrintError("No part selected.")
        return False
    unique_selected = []
    for item in s:
        if item not in unique_selected and isinstance(item, Part.Feature):
            # Ensuring that we are parts
            unique_selected.append(item)
            FreeCADGui.Selection.addSelection(item)
    # Fix wording
    textprompt = "Save the feature frames attached to the part"
    if len(unique_selected) > 1:
        textprompt = textprompt + "s"
    opts = QtGui.QFileDialog.DontConfirmOverwrite
    # Create file dialog
    ofile, filt = QtGui.QFileDialog.getSaveFileName(None, textprompt,
                                                    os.getenv("HOME"),
                                                    "*.json", options=opts)
    if ofile == "":
        # User cancelled
        return False
    if os.path.exists(ofile):
        msgbox = QtGui.QMessageBox()
        msgbox.setText("File already exists. We can overwrite the file, or add the information/rewrite only relevant sections.")
        append_button = msgbox.addButton(unicode("Append"),
                                         QtGui.QMessageBox.YesRole)
        overwrite_button = msgbox.addButton(unicode("Overwrite"),
                                            QtGui.QMessageBox.NoRole)
        msgbox.exec_()
        if msgbox.clickedButton() == append_button:
            NEWFILE = False
        elif msgbox.clickedButton() == overwrite_button:
            NEWFILE = True
        else:
            return False
    else:
        NEWFILE = True
    if NEWFILE:
        exportFeatureFrames(unique_selected[0], ofile)
    else:
        appendFeatureFrames(unique_selected[0], ofile)
    if len(unique_selected) > 1:
        FreeCAD.Console.PrintWarning("Multi-part export not yet supported\n")
    FreeCAD.Console.PrintMessage("Feature frames of " + str(unique_selected[0].Label) + " exported to " + str(ofile) + "\n")


def exportPartInfoAndFeaturesDialogue():
    """Spawns a dialogue window for exporting both."""
    s = FreeCADGui.Selection.getSelection()
    FreeCADGui.Selection.clearSelection()
    if len(s) == 0:
        FreeCAD.Console.PrintError("No part selected.")
        return False
    unique_selected = []
    for item in s:
        if item not in unique_selected and isinstance(item, Part.Feature):
            # Ensuring that we are parts
            unique_selected.append(item)
            FreeCADGui.Selection.addSelection(item)
    # Fix wording
    textprompt = "Save the part info and feature frames attached to the part"
    if len(unique_selected) > 1:
        textprompt = textprompt + "s"
    opts = QtGui.QFileDialog.DontConfirmOverwrite
    # Create file dialog
    ofile, filt = QtGui.QFileDialog.getSaveFileName(None, textprompt,
                                                    os.getenv("HOME"),
                                                    "*.json", options=opts)
    if ofile == "":
        # User cancelled
        return False
    if os.path.exists(ofile):
        msgbox = QtGui.QMessageBox()
        msgbox.setText("File already exists. We can overwrite the file, or add the information/rewrite only relevant sections.")
        append_button = msgbox.addButton(unicode("Append"),
                                         QtGui.QMessageBox.YesRole)
        overwrite_button = msgbox.addButton(unicode("Overwrite"),
                                            QtGui.QMessageBox.NoRole)
        msgbox.exec_()
        if msgbox.clickedButton() == append_button:
            NEWFILE = False
        elif msgbox.clickedButton() == overwrite_button:
            NEWFILE = True
        else:
            return False
    else:
        NEWFILE = True
    if NEWFILE:
        exportPartInfo(unique_selected[0], ofile)
        appendFeatureFrames(unique_selected[0], ofile)
    else:
        appendPartInfo(unique_selected[0], ofile)
        appendFeatureFrames(unique_selected[0], ofile)
    if len(unique_selected) > 1:
        FreeCAD.Console.PrintWarning("Multi-part export not yet supported.\n")
    FreeCAD.Console.PrintMessage("Feature frames of "
                                 + str(unique_selected[0].Label)
                                 + " exported to " + str(ofile) + "\n")


###################################################################
# GUI Commands
###################################################################
uidir = os.path.join(FreeCAD.getUserAppDataDir(),
                     "Mod", __workbenchname__, "UI")
icondir = os.path.join(uidir, "icons")
spawnClassCommand("ExportPartInfoAndFeaturesDialogueCommand",
                  exportPartInfoAndFeaturesDialogue,
                  {"Pixmap": str(os.path.join(icondir, "parttojson.svg")),
                   "MenuText": "Export info and featureframes",
                   "ToolTip": "Export part properties (placement, C.O.M) and feature frames"})


###################################################################
# Information from primitive type
###################################################################
def getPrimitiveInfo(prim_type, subobj, scale=1e-3):
    """returns a dictionary of the primitive's specific information."""
    d = {}
    if prim_type == "ArcOfCircle":
        d["radius"] = scale*subobj.Curve.Radius
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "ArcOfEllipse":
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["majorradius"] = scale*subobj.Curve.MajorRadius
        d["minorradius"] = scale*subobj.Curve.MinorRadius
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "ArcOfHyperBola":
        d["anglexu"] = subobj.Curve.AngleXU
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["majorradius"] = scale*subobj.Curve.MajorRadius
        d["minorradius"] = scale*subobj.Curve.MinorRadius
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "ArcOfParabola":
        d["anglexu"] = subobj.Curve.AngleXU
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["focal"] = scale*subobj.Curve.Focal
    elif prim_type == "BSplineCurve":
        FreeCAD.Console.PrintWarning("getPrimitiveInfo of BSpline incomplete.")
    elif prim_type == "BezierCurve":
        FreeCAD.Console.PrintWarning("getPrimitiveInfo of Bezier incomplete.")
    elif prim_type == "Circle":
        d["radius"] = scale*subobj.Curve.Radius
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "Ellipse":
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["majorradius"] = scale*subobj.Curve.MajorRadius
        d["minorradius"] = scale*subobj.Curve.MinorRadius
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "Hyperbola":
        d["anglexu"] = subobj.Curve.AngleXU
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["majorradius"] = scale*subobj.Curve.MajorRadius
        d["minorradius"] = scale*subobj.Curve.MinorRadius
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "Parabola":
        d["anglexu"] = subobj.Curve.AngleXU
        d["axis"] = vector2list(subobj.Curve.Axis, scale=1)
        d["center"] = vector2list(subobj.Curve.Center, scale)
        d["focal"] = scale*subobj.Curve.Focal
    elif prim_type == "Line":
        if int(FreeCAD.Version()[1]) > 16:
            sp = subobj.valueAt(subobj.FirstParameter)
            ep = subobj.valueAt(subobj.LastParameter)
            d["startpoint"] = vector2list(sp)
            d["endpoint"] = vector2list
        else:
            if not hasattr(subobj.Curve, "Infinite"):
                d["startpoint"] = vector2list(subobj.Curve.StartPoint)
                d["endpoint"] = vector2list(subobj.Curve.EndPoint)
            if hasattr(subobj.Curve, "Infinite"):
                if subobj.Curve.Infinite:
                    d["infinite"] = subobj.Curve.Infinite
                else:
                    d["startpoint"] = vector2list(subobj.Curve.StartPoint)
                    d["endpoint"] = vector2list(subobj.Curve.EndPoint)
    elif prim_type == "BSplineSurface":
        FreeCAD.Console.PrintWarning("getPrimitiveInfo of BSpline incomplete.")
    elif prim_type == "BezierSurface":
        FreeCAD.Console.PrintWarning("getPrimitiveInfo of Bezier incomplete.")
    elif prim_type == "Cylinder":
        d["axis"] = vector2list(subobj.Surface.Axis, scale=1)
        d["radius"] = scale*subobj.Surface.Radius
        d["center"] = vector2list(subobj.Surface.Center)
        PR = list(subobj.ParameterRange)
        PR[2] = PR[2]*scale
        PR[3] = PR[3]*scale
        d["parameterrange"] = PR
    elif prim_type == "Plane":
        d["axis"] = vector2list(subobj.Surface.Axis, scale=1)
        d["position"] = vector2list(subobj.Surface.Position, scale)
        d["parameterrange"] = [scale*i for i in subobj.ParameterRange]
    elif prim_type == "Sphere":
        d["axis"] = vector2list(subobj.Surface.Axis, scale=1)
        d["center"] = vector2list(subobj.Surface.Center, scale)
        d["radius"] = scale*subobj.Surface.Radius
        d["parameterrange"] = subobj.ParameterRange
    elif prim_type == "Toroid":
        d["axis"] = vector2list(subobj.Surface.Axis, scale=1)
        d["center"] = vector2list(subobj.Surface.Center, scale)
        d["majorradius"] = scale*subobj.Surface.MajorRadius
        d["minorradius"] = scale*subobj.Surface.MinorRadius
        d["parameterrange"] = subobj.Surface.ParameterRange
    elif prim_type == "Cone":
        d["axis"] = vector2list(subobj.Surface.Axis, scale=1)
        d["center"] = vector2list(subobj.Surface.Center, scale)
        d["radius"] = scale*subobj.Surface.Radius
        d["semiangle"] = subobj.Surface.SemiAngle
        d["parameterrange"] = subobj.ParameterRange
        FreeCAD.Console.PrintWarning("getPrimitiveInfo of Cone may have wrong ParameterRange.")
    return d
