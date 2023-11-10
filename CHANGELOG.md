# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2023-11-10

### Features

- *(#17)* Add method to filter plaxis volume objects above a list of polygons.
- *(#15)* Add method to project point3d onto polygon3d.
- *(#13)* Add class Polygon3D.
- *(#11)* Add classes BoundingBox3D and Point3D

### Bug Fixes

- *(#17)* Fix of formula to calculate the z-coordinate of plane at x,y coordinates.

### Lint

- *(#15)* Exclude numpy missing imports from mypy.
- *(#13)* Fix lint to ignore the missing imports from the package skspatial.
- *(#11)* Fix linting in bounding_box_3d.

## [0.1.0] - 2023-11-09

### Update

- *(#9)* Update image in Plaxis3D_input_controller notebook.

### Bug Fixes

- *(#1)* Fix issue with tests not using any module from plxcontroller.

### Features

- *(#1)* Add files according to version 0.1.0.

<!-- CEMS BV. -->
