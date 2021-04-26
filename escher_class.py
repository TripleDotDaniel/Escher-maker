import copy
import itertools

import attr
import numpy as np
from scipy.interpolate import interp1d


@attr.s(eq=False)
class Node(object):
    pos = attr.ib(default=np.array([0, 0]))
    movable = attr.ib(default=True)

    def move(self, movement=None, position=None):
        if position is not None:
            self.pos = position
        if movement is not None:
            self.pos += movement

    def __eq__(self, other):
        return id(self) == id(other)


@attr.s()
class Segment(object):
    nodes = attr.ib()
    angle = attr.ib(default=0)
    dist_for_center = attr.ib(default=1)


@attr.s()
class Link(object):
    segment_source = attr.ib(validator=attr.validators.instance_of(Segment))
    segment_linked = attr.ib(validator=attr.validators.instance_of(Segment))
    flip_x = attr.ib(default=False)
    flip_y = attr.ib(default=False)

    def update_linked_segment(self, shape):
        self.segment_linked.nodes = copy.deepcopy(self.segment_source.nodes)
        for node in self.segment_linked.nodes:
            # first rotate back such that the segment is horizontal, do flips, rotate to new angle
            node.pos = rotation_matrix(-self.segment_source.angle).dot(node.pos)
            node.pos += [0, -self.segment_source.dist_for_center]
            if self.flip_x:
                node.pos = node.pos * [-1, 1]
            if self.flip_y:
                node.pos = node.pos * [1, -1]
            node.pos += [0, self.segment_linked.dist_for_center]
            node.pos = rotation_matrix(self.segment_linked.angle).dot(node.pos)

        if self.flip_x:
            self.segment_linked.nodes.reverse()

        # update shared notes in neighboring segments
        index_segment_linked = shape.segments.index(self.segment_linked)
        shape.segments[(index_segment_linked - 1) % len(shape.segments)].nodes[-1] = self.segment_linked.nodes[0]
        shape.segments[(index_segment_linked + 1) % len(shape.segments)].nodes[0] = self.segment_linked.nodes[-1]


@attr.s()
class Shape(object):
    segments = attr.ib()
    links = attr.ib()

    def __str__(self):
        output = ""
        for i, segment in enumerate(self.segments):
            output += f"Segment {i}: {segment}\n"
        for i, link in enumerate(self.links):
            output += f"Link {i}: {link}\n"
        return output

    def get_nodes(self):
        # exclude every last node in segment to prevent overlap
        return [node
                for segment in self.segments
                for node in segment.nodes[:-1]]

    def get_movable_nodes(self):
        return [node for node in self.get_nodes() if node.movable]

    def get_coordinates(self, smoothed_curves):
        if smoothed_curves:
            return self.get_smooth_coordinates()

        return np.array([node.pos for node in self.get_nodes()])

    def get_smooth_coordinates(self):
        smooth_coordinates = []
        for index_side in range(int(len(self.segments) / 2)):
            nodes0 = self.segments[2 * index_side].nodes
            nodes1 = self.segments[2 * index_side + 1].nodes
            nodes_side = nodes0 + nodes1[1:]
            smooth_coordinates.append(smooth_curve(np.array([node.pos for node in nodes_side])))
        return np.concatenate(smooth_coordinates)

    def move_node(self, node, movement=None, position=None):
        if node.movable:
            node.move(movement, position)

            # update linked segment(s)
            for link in self.links:
                if node in link.segment_source.nodes:
                    link.update_linked_segment(self)

    def add_node(self, node):
        # add node
        for segment in self.segments:
            if node in segment.nodes:
                node_index = segment.nodes.index(node)
                if node_index < len(
                        segment.nodes) - 1:  # don't match last node because it overlaps with the next segment
                    new_node = copy.deepcopy(node)
                    # place new node in between current and next node
                    new_node.pos = (segment.nodes[node_index].pos + segment.nodes[node_index + 1].pos) / 2
                    segment.nodes.insert(node_index + 1, new_node)
                    break

        # update linked segment(s)
        for link in self.links:
            if node in link.segment_source.nodes:
                link.update_linked_segment(self)

    def get_next_node(self, node=None):
        movable_nodes = [node for node in self.get_nodes() if node.movable]
        if len(movable_nodes) == 0:
            raise RuntimeError("No movable nodes")

        if node in movable_nodes:
            return movable_nodes[(movable_nodes.index(node) + 1) % len(movable_nodes)]
        else:
            return movable_nodes[0]

    def get_linked_nodes(self, node):
        linked_nodes = []
        for link in self.links:
            if node in link.segment_source.nodes:
                node_index = link.segment_source.nodes.index(node)
                if link.flip_x:
                    node_index = len(link.segment_source.nodes) - 1 - node_index
                linked_nodes.append(link.segment_linked.nodes[node_index])
        return linked_nodes


