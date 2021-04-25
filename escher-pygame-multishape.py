# pip3 install attrs
import copy
import attr
import pprint
import pygame
import numpy as np
from pygame.locals import (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_a, K_z, K_ESCAPE, K_TAB, KEYDOWN,
                           MOUSEBUTTONDOWN, MOUSEBUTTONUP, QUIT)
from escher_generate_pattern import find_all_combinations, make_pattern
from scipy.interpolate import interp1d
from pygame import gfxdraw


# Classes (frozen means immutable objects)
# See attrs docs: https://www.attrs.org

@attr.s(eq=False)
class Node(object):
    pos = attr.ib(default=np.array([0, 0]))
    movable = attr.ib(default=True)

    def move(self, movement, position):
        if position is not None:
            self.pos = position
        if movement is not None:
            self.pos += movement

    def __eq__(self, other):
        return id(self) == id(other)


@attr.s()
class Segment(object):
    nodes = attr.ib()
    index_side = attr.ib()
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
    smoothed_curves = attr.ib(default=False)

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

    def get_coordinates(self):
        if self.smoothed_curves:
            return self.get_smooth_coordinates()

        return np.array([node.pos for node in self.get_nodes()])

    def get_smooth_coordinates(self):
        smooth_coordinates = []
        for index_side in range(int(len(self.segments) / 2)):
            nodes0 = self.segments[2 * index_side].nodes
            nodes1 = self.segments[2 * index_side + 1].nodes
            nodes_side = nodes0 + nodes1[1:]
            print()
            smooth_coordinates.append(smooth_curve(np.array([node.pos for node in nodes_side])))
        return np.concatenate(smooth_coordinates)

    def print_coordinates(self):
        pprint.pp(self.get_coordinates())

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


def rotation_matrix(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((c, s), (-s, c)))


def create_polygon(combination=None, size=1, nodes_per_segment=3, smoothed_curves=False):
    if combination is None:
        combination = [2, 3, 0, 1]
    nr_sides = len(combination)
    segment_per_side = 2
    nodes_per_side = (nodes_per_segment - 1) * segment_per_side  # minus 1 because of the overlapping node per segment

    # create nodes
    left_corner_pos = np.array([-np.tan(np.pi / nr_sides) * size / 2, size / 2])
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
                                    dist_for_center=size / 2,
                                    index_side=index_side))

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

    return Shape(segments=segments, links=links, smoothed_curves=smoothed_curves)


def move_points(points, actions):
    points = copy.deepcopy(points)
    for action in actions:
        if action[0] == 'translate':
            points += action[1]
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


