from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sc2.game_state import GameState

from logging import getLogger

logger = getLogger(__name__)

from math import hypot
from numpy import (
    ndarray,
    fromiter,
    float as np_float,
)
from warnings import catch_warnings, simplefilter

with catch_warnings():
    simplefilter("ignore")
    from scipy.spatial.distance import pdist, cdist

from typing import Dict, Tuple, Iterable, Generator


class DistanceCalculation:
    def __init__(self):
        self.state: GameState = None
        self._generated_frame = -100
        self._generated_frame2 = -100
        # A Dictionary with a dict positions: index of the pdist condensed matrix
        self._cached_unit_index_dict: Dict[int, int] = None
        # Pdist condensed vector generated by scipy pdist, half the size of the cdist matrix as 1d array
        self._cached_pdist: ndarray = None
        self._cached_cdist: ndarray = None

    @property
    def _units_count(self) -> int:
        return len(self.all_units)

    @property
    def _unit_index_dict(self) -> Dict[int, int]:
        """ As property, so it will be recalculated each time it is called, or return from cache if it is called multiple times in teh same game_loop. """
        if self._generated_frame != self.state.game_loop:
            return self.generate_unit_indices()
        return self._cached_unit_index_dict

    @property
    def _pdist(self) -> ndarray:
        """ As property, so it will be recalculated each time it is called, or return from cache if it is called multiple times in teh same game_loop. """
        if self._generated_frame2 != self.state.game_loop:
            return self.calculate_distances()
        return self._cached_pdist

    @property
    def _cdist(self) -> ndarray:
        """ As property, so it will be recalculated each time it is called, or return from cache if it is called multiple times in teh same game_loop. """
        if self._generated_frame2 != self.state.game_loop:
            return self.calculate_distances()
        return self._cached_cdist

    def generate_unit_indices(self) -> Dict[int, int]:
        if self._generated_frame != self.state.game_loop:
            self._cached_unit_index_dict = {unit.tag: index for index, unit in enumerate(self.all_units)}
            self._generated_frame = self.state.game_loop
        return self._cached_unit_index_dict

    def _calculate_distances_method1(self) -> ndarray:
        if self._generated_frame2 != self.state.game_loop:
            # Converts tuple [(1, 2), (3, 4)] to flat list like [1, 2, 3, 4]
            flat_positions = (coord for unit in self.all_units for coord in unit.position_tuple)
            # Converts to numpy array, then converts the flat array back to shape (n, 2): [[1, 2], [3, 4]]
            positions_array: ndarray = fromiter(
                flat_positions, dtype=np_float, count=2 * self._units_count
            ).reshape((self._units_count, 2))
            assert len(positions_array) == self._units_count
            self._generated_frame2 = self.state.game_loop
            # See performance benchmarks
            self._cached_pdist = pdist(positions_array, "sqeuclidean")

            # # Distance check of all units
            # for unit1 in self.all_units:
            #     for unit2 in self.all_units:
            #         if unit1.tag == unit2.tag:
            #             # Is zero
            #             continue
            #         try:
            #             index1 = self._unit_index_dict[unit1.tag]
            #             index2 = self._unit_index_dict[unit2.tag]
            #             condensed_index = self.square_to_condensed(index1, index2)
            #             assert condensed_index < len(self._pdist)
            #             pdist_distance = self._pdist[condensed_index]
            #             correct_dist = self._distance_pos_to_pos(unit1.position_tuple, unit2.position_tuple) ** 2
            #             error_margin = 1e-5
            #             assert (abs(pdist_distance - correct_dist) < error_margin), f"Actual distance is {correct_dist} but calculated pdist distance is {pdist_distance}"
            #         except:
            #             print(
            #                 f"Error caused by unit1 {unit1} and unit2 {unit2} with positions {unit1.position_tuple} and {unit2.position_tuple}"
            #             )
            #             raise

        return self._cached_pdist

    def _calculate_distances_method2(self) -> ndarray:
        if self._generated_frame2 != self.state.game_loop:
            # Converts tuple [(1, 2), (3, 4)] to flat list like [1, 2, 3, 4]
            flat_positions = (coord for unit in self.all_units for coord in unit.position_tuple)
            # Converts to numpy array, then converts the flat array back to shape (n, 2): [[1, 2], [3, 4]]
            positions_array: ndarray = fromiter(
                flat_positions, dtype=np_float, count=2 * self._units_count
            ).reshape((self._units_count, 2))
            assert len(positions_array) == self._units_count
            self._generated_frame2 = self.state.game_loop
            # See performance benchmarks
            self._cached_cdist = cdist(positions_array, positions_array, "sqeuclidean")

        return self._cached_cdist

    def _calculate_distances_method3(self) -> ndarray:
        """ Nearly same as above, but without asserts"""
        if self._generated_frame2 != self.state.game_loop:
            flat_positions = (coord for unit in self.all_units for coord in unit.position_tuple)
            positions_array: ndarray = fromiter(
                flat_positions, dtype=np_float, count=2 * self._units_count
            ).reshape((-1, 2))
            self._generated_frame2 = self.state.game_loop
            # See performance benchmarks
            self._cached_cdist = cdist(positions_array, positions_array, "sqeuclidean")

        return self._cached_cdist

    def _get_index_of_two_units_method1(self, unit1: Unit, unit2: Unit) -> int:
        assert (
            unit1.tag in self._unit_index_dict
        ), f"Unit1 {unit1} is not in index dict for distance calculation. Make sure the unit is alive in the current frame. Ideally take units from 'self.units' or 'self.structures' as these contain unit data from the current frame. Do not try to save 'Units' objects over several iterations."
        assert (
            unit2.tag in self._unit_index_dict
        ), f"Unit2 {unit2} is not in index dict for distance calculation. Make sure the unit is alive in the current frame. Ideally take units from 'self.units' or 'self.structures' as these contain unit data from the current frame. Do not try to save 'Units' objects over several iterations."
        # index1 = self._unit_index_dict[unit1.tag]
        # index2 = self._unit_index_dict[unit2.tag]
        return self.square_to_condensed(self._unit_index_dict[unit1.tag], self._unit_index_dict[unit2.tag])

    def _get_index_of_two_units_method2(self, unit1: Unit, unit2: Unit) -> Tuple[int, int]:
        assert (
            unit1.tag in self._unit_index_dict
        ), f"Unit1 {unit1} is not in index dict for distance calculation. Make sure the unit is alive in the current frame. Ideally take units from 'self.units' or 'self.structures' as these contain unit data from the current frame. Do not try to save 'Units' objects over several iterations."
        assert (
            unit2.tag in self._unit_index_dict
        ), f"Unit2 {unit2} is not in index dict for distance calculation. Make sure the unit is alive in the current frame. Ideally take units from 'self.units' or 'self.structures' as these contain unit data from the current frame. Do not try to save 'Units' objects over several iterations."
        return self._unit_index_dict[unit1.tag], self._unit_index_dict[unit2.tag]

    def _get_index_of_two_units_method3(self, unit1: Unit, unit2: Unit) -> Tuple[int, int]:
        """ Same function as above, but without asserts"""
        return self._unit_index_dict[unit1.tag], self._unit_index_dict[unit2.tag]

    # Helper functions

    def square_to_condensed(self, i, j) -> int:
        # Converts indices of a square matrix to condensed matrix
        # https://stackoverflow.com/a/36867493/10882657
        assert i != j, "No diagonal elements in condensed matrix! Diagonal elements are zero"
        if i < j:
            i, j = j, i
        return self._units_count * j - j * (j + 1) // 2 + i - 1 - j

    def convert_tuple_to_numpy_array(self, pos: Tuple[float, float]) -> ndarray:
        """ Converts a single position to a 2d numpy array with 1 row and 2 columns. """
        return fromiter(pos, dtype=float, count=2).reshape((1, 2))

    # Fast and simple calculation functions

    def distance_math_hypot(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        return hypot(p1[0] - p2[0], p1[1] - p2[1])

    def distance_math_hypot_squared(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return dx*dx + dy*dy

    def _distance_squared_unit_to_unit_method0(self, unit1: Unit, unit2: Unit) -> float:
        return self.distance_math_hypot_squared(unit1.position_tuple, unit2.position_tuple)

    # Distance calculation using the pre-calculated matrix above

    def _distance_squared_unit_to_unit_method1(self, unit1: Unit, unit2: Unit) -> float:
        # If checked on units if they have the same tag, return distance 0 as these are not in the 1 dimensional pdist array - would result in an error otherwise
        if unit1.tag == unit2.tag:
            return 0
        # Calculate index, needs to be after pdist has been calculated and cached
        condensed_index = self._get_index_of_two_units(unit1, unit2)
        assert condensed_index < len(
            self._cached_pdist
        ), f"Condensed index is larger than amount of calculated distances: {condensed_index} < {len(self._cached_pdist)}, units that caused the assert error: {unit1} and {unit2}"
        distance = self._pdist[condensed_index]
        return distance

    def _distance_squared_unit_to_unit_method2(self, unit1: Unit, unit2: Unit) -> float:
        # Calculate index, needs to be after cdist has been calculated and cached
        # index1, index2 = self._get_index_of_two_units(unit1, unit2)
        # distance = self._cdist[index1, index2]
        # return distance
        return self._cdist[self._get_index_of_two_units(unit1, unit2)]

    # Distance calculation using the fastest distance calculation functions

    def _distance_pos_to_pos(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        return self.distance_math_hypot(pos1, pos2)

    def _distance_units_to_pos(self, units: Units, pos: Tuple[float, float]) -> Generator[float, None, None]:
        """ This function does not scale well, if len(units) > 100 it gets fairly slow """
        return (self.distance_math_hypot(u.position_tuple, pos) for u in units)

    def _distance_unit_to_points(
        self, unit: Unit, points: Iterable[Tuple[float, float]]
    ) -> Generator[float, None, None]:
        """ This function does not scale well, if len(points) > 100 it gets fairly slow """
        pos = unit.position_tuple
        return (self.distance_math_hypot(p, pos) for p in points)

    def _distances_override_functions(self, method: int = 0):
        """ Overrides the internal distance calculation functions at game start in bot_ai.py self._prepare_start() function
        method 0: Use python's math.hypot
        The following methods calculate the distances between all units once:
        method 1: Use scipy's pdist condensed matrix (1d array)
        method 2: Use scipy's cidst square matrix (2d array)
        method 3: Use scipy's cidst square matrix (2d array) without asserts (careful: very weird error messages, but maybe slightly faster) """
        assert 0 <= method <= 3, f"Selected method was: {method}"
        if method == 0:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method0
        elif method == 1:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method1
            self.calculate_distances = self._calculate_distances_method1
            self._get_index_of_two_units = self._get_index_of_two_units_method1
        elif method == 2:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method2
            self.calculate_distances = self._calculate_distances_method2
            self._get_index_of_two_units = self._get_index_of_two_units_method2
        elif method == 3:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method2
            self.calculate_distances = self._calculate_distances_method3
            self._get_index_of_two_units = self._get_index_of_two_units_method3
