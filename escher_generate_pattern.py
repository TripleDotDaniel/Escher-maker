import math
import numpy as np
import itertools
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon, Polygon


def find_all_combinations(nr_sides, with_mirror=True):
    combinations = find_combinations(nr_sides)
    if with_mirror:
        combinations = add_mirror_combinations(combinations)
    return combinations


def find_combinations(nr_sides, combination=None):
    if combination is None:
        combination = []
    index = len(combination)
    if index == nr_sides:
        return [combination]

    if index in combination:
        combination.append(combination.index(index))
        return find_combinations(nr_sides, combination)

    combinations = []
    for i in (set(range(index, nr_sides)) - set(combination)):
        combination_copy = combination.copy()
        combination_copy.append(i)
        combinations.extend(find_combinations(nr_sides, combination_copy))
    return combinations


def add_mirror_combinations(combinations):
    new_combinations = []
    nr_sides = len(combinations[0])
    for combination in combinations:
        indexes = np.arange(nr_sides)
        indexes_of_pairs = indexes[indexes < combination]
        sets_to_mirror = [com for L in range(len(indexes_of_pairs)) for com in
                          itertools.combinations(indexes_of_pairs, L + 1)]
        for set_to_mirror in sets_to_mirror:
            new_combination = combination.copy()
            for index_pair in set_to_mirror:
                new_combination[combination[index_pair]] = -combination[combination[index_pair]] - 1
                new_combination[index_pair] = -combination[index_pair] - 1
            new_combinations.append(new_combination)
    combinations.extend(new_combinations)
    return combinations


def tile_in_set(tiles, new_tile, eps=1e-5):
    for tile in tiles:
        diff_pos = abs(tile["pos"] - new_tile["pos"])
        diff_rot = abs(tile["rotation"] - new_tile["rotation"])
        if diff_rot > np.pi:
            diff_rot -= 2 * np.pi
        if all(diff_pos < eps):
            return True, diff_rot < eps and tile["mirror"] == new_tile["mirror"]
    return False, False


def index_to_rotation(index, nr_sides):
    return 2 * math.pi / nr_sides * index


def make_pattern(combination, nr_of_tiles=20, size=1):
    nr_sides = len(combination)
    tiles = [{"pos": np.array([0, 0]), "rotation": 0, "mirror": 1}]
    index_tile = 0
    while index_tile < nr_of_tiles:
        tile = tiles[index_tile]
        for index_side in range(nr_sides):
            direction = tile["rotation"] + index_to_rotation(index_side, nr_sides) * tile["mirror"]
            if combination[index_side] >= 0:
                side_match = combination[index_side]
                mirror = tile["mirror"]
            else:
                side_match = -combination[index_side] - 1
                mirror = -tile["mirror"]

            new_tile = {"pos": tile["pos"] + size * np.array([math.sin(direction), math.cos(direction)]),
                        "rotation": (direction - index_to_rotation(side_match, nr_sides) * mirror + np.pi) % (2 * np.pi),
                        "mirror": mirror}
            inset = tile_in_set(tiles, new_tile)
            if not inset[0]:
                tiles.append(new_tile)
            elif not inset[1]:
                return None
        index_tile += 1
    return {"combination": combination, "tiles": tiles, "size": size}


def draw_pattern(pattern):
    nr_sides = len(pattern["combination"])
    fig, ax = plt.subplots(1)
    ax.set_aspect('equal')

    radius = 0.5 / math.cos(math.pi / nr_sides) * pattern['size']
    for tile in pattern["tiles"]:
        if tile["mirror"] > 0:
            color = np.array([1.0, 0, 0])
        else:
            color = np.array([0, 1.0, 0])
        color *= (tile["rotation"] + 1) / (2*np.pi + 1)
        polygon = RegularPolygon(tile["pos"],
                                 numVertices=nr_sides,
                                 orientation=np.pi / nr_sides + tile["rotation"],
                                 facecolor=color, radius=radius)
        ax.add_patch(polygon)
    plt.autoscale(enable=True)
    plt.title(pattern["combination"])
    plt.show()


def move_shape(shape, translation=None, rotation=0.0, scale=None):
    if scale is None:
        scale = [1, 1]
    if translation is None:
        translation = [0, 0]
    return np.array([[math.cos(rotation), math.sin(rotation)],
                     [-math.sin(rotation), math.cos(rotation)]]).dot(
        [shape[0] * scale[0] + translation[0],
         shape[1] * scale[1] + translation[1]])


def create_shape(combination, edge_shapes, edge_height=0.5):
    nr_sides = len(combination)
    side_length = math.tan(math.pi / nr_sides)

    shape = None
    for i in range(len(combination)):
        if i == combination[i]:
            edge_shape_index = i
            edge_dir = [1, -1]
        elif i < combination[i] or -i > combination[i]:
            edge_shape_index = i
            edge_dir = [1, 0]
        elif combination[i] >= 0:
            edge_shape_index = combination[i]
            edge_dir = [0, -1]
        else:
            edge_shape_index = -combination[i] - 1
            edge_dir = [-1, 0]

        trans = [0, 0.5]
        rot = 2 * math.pi / nr_sides * i
        scale = np.array([side_length / 2, edge_height])

        shape_left = edge_shapes[edge_shape_index]
        shape_right = edge_shapes[edge_shape_index]
        shape_left = move_shape(shape_left, trans, rot, scale * [-1, edge_dir[0]])[:, ::-1]
        shape_right = move_shape(shape_right, trans, rot, scale * [1, edge_dir[1]])
        if shape is not None:
            shape = np.append(shape, shape_left, axis=1)
        else:
            shape = shape_left
        shape = np.append(shape, shape_right, axis=1)
    return shape


def plot_pattern(pattern, tile_color=np.array([1.0, 0, 0]), tile_flipped_color=np.array([0, 1.0, 0])):
    nr_sides = len(pattern["combination"])

    fig, ax = plt.subplots(1, figsize=(10, 10))
    ax.set_aspect("equal")
    for tile in pattern["tiles"]:
        if tile["mirror"] > 0:
            color = tile_color.copy()
        else:
            color = tile_flipped_color.copy()
        color *= (tile["rotation"] + 1) / (2 * np.pi + 1)
        moved_shape = move_shape(pattern["shape"], rotation=tile["rotation"],
                                 scale=[tile["mirror"], 1])
        moved_shape = move_shape(moved_shape, translation=tile["pos"])
        pol = Polygon(moved_shape.T, facecolor=color, edgecolor="k")
        ax.add_patch(pol)
    ax.autoscale(enable=True)
    ax.set_title(pattern['combination'])
    ax.set_axis_off()
    fig.show()
    return fig, ax
