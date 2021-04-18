# pip3 install attrs
import attr
import pprint
import pygame
import time

# Classes (frozen means immutable objects)
# See attrs docs: https://www.attrs.org
@attr.s(frozen=True)
class Node(object):
	x = attr.ib()
	y = attr.ib()

@attr.s(frozen=True)
class Segment(object):
	nodes = attr.ib()
	trans = attr.ib()

@attr.s(frozen=True)
class Shape(object):
	segments = attr.ib()


# Functions
def shape_combined_segments(shape: Shape):
	segments = shape.segments

	transposed_segments = []
	for segment in segments:
		transposed_segments.append(transpose_segment(segment))

	return segments + transposed_segments

def transpose_segment(segment: Segment):
	if segment.trans == 'x':
		transposed_nodes = [Node(200 + node.x, node.y) for node in segment.nodes] # mirror x coordinate
		transposed_nodes.reverse() # reverse node order
		return Segment(transposed_nodes, 'x')

	if segment.trans == 'y':
		transposed_nodes = [Node(node.x, node.y - 200) for node in segment.nodes] # mirror y coordinate
		transposed_nodes.reverse() # reverse node order
		return Segment(transposed_nodes, 'y')

def print_combined_segments(shape: Shape):
	pprint.pp(shape_combined_segments(shape))

def add_node_to_shape(shape: Shape, segment_id, node_id, node_x, node_y):
	segments = shape.segments
	segment = segments[segment_id]
	segment = add_node_to_segment(segment, node_id, node_x, node_y)
	segments[segment_id] = segment
	return Shape(segments)

def add_node_to_segment(segment:Segment, node_id, node_x, node_y):
	nodes = segment.nodes
	node = Node(node_x, node_y)
	nodes.insert(node_id, node)
	return Segment(nodes, segment.trans)

def move_node_in_shape(shape: Shape, segment_id, node_id, node_delta_x, node_delta_y):
	segments = shape.segments
	segment = segments[segment_id]
	segment = move_node_in_segment(segment, node_id, node_delta_x, node_delta_y)
	segments[segment_id] = segment
	return Shape(segments)

def move_node_in_segment(segment:Segment, node_id, node_delta_x, node_delta_y):
	nodes = segment.nodes
	node = nodes[node_id]
	node = Node(node.x + node_delta_x, node.y + node_delta_y)
	nodes[node_id] = node
	return Segment(nodes, segment.trans)

def shape_coordinates(shape:Shape):
	nodes = []
	for segment in shape_combined_segments(shape):
		nodes += segment.nodes[:-1] # exclude every last node in segment to prevent overlap
	nodes.append(nodes[0]) # Duplicate the start node to the end to close the shape
	coordinates = [(node.x, node.y) for node in nodes]
	return coordinates

def print_coordinates(shape: Shape):
	pprint.pp(shape_coordinates(shape))

def shape_movable_nodes(shape:Shape):
	moveable_nodes = []
	for segment_id, segment in enumerate(shape.segments):
		for node_id, node in enumerate(segment.nodes[1:-1]):
			moveable_nodes.append((segment_id, node_id + 1))
	return moveable_nodes

# Create start square
def create_square_shape():
	# Create square
	node1 = Node(-100, -100) # left-bottom
	node2 = Node(-100,  100) # left-top
	node3 = Node( 100,  100) # right-top

	segment1 = Segment(
		nodes = [node1, node2], 
		trans = 'x'
	)
	segment2 = Segment(
		nodes = [node2, node3], 
		trans = 'y'
	)
	return Shape([segment1, segment2])


# Pygame
from pygame.locals import (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_a, K_ESCAPE, K_TAB, KEYDOWN, QUIT)
pygame.init()
screen = pygame.display.set_mode([750, 750])
clock = pygame.time.Clock()

# Set colors
#black = (0,0,0)
#green = (0,255,0)
#blue = (0,0,255)
#greybrown = (139,146,154)

