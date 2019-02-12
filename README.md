# Arbench
Annotation for robotics bench. A FreeCAD workbench for annotating frames of interest, exporting these w.r.t. the part frame, and exporting part information.

# Installation instructions
This workbench supports versions of FreeCAD>0.16.

1. [Install FreeCAD](https://www.freecadweb.org/wiki/Installing)
2. If you're not on Ubuntu follow the [workbench installation instructions](https://www.freecadweb.org/wiki/How_to_install_additional_workbenches) or you can do the following on Ubuntu.
3. Custom workbenches are located in `.FreeCAD/Mod/` under your home directory
`cd ~/.FreeCAD/Mod/`
3. Either
   - Clone the repository there
   - symlink the cloned repo in there (`ln -s ./ARBench ~/.FreeCAD/ARBench`)
4. Start the workbench by
   1. Running FreeCAD
   2. Open a STEP file
   3. Open the `ARBench` workbench

# Usage

1. Click a small feature e.g. a circle
2. Press the feature frame creator (cone with a magnifying glass on it icon)
3. Chose type of feature to create
4. Chose feature parameters if relevant and the offset of the frame from the feature.
5. Repeat 4 for each feature you want on each part
6. Click a part and press the export to json button (block->textfile icon)
7. Save json
8. Use the json with whatever you want. E.g. [`arbench_part_publisher`](https://github.com/mahaarbo/arbench_part_publisher)
