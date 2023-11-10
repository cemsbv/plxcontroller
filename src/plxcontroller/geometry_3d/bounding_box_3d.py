from __future__ import annotations

from plxcontroller.geometry_3d.point_3d import Point3D


class BoundingBox3D:
    """
    A class with information about a bounding box in the 3D space.
    """

    def __init__(
        self,
        x_min: float,
        y_min: float,
        z_min: float,
        x_max: float,
        y_max: float,
        z_max: float,
    ) -> None:
        """Initializes a BoundingBox3D instance.

        Parameters
        ----------
        x_min : float
            the minimum value of the bounding box in the x direction.
        y_min : float
            the minimum value of the bounding box in the y direction.
        z_min : float
            the minimum value of the bounding box in the z direction.
        x_max : float
            the maximum value of the bounding box in the x direction.
        y_max : float
            the maximum value of the bounding box in the y direction.
        z_max : float
            the maximum value of the bounding box in the z direction.

        Raises
        ------
        TypeError
            if any parameter is not of the expected type.
        ValueError
            if x_max is not >= x_min
            if y_max is not >= y_max
            if z_max is not >= z_min
        """
        # Validate types
        if not isinstance(x_min, (float, int)):
            raise TypeError(
                f"Unexpected type found for x_min. Expected float, but got {type(x_min)}"
            )
        if not isinstance(y_min, (float, int)):
            raise TypeError(
                f"Unexpected type found for y_min. Expected float, but got {type(y_min)}"
            )
        if not isinstance(z_min, (float, int)):
            raise TypeError(
                f"Unexpected type found for z_min. Expected float, but got {type(z_min)}"
            )

        if not isinstance(x_max, (float, int)):
            raise TypeError(
                f"Unexpected type found for x_max. Expected float, but got {type(x_max)}"
            )
        if not isinstance(y_max, (float, int)):
            raise TypeError(
                f"Unexpected type found for y_max. Expected float, but got {type(y_max)}"
            )
        if not isinstance(z_max, (float, int)):
            raise TypeError(
                f"Unexpected type found for z_max. Expected float, but got {type(z_max)}"
            )

        # Validate values
        if not x_max >= x_min:
            raise ValueError("x_max must be >= x_min")

        if not y_max >= y_min:
            raise ValueError("y_max must be >= y_min")

        if not z_max >= z_min:
            raise ValueError("z_max must be >= z_min")

        self._x_min = x_min
        self._y_min = y_min
        self._z_min = z_min

        self._x_max = x_max
        self._y_max = y_max
        self._z_max = z_max

    @property
    def x_min(self) -> float:
        """Returns the x_min of the bounding box."""
        return self._x_min

    @property
    def y_min(self) -> float:
        """Returns the y_min of the bounding box."""
        return self._y_min

    @property
    def z_min(self) -> float:
        """Returns the z_min of the bounding box."""
        return self._z_min

    @property
    def x_max(self) -> float:
        """Returns the x_max the bounding box."""
        return self._x_max

    @property
    def y_max(self) -> float:
        """Returns the y_max of the bounding box."""
        return self._y_max

    @property
    def z_max(self) -> float:
        """Returns the z_max of the bounding box."""
        return self._z_max

    @property
    def centroid(self) -> Point3D:
        """Returns the centroid of the bounding box."""
        return Point3D(
            x=0.5 * (self.x_min + self.x_max),
            y=0.5 * (self.y_min + self.y_max),
            z=0.5 * (self.z_min + self.z_max),
        )