white = (255,255,255)
red = (255,25,55)
lightgreenblue = (182,220,233)
darkgreenblue = (48,124,145)
greywhite = (229,227,228)
brown = (123,92,82)

color1 = lightgreenblue
color2 = darkgreenblue

# Set origin (0, 0) in the center of the screen instead of top-left and flip direction of y-axis
center_origin = lambda p, center: (center[0] + p[0] + screen.get_width() // 2, center[1] - p[1] + screen.get_height() // 2)
center_origins = lambda l, center: [center_origin(coordinates, center) for coordinates in l]

# Set the start shape
shape = create_square_shape()
shape = add_node_to_shape(shape, segment_id=0, node_id=1, node_x=-100, node_y=-30)
shape = add_node_to_shape(shape, segment_id=0, node_id=2, node_x=-70, node_y=0)
shape = add_node_to_shape(shape, segment_id=0, node_id=3, node_x=-70, node_y=30)
shape = add_node_to_shape(shape, segment_id=0, node_id=4, node_x=-100, node_y=30)
shape = add_node_to_shape(shape, segment_id=1, node_id=1, node_x=-20, node_y=100)
shape = add_node_to_shape(shape, segment_id=1, node_id=2, node_x=-0, node_y=75)
shape = add_node_to_shape(shape, segment_id=1, node_id=3, node_x=20, node_y=100)
print("Start shape")
print_combined_segments(shape)
print_coordinates(shape)

# Select the start node for movement
selected_id = 0

# Set the texts
font = pygame.font.Font(pygame.font.get_default_font(), 14)
draw_text = lambda text, pos: screen.blit(font.render(text, True, brown, greywhite), pos)

# Start loop
running = True
while running:
	movable_nodes = shape_movable_nodes(shape)
	selected_segment_id = movable_nodes[selected_id][0]
	selected_node_id = movable_nodes[selected_id][1]
	selected_node = shape.segments[selected_segment_id].nodes[selected_node_id]

	# Single key-press
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				running = False

			if event.key == K_TAB:
				selected_id += 1
				if selected_id >= len(movable_nodes): 
					selected_id = 0

			if event.key == K_a:
				shape = add_node_to_shape(
					shape, 
					segment_id=selected_segment_id, 
					node_id=selected_node_id, 
					node_x=selected_node.x, 
					node_y=selected_node.y
				)
				selected_id += 1

		elif event.type == QUIT:
			running = False

	# Continious key-press
	pressed_keys = pygame.key.get_pressed()

	if pressed_keys[K_UP]:
		shape = move_node_in_shape(shape, selected_segment_id, selected_node_id, 0, 5)
		print_coordinates(shape)

	if pressed_keys[K_DOWN]:
		shape = move_node_in_shape(shape, selected_segment_id, selected_node_id, 0, -5)
		print_coordinates(shape)

	if pressed_keys[K_LEFT]:
		shape = move_node_in_shape(shape, selected_segment_id, selected_node_id, -5, 0)
		print_coordinates(shape)

	if pressed_keys[K_RIGHT]:
		shape = move_node_in_shape(shape, selected_segment_id, selected_node_id, 5, 0)
		print_coordinates(shape)

	screen.fill(white)

	color = color1
	for x_center in range(-400,600,200):
		for y_center in range(-400,600,200):
			pygame.draw.polygon(screen, color, center_origins(shape_coordinates(shape), (x_center,y_center)))
			color = color2 if color == color1 else color1

	pygame.draw.circle(screen, red, center_origin((selected_node.x, selected_node.y), (0,0)), 7)

	draw_text("ESCHER MAKER", (10, 10))
	draw_text("Select with tab. Move with arrows. Add with a", (10, 30))
	draw_text(f"Segment: {selected_segment_id}", (10, 50))
	draw_text(f"Node: {selected_node_id}", (110, 50))
	draw_text(f"Position: ({selected_node.x}, {selected_node.y})", (185, 50))

	pygame.display.update()

	clock.tick(60)

pygame.quit()