@attr.s()
class Tile(object):
    pos = attr.ib(default=np.array([0, 0]))
    rot = attr.ib(default=0)
    mirror = attr.ib(default=1)

    def move_coordinates(self, coordinates):
        return move_points(coordinates,
                           [['scale', [self.mirror, 1]],
                            ['rotate', self.rot],
                            ['translate', self.pos]])


@attr.s(eq=False)
class Pattern(object):
    tiles = attr.ib()
    combination = attr.ib()
    shape = attr.ib()

    def __eq__(self, other):
        return id(self) == id(other)


def create_shape(combination=None, radius=1, nodes_per_segment=3):
    if combination is None:
        combination = [2, 3, 0, 1]
    nr_sides = len(combination)
    height = radius * np.cos(np.pi / nr_sides)
    segment_per_side = 2
    nodes_per_side = (nodes_per_segment - 1) * segment_per_side  # minus 1 because of the overlapping node per segment

    # create nodes
    left_corner_pos = np.array([-np.tan(np.pi / nr_sides) * height / 2, height / 2])
    right_corner_pos = left_corner_pos * [-1, 1]
    # right corner is an overlapping node, added for correct spacing and then removed
    nodes_pos = np.linspace(left_corner_pos, right_corner_pos, nodes_per_side + 1)[:-1]
    nodes = []
    for index_side in range(nr_sides):
        angle = 2 * np.pi / nr_sides * index_side
        for i, node_pos in enumerate(nodes_pos):
            nodes.append(Node(pos=rotation_matrix(angle).dot(node_pos), movable=(i != 0)))

    # create segments
    segments = []
    for index_side in range(nr_sides):
        angle = 2 * np.pi / nr_sides * index_side
        for s in range(segment_per_side):
            index_segment = index_side * segment_per_side + s
            index_nodes = [(index_segment * (nodes_per_segment - 1) + i) % len(nodes) for i in range(nodes_per_segment)]
            segments.append(Segment(nodes=[nodes[i] for i in index_nodes],
                                    angle=angle,
                                    dist_for_center=height / 2))

    # create links
    links = []
    for index_side in range(nr_sides):
        if index_side == combination[index_side]:  # side linked to itself
            links.append(Link(segment_source=segments[2 * index_side],
                              segment_linked=segments[2 * index_side + 1],
                              flip_x=True,
                              flip_y=True))
            links.append(Link(segment_source=segments[2 * index_side + 1],
                              segment_linked=segments[2 * index_side],
                              flip_x=True,
                              flip_y=True))
            segments[2 * index_side + 1].nodes[0].movable = False
        elif combination[index_side] >= 0:  # side linked to other side of shape
            links.append(Link(segment_source=segments[2 * index_side],
                              segment_linked=segments[2 * combination[index_side] + 1],
                              flip_x=True,
                              flip_y=True))
            links.append(Link(segment_source=segments[2 * index_side + 1],
                              segment_linked=segments[2 * combination[index_side]],
                              flip_x=True,
                              flip_y=True))
        else:  # side linked to other side of flipped shape
            links.append(Link(segment_source=segments[2 * index_side],
                              segment_linked=segments[2 * (-combination[index_side] - 1)],
                              flip_x=False,
                              flip_y=True))
            links.append(Link(segment_source=segments[2 * index_side + 1],
                              segment_linked=segments[2 * (-combination[index_side] - 1) + 1],
                              flip_x=False,
                              flip_y=True))

    return Shape(segments=segments, links=links)


