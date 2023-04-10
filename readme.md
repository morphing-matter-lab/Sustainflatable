# Sustainflatable Design Tool

## Installation
Our design tool can correctly run on Rhino 7.4 on Windows. Several plugins for Rhino Grasshopper need to be installed, which are: 

- [Mesh Pipe](https://www.grasshopper3d.com/forum/topics/mesh-pipe)
- [Human](https://www.food4rhino.com/en/app/human)
- [Human UI](https://www.food4rhino.com/en/app/human-ui)

## Usage
To launch the design tool, you may open the `sustainflatable design tool.3dm` file first, which contains a few pre-defined 3D models and render settings. Next, open GrassHopper in Rhino, then opens the `sustainflatable design tool.gh` file to pop out the GUI console. You can follow the above steps to test whether the design tool runs correctly and also create your own project based on the file.

To use the design tool, you may follow the steps presented in our paper for further instructions.

## Secondary Development
The source file for the design tool is `sustainflatable design tool.gh`, which contains the simulation program (done with python components) and UI implementation. We also provide an external file `simulation_kernal.py`, which contains the primary simulation program and can be easily edited/debugged in other IDEs outside the Grasshopper platform. Noted that the external file and the design tool are not connected currently, i.e., updates should be synchronized manually.
