import FreeCAD
import Part
if FreeCAD.GuiUp:
    import FreeCADGui


__title__ = "ARTools"
__author__ = "Mathias Hauan Arbo"
__workbenchname__ = "ARBench"
__version__ = "0.1"
__url__ = "https://github.com/mahaarbo/ARBench"
__doc__ = """"""


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


def placement2axisvec(pl):
    """Gives the placement as an dictionary of origin and rotation.
    origin: [x,y,z], rotation:{axis:[ax,ay,az], angle:ang}"""
    return {"origin": vector2list(pl.Base),
            "rotation": {"axis": vector2list(pl.Rotation.Axis, scale=1),
                         "angle": pl.Rotation.Angle}}


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
    then add "testcommand" to commandlist in InitGui.py"""
    def Activated(s):
        function()

    def GetResources(s):
        return resources
    CommandClass = type("classname", (object,), {"Activated": Activated,
                                                 "GetResources": GetResources})
    FreeCADGui.addCommand(classname, CommandClass())