def move_points(points, actions):
    points = copy.deepcopy(points)
    for action in actions:
        if action[0] == 'translate':
            points += np.array(action[1])
        elif action[0] == 'rotate':
            points = rotation_matrix(action[1]).dot(points.T).T
        elif action[0] == 'scale':
            points *= action[1]
        elif action[0] == 'smooth':
            points = smooth_curve(points, nr_of_subdivisions=action[1])
        else:
            raise NotImplementedError(f"Action {action[0]} is not defined")
    return points


def smooth_curve(points, nr_of_subdivisions=5, close_loop=False):
    # based on https://stackoverflow.com/a/27650158
    nr_of_points = len(points)
    if close_loop:
        x = np.concatenate([points[-3:-1, :], points, points[1:3, :]])
        ti = np.linspace(2, nr_of_points + 1, nr_of_subdivisions * nr_of_points)
    else:
        x = points
        ti = np.linspace(0, nr_of_points - 1, nr_of_subdivisions * nr_of_points)

    t = np.arange(len(x))
    xi = interp1d(t, x, axis=0, kind='cubic', fill_value='extrapolate')(ti)
    return np.array(xi)


def rotation_matrix(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((c, s), (-s, c)))


def get_all_patterns(nr_sides, with_mirror=True, radius=1, max_distance=3.5):
    combinations = find_combinations(nr_sides)
    if with_mirror:
        combinations = add_mirror_combinations(combinations)

    patterns = []
    for combination in combinations:
        pattern = make_pattern(combination, radius=radius, max_distance=max_distance, error_if_not_valid=False)
        if pattern:
            patterns.append(pattern)
    return patterns


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
        diff_pos = abs(tile.pos - new_tile.pos)
        diff_rot = abs(tile.rot - new_tile.rot)
        if diff_rot > np.pi:
            diff_rot -= 2 * np.pi
        if all(diff_pos < eps):
            return True, diff_rot < eps and tile.mirror == new_tile.mirror
    return False, False


def index_to_rotation(index, nr_sides):
    return 2 * np.pi / nr_sides * index


def make_pattern(combination, radius=1, error_if_not_valid=True, max_distance=4.5):
    nr_sides = len(combination)
    shape = create_shape(combination=combination, radius=radius)
    tiles = [Tile()]
    index_tile = 0
    height = radius * np.cos(np.pi / nr_sides)
    while index_tile < len(tiles):
        tile = tiles[index_tile]
        for index_side in range(nr_sides):
            direction = tile.rot + index_to_rotation(index_side, nr_sides) * tile.mirror
            if combination[index_side] >= 0:
                side_match = combination[index_side]
                mirror = tile.mirror
            else:
                side_match = -combination[index_side] - 1
                mirror = -tile.mirror

            new_tile = Tile(pos=tile.pos + height * np.array([np.sin(direction), np.cos(direction)]),
                            rot=(direction - index_to_rotation(side_match, nr_sides) * mirror + np.pi) % (2 * np.pi),
                            mirror=mirror)
            inset = tile_in_set(tiles, new_tile)
            if np.linalg.norm(new_tile.pos) < max_distance * height:
                if not inset[0]:
                    tiles.append(new_tile)
                elif not inset[1]:
                    if error_if_not_valid:
                        raise RuntimeError(f"Combination {combination} does not result in a valid pattern")
                    return None
        index_tile += 1

    return Pattern(tiles=tiles, combination=combination, shape=shape)
