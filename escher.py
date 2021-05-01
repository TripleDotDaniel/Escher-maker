# pip3 install attrs
import json

import cattr
import numpy as np
import pygame
from pygame import gfxdraw
from pygame.locals import (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_a, K_z, K_x, K_c, K_v, K_o, K_p, K_s, K_l, K_q, K_w,
                           K_ESCAPE, K_TAB, KEYDOWN, K_LEFTBRACKET, K_RIGHTBRACKET,
                           MOUSEBUTTONDOWN, MOUSEBUTTONUP, QUIT)

from escher_class import Pattern, move_points, get_all_patterns


class EncodeFromNumpy(json.JSONEncoder):
    """
    - Serializes python/Numpy objects via customizing json encoder.
    - **Usage**
        - `json.dumps(python_dict, cls=EncodeFromNumpy)` to get json string.
        - `json.dump(*args, cls=EncodeFromNumpy)` to create a file.json.
    """

    def default(self, obj):
        import numpy
        if isinstance(obj, numpy.ndarray):
            return {
                "_kind_": "ndarray",
                "_value_": obj.tolist()
            }
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, range):
            value = list(obj)
            return {
                "_kind_": "range",
                "_value_": [value[0], value[-1] + 1]
            }
        return super(EncodeFromNumpy, self).default(obj)


class DecodeToNumpy(json.JSONDecoder):
    """
    - Deserilizes JSON object to Python/Numpy's objects.
    - **Usage**
        - `json.loads(json_string,cls=DecodeToNumpy)` from string, use `json.load()` for file.
    """

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        import numpy
        if '_kind_' not in obj:
            return obj
        kind = obj['_kind_']
        if kind == 'ndarray':
            return numpy.array(obj['_value_'])
        elif kind == 'range':
            value = obj['_value_']
            return range(value[0], value[-1])
        return obj


def pygame_draw_pattern(screen, pattern, draw_settings):
    tile_shapes = []
    shape_points = pattern.shape.get_coordinates(smoothed_curves=draw_settings['smoothed_curves'])
    for tile in pattern.tiles:
        if tile.mirror > 0:
            color = draw_settings['tile_color'].copy()
        else:
            color = draw_settings['tile_flipped_color'].copy()
        color *= (tile.rot + 1) / (2 * np.pi + 1)
        shape_points_moved = tile.move_coordinates(shape_points)
        shape_points_moved = pattern_pos_to_screen_pos(shape_points_moved, draw_settings)
        tile_shapes.append((shape_points_moved, color))

    for tile_shape in tile_shapes:
        # Draw an anti-aliased and filled polygon.
        # Is the gfxdraw alternative of pygame.draw.polygon(screen, color, shape_points_moved)
        pygame.gfxdraw.aapolygon(screen, tile_shape[0], tile_shape[1].tolist())
        pygame.gfxdraw.filled_polygon(screen, tile_shape[0], tile_shape[1].tolist())

    if draw_settings['borders']:
        for tile_shape in tile_shapes:
            pygame.gfxdraw.aapolygon(screen, tile_shape[0], (255, 255, 255))


def draw_circle(screen, color, pos, size, filled=True):
    # Is the gfxdraw alternative of pygame.draw.circle(screen, color, pos, size)
    pygame.gfxdraw.aacircle(screen, int(pos[0]), int(pos[1]), size, color)
    if filled:
        pygame.gfxdraw.filled_circle(screen, int(pos[0]), int(pos[1]), size, color)


def spherical_transform(pos):
    circle_radius = 3
    c = circle_radius / (circle_radius - 1)
    norm = np.linalg.norm(pos, axis=1)
    sel = norm > 0
    scaling = circle_radius * (1 - np.power(c, -norm[sel])) / norm[sel]
    pos[sel] = (pos[sel].T * scaling.T).T

    return pos


