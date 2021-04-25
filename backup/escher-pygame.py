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

@attr.s(frozen=True)
class MoveableNode(object):
	segment_id = attr.ib()
	node_id = attr.ib()
	node = attr.ib()

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

def add_node_to_shape(shape: Shape, segment_id, node_id, node: Node):
	segments = shape.segments
	segment = segments[segment_id]
	nodes = segment.nodes
	nodes.insert(node_id, node)
	segments[segment_id] = Segment(nodes, segment.trans)
	return Shape(segments)

def replace_node_in_shape(shape: Shape, segment_id, node_id, node: Node):
	segments = shape.segments
	segment = segments[segment_id]
	nodes = segment.nodes
	nodes[node_id] = node
	segments[segment_id] = Segment(nodes, segment.trans)
	return Shape(segments)

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
			moveable_node = MoveableNode(segment_id, node_id + 1, node)
			moveable_nodes.append(moveable_node)
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
from pygame.locals import *
pygame.init()
screen = pygame.display.set_mode([750, 750])
clock = pygame.time.Clock()

# Set colors
black = (0,0,0)
#green = (0,255,0)
#blue = (0,0,255)
greybrown = (139,146,154)

white = (255,255,255)
red = (255,25,55)
lightgreenblue = (182,220,233)
darkgreenblue = (48,124,145)
greywhite = (229,227,228)
brown = (123,92,82)

color1 = lightgreenblue
color2 = darkgreenblue

X,Y,Z = 0,1,2

# Set origin (0, 0) in the center of the screen instead of top-left and flip direction of y-axis
coord_to_screen = lambda c, center: (c[0] + center[0] + screen.get_width() // 2, - c[1] + center[1] + screen.get_height() // 2)
coords_to_screen = lambda l, center: [coord_to_screen(coordinates, center) for coordinates in l]
screen_to_coord = lambda s, center: (s[0] - center[0] - screen.get_width() // 2, - s[1] + center[1] + screen.get_height() // 2) 

# Set the start shape
shape = create_square_shape()
shape = add_node_to_shape(shape, segment_id=0, node_id=1, node=Node(-100, -30))
shape = add_node_to_shape(shape, segment_id=0, node_id=2, node=Node(-70, 0))
shape = add_node_to_shape(shape, segment_id=0, node_id=3, node=Node(-70, 30))
shape = add_node_to_shape(shape, segment_id=0, node_id=4, node=Node(-100, 30))
shape = add_node_to_shape(shape, segment_id=1, node_id=1, node=Node(-20, 100))
shape = add_node_to_shape(shape, segment_id=1, node_id=2, node=Node(0, 75))
shape = add_node_to_shape(shape, segment_id=1, node_id=3, node=Node(20, 100))
print("Start shape")
print_combined_segments(shape)
print_coordinates(shape)

# Select the start node for movement
selected = None

# Set the texts
font = pygame.font.Font(pygame.font.get_default_font(), 14)
draw_text = lambda text, pos: screen.blit(font.render(text, True, brown, greywhite), pos)

# Start loop
running = True
while running:
	movable_nodes = shape_movable_nodes(shape)

	# Single key-press
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				running = False

		elif event.type == MOUSEBUTTONDOWN and event.button == 1:
			mouse_x, mouse_y = screen_to_coord(pygame.mouse.get_pos(), (0,0))
			print(pygame.mouse.get_pos(), mouse_x, mouse_y)
			for m in movable_nodes:
				if abs(m.node.x - mouse_x) < 10 and abs(m.node.y - mouse_y) < 10 :
					selected = m

		elif event.type == MOUSEBUTTONUP and event.button == 1:
			selected = None

		elif event.type == QUIT:
			running = False

	screen.fill(white)

	color = color1
	for x_center in range(-400,600,200):
		for y_center in range(-400,600,200):
			pygame.draw.polygon(screen, color, coords_to_screen(shape_coordinates(shape), (x_center,y_center)))
			color = color2 if color == color1 else color1

	movable_nodes = shape_movable_nodes(shape)
	for moveable_node in movable_nodes:
		coord = (moveable_node.node.x, moveable_node.node.y)
		pygame.draw.circle(screen, black, coord_to_screen(coord, (0,0)), 1)

	if selected is not None:
		mouse_pos = pygame.mouse.get_pos();
		mouse_x, mouse_y = screen_to_coord(mouse_pos, (0,0))
		shape = replace_node_in_shape(shape, selected.segment_id, selected.node_id, Node(mouse_x, mouse_y))
		pygame.draw.circle(screen, red, (mouse_pos[0], mouse_pos[1]), 5)

	draw_text("ESCHER MAKER", (10, 10))
	# draw_text("Select with tab. Move with arrows. Add with a", (10, 30))
	# draw_text(f"Segment: {selected_segment_id}", (10, 50))
	# draw_text(f"Node: {selected_node_id}", (110, 50))
	# draw_text(f"Position: ({selected_node.x}, {selected_node.y})", (185, 50))

	pygame.display.update()

	clock.tick(60)

pygame.quit()