def pygame_draw_pattern(screen, pattern, shape, tile_color=np.array([0, 0, 256.0]),
                        tile_flipped_color=np.array([0, 256.0, 0])):
    shape_points = shape.get_coordinates()
    for tile in pattern['tiles']:
        if tile["mirror"] > 0:
            color = tile_color.copy()
        else:
            color = tile_flipped_color.copy()
        color *= (tile["rotation"] + 1) / (2 * np.pi + 1)
        shape_points_moved = move_points(shape_points, [['scale', [tile["mirror"], 1]],
                                                        ['rotate', tile["rotation"]],
                                                        ['translate', tile["pos"]],
                                                        ['scale', [1, -1]],  # because y is down on screen
                                                        ['translate', [screen.get_width() // 2,
                                                                       screen.get_height() // 2]],  # center on screen
                                                        ])

        # Draw an anti-aliased and filled polygon.
        # Is the gfxdraw alternative of pygame.draw.polygon(screen, color, shape_points_moved)
        pygame.gfxdraw.aapolygon(screen, shape_points_moved, color.tolist())
        pygame.gfxdraw.filled_polygon(screen, shape_points_moved, color.tolist())


def draw_circle(screen, color, pos, size, filled=True):
    # Is the gfxdraw alternative of pygame.draw.circle(screen, color, pos, size)
    pygame.gfxdraw.aacircle(screen, int(pos[0]), int(pos[1]), size, color)
    if filled:
        pygame.gfxdraw.filled_circle(screen, int(pos[0]), int(pos[1]), size, color)


def main():
    # Settings
    # combination = [1, 0, 2]
    combination = [0, -3, -2]
    # combination = [2, 1, 0, 3]
    # combination = [0, 1, -4, -3]
    # combination = [5, 2, 1, 4, 3, 0]
    # combination = [-4, 1, -5, -1, -3, 5]
    size_shape = 100
    nr_of_tiles = 25
    smoothed_curves = True

    # Create pattern and shape
    pattern = make_pattern(combination, size=size_shape, nr_of_tiles=nr_of_tiles)
    shape = create_polygon(combination=combination, size=size_shape, smoothed_curves=smoothed_curves)

    # Pygame
    pygame.init()
    pygame.display.set_caption("Escher maker")
    screen = pygame.display.set_mode([750, 750])
    clock = pygame.time.Clock()

    # Set colors
    # black = (0, 0, 0)
    white = (255, 255, 255)
    red = (255, 25, 55)
    # darkred = (255, 200, 200)
    # lightgreenblue = (182, 220, 233)
    # darkgreenblue = (48, 124, 145)
    greybrown = (139, 146, 154)
    greywhite = (229, 227, 228)
    brown = (123, 92, 82)

    # Set origin (0, 0) in the center of the screen instead of top-left and flip direction of y-axis
    def center_pos_to_screen_pos(pos):
        return pos[0] + screen.get_width() // 2, - pos[1] + screen.get_height() // 2

    def screen_pos_to_center_pos(pos):
        return np.array([pos[0] - screen.get_width() // 2, -pos[1] + screen.get_height() // 2])

    # Select the start node for movement
    selected_node = shape.get_next_node()

    # Set the texts
    def draw_text(text, pos, size=14):
        if isinstance(text, list):
            for i, t in enumerate(text):
                draw_text(t, (pos[0], pos[1] + size * i), size)
            return

        font = pygame.font.Font(pygame.font.get_default_font(), size)
        screen.blit(font.render(text, True, brown, greywhite), pos)

    # Start loop
    running = True
    follow_mouse = False
    while running:
        # Single key-press
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

                if event.key == K_TAB:
                    selected_node = shape.get_next_node(selected_node)

                if event.key == K_a:
                    shape.add_node(selected_node)
                    selected_node = shape.get_next_node(selected_node)

                if event.key == K_z:
                    shape.smoothed_curves = not shape.smoothed_curves

            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = screen_pos_to_center_pos(pygame.mouse.get_pos())
                for node in shape.get_movable_nodes():
                    if np.linalg.norm(node.pos - mouse_pos) < 10:
                        selected_node = node
                        follow_mouse = True

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                follow_mouse = False

            elif event.type == QUIT:
                running = False

        # Continuous key-press
        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_UP]:
            shape.move_node(selected_node, movement=[0, 5])

        if pressed_keys[K_DOWN]:
            shape.move_node(selected_node, movement=[0, -5])

        if pressed_keys[K_LEFT]:
            shape.move_node(selected_node, movement=[-5, 0])

        if pressed_keys[K_RIGHT]:
            shape.move_node(selected_node, movement=[5, 0])

        if follow_mouse:
            mouse_pos = screen_pos_to_center_pos(pygame.mouse.get_pos())
            shape.move_node(selected_node, position=mouse_pos)

        screen.fill(white)

        pygame_draw_pattern(screen, pattern, shape)
        for node_to_draw in shape.get_nodes():
            if node_to_draw.movable:
                color = greywhite
            else:
                color = greybrown
            draw_circle(screen, color, center_pos_to_screen_pos(node_to_draw.pos), 5)
        draw_circle(screen, red, center_pos_to_screen_pos(selected_node.pos), 7)
        for linked_node in shape.get_linked_nodes(selected_node):
            draw_circle(screen, greywhite, center_pos_to_screen_pos(linked_node.pos), 7)

        draw_text("ESCHER MAKER", (10, 10), size=20)
        draw_text(["Controls:",
                   "- Select node with tab.",
                   "- Move node with arrows.",
                   "- Add node with a.",
                   "- Switch straight/smooth curves with z."],
                  (10, 40))

        pygame.display.update()

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
