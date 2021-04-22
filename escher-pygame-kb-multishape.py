# pip3 install attrs
import copy
import attr
import pprint
import pygame
import time
import numpy as np
from pygame.locals import (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_a, K_ESCAPE, K_TAB, KEYDOWN, QUIT)
from escher_generate_pattern import find_all_combinations, make_pattern, draw_pattern, move_shape


# Classes (frozen means immutable objects)
# See attrs docs: https://www.attrs.org

@attr.s(eq=False)
class Node(object):
    pos = attr.ib(default=np.array([0, 0]))
    movable = attr.ib(default=True)

    def move(self, movement):
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

    def add_node(self, segment_id, node_id, node: Node):
        self.segments[segment_id].nodes.insert(node_id, node)

    def get_coordinates(self):
        coordinates = np.array([node.pos for node in self.get_nodes()])
        return coordinates

    def get_nodes(self):
        # exclude every last node in segment to prevent overlap
        return [node
                for segment in self.segments
                for node in segment.nodes[:-1]]

    def print_coordinates(self):
        print([id(node) for node in self.get_nodes()])
        pprint.pp(self.get_coordinates())

    def move_node(self, node, movement):
        if node.movable:
            node.move(movement)
            for link in self.links:
                if node in link.segment_source.nodes:
                    link.update_linked_segment(self)

    def get_next_node(self, node):
        nodes = self.get_nodes()
        index = nodes.index(node)
        while True:
            index = (index + 1) % len(nodes)
            if nodes[index].movable:
                break

        return nodes[index]


def rotation_matrix(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((c, s), (-s, c)))


def create_polygon(combination=None, size=1):
    if combination is None:
        combination = [2, 3, 0, 1]
    nr_sides = len(combination)

    # create nodes
    nodes = []
    pos0 = np.array([0, size / 2])
    pos1 = np.array([np.tan(np.pi / nr_sides) * size / 2, size / 2])
    for index_side in range(nr_sides):
        angle = 2 * np.pi / nr_sides * index_side
        nodes.append(Node(pos=rotation_matrix(angle).dot(pos0), movable=True))
        nodes.append(Node(pos=rotation_matrix(angle).dot(pos1), movable=False))

    # create segments
    segments = []
    for index_side in range(nr_sides):
        angle = 2 * np.pi / nr_sides * index_side
        node_m1 = nodes[(2 * index_side - 1) % (2 * nr_sides)]
        node_0 = nodes[2 * index_side]
        node_p1 = nodes[2 * index_side + 1]
        segments.append(Segment(nodes=[node_m1, node_0], angle=angle, dist_for_center=size / 2))
        segments.append(Segment(nodes=[node_0, node_p1], angle=angle, dist_for_center=size / 2))

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
            segments[2 * index_side].nodes[-1].movable = False
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
                              segment_linked=segments[2 * (-combination[index_side] + 1) + 1],
                              flip_x=False,
                              flip_y=True))
            links.append(Link(segment_source=segments[2 * index_side + 1],
                              segment_linked=segments[2 * (-combination[index_side] + 1)],
                              flip_x=False,
                              flip_y=True))

    return Shape(segments=segments, links=links)


def move_points(points, actions):
    for action in actions:
        if action[0] == 'translate':
            points += action[1]
        elif action[0] == 'rotate':
            points = rotation_matrix(action[1]).dot(points.T).T
        elif action[0] == 'scale':
            points *= action[1]
        else:
            raise NotImplementedError(f"Action {action[0]} is not defined")
    return points


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
        pygame.draw.polygon(screen, color, shape_points_moved)


# Settings
combination = [1, 0, 2]
combination = [5, 2, 1, 4, 3, 0]
size_shape = 100

# Create pattern and shape
pattern = make_pattern(combination, size=size_shape)
shape = create_polygon(combination=combination, size=size_shape)

# Pygame
pygame.init()
screen = pygame.display.set_mode([750, 750])
clock = pygame.time.Clock()

# Set colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 25, 55)
lightgreenblue = (182, 220, 233)
darkgreenblue = (48, 124, 145)
greybrown = (139, 146, 154)
greywhite = (229, 227, 228)
brown = (123, 92, 82)
color1 = lightgreenblue
color2 = darkgreenblue

# Set origin (0, 0) in the center of the screen instead of top-left and flip direction of y-axis
center_origin = lambda p, center: (
    center[0] + p[0] + screen.get_width() // 2, center[1] - p[1] + screen.get_height() // 2)
center_origins = lambda l, center: [center_origin(coordinates, center) for coordinates in l]

# Select the start node for movement
selected_node = shape.get_next_node(shape.get_nodes()[0])

# Set the texts
font = pygame.font.Font(pygame.font.get_default_font(), 14)
draw_text = lambda text, pos: screen.blit(font.render(text, True, brown, greywhite), pos)

# Start loop
running = True
while running:
    # Single key-press
    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            if event.key == K_TAB:
                selected_node = shape.get_next_node(selected_node)

            # if event.key == K_a:
            #    shape.add_node(
            #        segment_id=selected_segment_id,
            #        node_id=selected_node_id,
            #        node=Node(selected_node.x, selected_node.y)
            #    )
            #    selected_id += 1

        elif event.type == QUIT:
            running = False

    # Continuous key-press
    pressed_keys = pygame.key.get_pressed()

    if pressed_keys[K_UP]:
        shape.move_node(selected_node, [0, 5])

    if pressed_keys[K_DOWN]:
        shape.move_node(selected_node, [0, -5])

    if pressed_keys[K_LEFT]:
        shape.move_node(selected_node, [-5, 0])

    if pressed_keys[K_RIGHT]:
        shape.move_node(selected_node, [5, 0])

    screen.fill(white)

    pygame_draw_pattern(screen, pattern, shape)
    for node_to_draw in shape.get_nodes():
        if node_to_draw.movable:
            color = greywhite
        else:
            color = greybrown
        pygame.draw.circle(screen, color, center_origin(node_to_draw.pos, (0, 0)), 5)
    pygame.draw.circle(screen, red, center_origin(selected_node.pos, (0, 0)), 7)

    draw_text("ESCHER MAKER", (10, 10))
    draw_text("Select with tab. Move with arrows. Add with a", (10, 30))
    draw_text(f"Position: ({selected_node.pos})", (185, 50))

    pygame.display.update()

    clock.tick(60)

pygame.quit()
