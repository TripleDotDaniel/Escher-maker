# pip3 install attrs
import attr
import pprint


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
		transposed_nodes = [Node(20 + node.x, node.y) for node in segment.nodes] # mirror x coordinate
		transposed_nodes.reverse() # reverse node order
		return Segment(transposed_nodes, 'x')

	if segment.trans == 'y':
		transposed_nodes = [Node(node.x, node.y - 20) for node in segment.nodes] # mirror y coordinate
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


# Create square
node1 = Node(-10, -10) # left-bottom
node2 = Node(-10,  10) # left-top
node3 = Node( 10,  10) # right-top

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


# Add node to first segment
node = Node(-7, 2) # Make a small dent just above the middle
index = 1 # Put node between the first and the second node
segment1 = add_node_to_segment(segment1, node, index)
shape = Shape([segment1, segment2])

print("\nAdd node to first segment")
print_combined_segments(shape)


# Update node in first segment
node = Node(-7, 4) # Make a bigger dent
index = 1 # Update the second node
segment1 = update_node_in_segment(segment1, node, index)
shape = Shape([segment1, segment2])

print("\nUpdate node in first segment")
print_combined_segments(shape)


# Create list of coordinates for drawing the shape
print("\nCreate list of coordinates for drawing the shape")
print_coordinates(shape)

