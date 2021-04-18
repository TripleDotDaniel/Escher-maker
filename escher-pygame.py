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

def add_node_to_segment(segment:Segment, new_node:Node, index:int):
	new_nodes = segment.nodes
	new_nodes.insert(index, new_node)
	return Segment(new_nodes, segment.trans)

def update_node_in_segment(segment:Segment, updated_node:Node, index:int):
	updated_nodes = segment.nodes
	updated_nodes[index] = updated_node
	return Segment(updated_nodes, segment.trans)

def shape_coordinates(shape:Shape):
	nodes = []
	for segment in shape_combined_segments(shape):
		nodes += segment.nodes[:-1] # exclude every last node in segment to prevent overlap
	nodes.append(nodes[0]) # Duplicate the start node to the end to close the shape
	coordinates = [(node.x, node.y) for node in nodes]
	return coordinates

def print_coordinates(shape: Shape):
	pprint.pp(shape_coordinates(shape))


# Steps for demonstration
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

	shape = Shape([segment1, segment2])
	print("Create square")
	print_combined_segments(shape)
	return shape

def add_node_to_first_segment(shape: Shape):
	segment1 = shape.segments[0]
	segment2 = shape.segments[1]
	node = Node(-70, 20) # Make a small dent just below the middle
	index = 1 # Put node between the first and the second node
	segment1 = add_node_to_segment(segment1, node, index)
	shape = Shape([segment1, segment2])
	print("\nAdd node to first segment")
	print_combined_segments(shape)
	return shape

def move_node_in_first_segment(shape: Shape, move_x, move_y):
	segment1 = shape.segments[0]
	segment2 = shape.segments[1]
	index = 1
	node = segment1.nodes[index]
	moved_node = Node(node.x + move_x, node.y + move_y)
	segment1 = update_node_in_segment(segment1, moved_node, index)
	shape = Shape([segment1, segment2])
	print("\nUpdate node in first segment")
	print_combined_segments(shape)
	return shape


# Pygame
from pygame.locals import (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_ESCAPE, KEYDOWN, QUIT)

pygame.init()
screen = pygame.display.set_mode([500, 500])
clock = pygame.time.Clock()

white = (255,255,255)
black = (0,0,0)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)

# Set origin (0, 0) in the center of the screen instead of top-left
center_origin = lambda p: (p[0] + screen.get_width() // 2, p[1] + screen.get_height() // 2)
center_origins = lambda l: [center_origin(coordinates) for coordinates in l]

# Set the start shape
shape = create_square_shape()
shape = add_node_to_first_segment(shape)

running = True
while running:

	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				running = False
		elif event.type == QUIT:
			running = False

	pressed_keys = pygame.key.get_pressed()

	if pressed_keys[K_UP]:
		shape = move_node_in_first_segment(shape, 0, -10)
		print_coordinates(shape)

	if pressed_keys[K_DOWN]:
		shape = move_node_in_first_segment(shape, 0, 10)
		print_coordinates(shape)

	if pressed_keys[K_LEFT]:
		shape = move_node_in_first_segment(shape, -10, 0)
		print_coordinates(shape)

	if pressed_keys[K_RIGHT]:
		shape = move_node_in_first_segment(shape, 10, 0)
		print_coordinates(shape)

	screen.fill(white)
	pygame.draw.polygon(screen, green, center_origins(shape_coordinates(shape)))
	pygame.display.update()

	clock.tick(60)

pygame.quit()



