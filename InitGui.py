class ARBench(Workbench):
    MenuText = "ARBench"
    ToolTip = "Annotation for Robotics workbench"
    Icon = """"""

    def __init__(self):
        import os
        self.Icon = os.path.join(FreeCAD.getUserAppDataDir(), "Mod",
                                 "ARBench", "UI", "icons", "frame.svg")

    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        import ARFrames
        self.framecommands = ["FrameCommand",
                              "AllPartFramesCommand",
                              "FeatureFrameCommand"]
        self.toolcommands = ["ExportPartInfoAndFeaturesDialogueCommand"]
        self.appendToolbar("AR Frames", self.framecommands)
        self.appendToolbar("AR Tools", self.toolcommands)

    def Activated(self):
        """This function is executed when the workbench is activated."""
        #
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated."""
        #
        return

    def ContextMenu(self, recipient):
        """This is execcuted whenever the user right-clicks on screen."""
        pass

    def GetClassName(self):
        # This function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"

Gui.addWorkbench(ARBench())