def pattern_pos_to_screen_pos(pos, draw_settings):
    single_dim = pos.ndim == 1
    if single_dim:
        pos = np.array([pos])

    pos_moved = pos.copy()
    if draw_settings['spherical']:
        pos_moved = spherical_transform(pos_moved)

    pos_moved = move_points(pos_moved, [['scale', [draw_settings['shape_radius'], -draw_settings['shape_radius']]],
                                        ['translate', [draw_settings['screen_size'][0] // 2,
                                                       draw_settings['screen_size'][1] // 2]],  # center on screen
                                        ])
    if single_dim:
        pos_moved = pos_moved[0]
    return pos_moved


def screen_pos_to_pattern_pos(pos, draw_settings):
    return move_points(pos, [['translate', np.array([-draw_settings['screen_size'][0] // 2,
                                                     -draw_settings['screen_size'][1] // 2], dtype=np.float32)],
                             ['scale', np.array([1 / draw_settings['shape_radius'],
                                                 -1 / draw_settings['shape_radius']], dtype=np.float32)]
                             ])


def main():
    # settings
    draw_settings = {
        'shape_radius': 100,
        'screen_size': [750, 750],
        'smoothed_curves': True,
        'borders': True,
        'show_controls': True,
        'spherical': True,
        'tile_color': np.array([0, 0, 255.0]),
        'tile_flipped_color': np.array([0, 255.0, 0]),
    }

    # create list with all patterns
    max_distance = np.ceil(np.max(draw_settings['screen_size']) / draw_settings['shape_radius']) * 1.5
    all_patterns = []
    for nr_sides in [3, 4, 6]:
        all_patterns.append(get_all_patterns(nr_sides, max_distance=max_distance))

    # create shape for first pattern
    nr_sides_index = 1
    pattern_index = 0
    pattern = all_patterns[nr_sides_index][pattern_index]

    # Select the start node for movement
    selected_node = pattern.shape.get_next_node()

    # Pygame
    pygame.init()
    pygame.display.set_caption("Escher maker")
    screen = pygame.display.set_mode(draw_settings['screen_size'])
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

    # Set the texts
    def draw_text(text, pos, size=14, width=100):
        if not isinstance(text, list):
            text = [text]

        padding = 5
        font = pygame.font.Font(pygame.font.get_default_font(), size)
        pygame.draw.rect(screen, greywhite, (pos[0] - padding,
                                             pos[1] - padding,
                                             width,
                                             len(text) * size + 2 * padding), border_radius=5)

        for i, t in enumerate(text):
            screen.blit(font.render(t, True, brown, greywhite), (pos[0], pos[1] + size * i))

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
                    selected_node = pattern.shape.get_next_node(selected_node)

                if event.key == K_a:
                    pattern.shape.add_node(selected_node)
                    selected_node = pattern.shape.get_next_node(selected_node)

                if event.key == K_z:
                    draw_settings['smoothed_curves'] = not draw_settings['smoothed_curves']

                if event.key == K_x:
                    draw_settings['borders'] = not draw_settings['borders']

                if event.key == K_c:
                    draw_settings['spherical'] = not draw_settings['spherical']

                if event.key == K_v:
                    draw_settings['show_controls'] = not draw_settings['show_controls']

                if event.key == K_q:
                    draw_settings['shape_radius'] *= 1 / 1.1

                if event.key == K_w:
                    draw_settings['shape_radius'] *= 1.1

                if event.key == K_o:
                    pattern_index = (pattern_index - 1) % len(all_patterns[nr_sides_index])

                if event.key == K_p:
                    pattern_index = (pattern_index + 1) % len(all_patterns[nr_sides_index])

                if event.key == K_LEFTBRACKET:
                    nr_sides_index = (nr_sides_index - 1) % len(all_patterns)
                    pattern_index = 0

                if event.key == K_RIGHTBRACKET:
                    nr_sides_index = (nr_sides_index + 1) % len(all_patterns)
                    pattern_index = 0

                if event.key in (K_o, K_p, K_LEFTBRACKET, K_RIGHTBRACKET):
                    pattern = all_patterns[nr_sides_index][pattern_index]
                    selected_node = pattern.shape.get_next_node()

                # Loading and saving
                # Based on:
                # https://cattrs.readthedocs.io/en/latest/readme.html
                # https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/
                # https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable

                if event.key == K_s:
                    print(f"Saving")
                    print(f"{pattern}")
                    with open('save.txt', 'w') as outfile:
                        json.dump(cattr.unstructure(pattern), outfile, cls=EncodeFromNumpy)

                if event.key == K_l:
                    print(f"Loading")
                    with open('save.txt') as json_file:
                        pattern = cattr.structure(json.load(json_file, cls=DecodeToNumpy), Pattern)
                    print(f"{pattern}")

            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for node in pattern.shape.get_movable_nodes():
                    if np.linalg.norm(pattern_pos_to_screen_pos(node.pos, draw_settings) - mouse_pos) < 10:
                        selected_node = node
                        follow_mouse = True

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                follow_mouse = False

            elif event.type == QUIT:
                running = False

        # Continuous key-press
        pressed_keys = pygame.key.get_pressed()
        move_amount = 5 / draw_settings['shape_radius']
        if pressed_keys[K_UP]:
            pattern.shape.move_node(selected_node, movement=[0, move_amount])

        if pressed_keys[K_DOWN]:
            pattern.shape.move_node(selected_node, movement=[0, -move_amount])

        if pressed_keys[K_LEFT]:
            pattern.shape.move_node(selected_node, movement=[-move_amount, 0])

        if pressed_keys[K_RIGHT]:
            pattern.shape.move_node(selected_node, movement=[move_amount, 0])

        if follow_mouse:
            mouse_pos = screen_pos_to_pattern_pos(pygame.mouse.get_pos(), draw_settings)
            pattern.shape.move_node(selected_node, position=mouse_pos)

        screen.fill(white)

        pygame_draw_pattern(screen, pattern, draw_settings)
        draw_circle(screen, red, pattern_pos_to_screen_pos(selected_node.pos, draw_settings), 7)
        for node_to_draw in pattern.shape.get_nodes():
            if node_to_draw.movable:
                color = greywhite
            else:
                color = greybrown
            draw_circle(screen, color, pattern_pos_to_screen_pos(node_to_draw.pos, draw_settings), 5)

        for linked_node in pattern.shape.get_linked_nodes(selected_node):
            draw_circle(screen, greywhite, pattern_pos_to_screen_pos(linked_node.pos, draw_settings), 7)

        if draw_settings['show_controls']:
            draw_text("ESCHER MAKER", (20, 20), size=20, width=180)

            draw_text(["Controls:",
                       "- Tab key: select node",
                       "- Arrow key: move node",
                       "- A-key: add node",
                       "- Z-key: straight/smooth curves",
                       "- X-key: border on/off",
                       "- C-key: flat/spherical",
                       "- V-key: show/hide control",
                       "- Q/W-keys: zoom in/out",
                       "- O/P-keys: change pattern",
                       "- S/L-key: save & load (WIP)",
                       "- []-keys: change number of sides"],
                      (20, 60), width=300)
            draw_text([f"Info:",
                       f"Pattern {pattern_index + 1} of {len(all_patterns[nr_sides_index])}",
                       f"Combination: {pattern.combination}"],
                      (screen.get_width() - 250, 40), width=240)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
