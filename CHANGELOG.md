# Changelog

All notable changes to this project will be documented in this file.

## [0.7.1] - 2024-10-31

### Bug Fixes

- *(plaxis_2d)* Set the correct port in method connect Plaxis2DOutputController and correct the name of the environmental variables

## [0.7.0] - 2024-10-31

### Features

- *(plaxis_2d)* Add Plaxis2DOutputController
- *(#47)* Update the name comparison to consider lower case.

## [0.6.1] - 2023-11-22

### Features

- *(#43)* Add readme to installation windows.

## [0.6.0] - 2023-11-21

### Features

- *(#41)* Add the environmental variable CEMS_PYTHON_DIR to be used in the installation scripts. Make the installation script also reusable for update.
- *(#41)* Add first version of the install scripts for windows.
- *(#37)* Add method to filter cut volumes by name criteria.
- *(#36)* Add method to filter cut volumes below polygons.

### Miscellaneous Tasks

- *(#35)* Loop through unique cut volumes in method `get_nodes_per_cut_volume`.

## [0.5.1] - 2023-11-16

### Features

- *(#33)* Fix method `get_nodes_per_cut_volume` to consider all volumes in Plaxis3DOutputController.

## [0.5.0] - 2023-11-15

### Features

- *(#29)* [**breaking**] Improve method `filter_cut_volumes_above_polygons` to consider all the vertices of the cut_volumes, instead of only the centroid of the bounding box.

## [0.4.0] - 2023-11-15

### Features

- *(#28)* Add method to map convex hulls per cut volume in Plaxis3DOutputController.
- *(#27)* Add class ConvexHull3D.
- *(#22)* Add method to get nodes per cut volume in Plaxis3DOutputController.
- *(#25)* Add class Node3D.
- *(#21)* Add class Plaxis3DOutputController.

## [0.3.0] - 2023-11-10

### Bug Fixes

- *(#19)* Fix method `filter_volumes_above_polygons` to consider both all the SoilVolumes and Volumes in plaxis and not only the Volumes.

## [0.2.0] - 2023-11-10

### Bug Fixes

- *(#17)* Fix of formula to calculate the z-coordinate of plane at x,y coordinates.

### Features

- *(#17)* Add method to filter plaxis volume objects above a list of polygons.
- *(#15)* Add method to project point3d onto polygon3d.
- *(#13)* Add class Polygon3D.
- *(#11)* Add classes BoundingBox3D and Point3D

### Lint

- *(#15)* Exclude numpy missing imports from mypy.
- *(#13)* Fix lint to ignore the missing imports from the package skspatial.
- *(#11)* Fix linting in bounding_box_3d.

## [0.1.0] - 2023-11-09

### Bug Fixes

- *(#1)* Fix issue with tests not using any module from plxcontroller.

### Features

- *(#1)* Add files according to version 0.1.0.

### Update

- *(#9)* Update image in Plaxis3D_input_controller notebook.

<!-- CEMS BV. -->
