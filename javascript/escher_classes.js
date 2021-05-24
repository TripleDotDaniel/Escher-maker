class Node {
  constructor(x, y) {
    this.pos = createVector(x, y);
    this.movable = true;
    this.node_id = objectId(this);
  }
  
  move(movement) {
    this.pos.add(movement);
  }
  
  set_pos(position) {
    this.pos = position;
  }
}

class Segment {
  constructor(nodes, angle, dist_to_center) {
    this.nodes = nodes;
    this.angle = angle;
    this.dist_to_center = dist_to_center;
    this.segment_id = objectId(this);
  }
}

class Link {
  constructor(segment_source, segment_linked, flip_x, flip_y) {
    this.segment_source = segment_source;
    this.segment_linked = segment_linked;   
    this.flip_x = flip_x;
    this.flip_y = flip_y;
    this.segment_source_id = objectId(segment_source);
    this.segment_linked_id = objectId(segment_linked);
    this.link_id = objectId(this);
  }
  
  get_linked_node(node) {
    let index_node = this.segment_source.nodes.indexOf(node);
    if (this.flip_x) {
      index_node = this.segment_source.nodes.length - 1 - index_node;
    }
    return this.segment_linked.nodes[index_node];
  }
  
  update_linked_segment(node) {
    let new_pos = node.pos.copy();
    // first rotate back such that the segment is horizontal, 
    // do flips, rotate to new angle
    new_pos.rotate(this.segment_source.angle);
    new_pos.add(0, -this.segment_source.dist_to_center);
    if (this.flip_x) {
      new_pos.mult(-1, 1);
    }
    if (this.flip_y) {
      new_pos.mult(1, -1);
    }
    new_pos.add(0, this.segment_source.dist_to_center);
    new_pos.rotate(-this.segment_linked.angle);
    this.get_linked_node(node).pos = new_pos;
  }
}

class Shape {
  constructor(segments, links) {
    this.segments = segments;
    this.links = links;
  }
  
  get_nodes() {
    // exclude every last node in segment to prevent overlap
    let nodes = [];
    for (let segment of this.segments) {
      for (let i = 0; i < (segment.nodes.length-1); i++) {
        nodes.push(segment.nodes[i]);
      }
    }
    return nodes;
  }
  
  get_movable_nodes() {
    let movable_nodes = [];
    for (let node of this.get_nodes()) {
      if (node.movable) {
        movable_nodes.push(node);
      }
    }
    return movable_nodes;
  }
  
  get_coordinates(smoothed_curves) {
    if (smoothed_curves) {
      return this.get_smooth_coordinates();
    }
    let coordinates = [];
    let nodes = this.get_nodes();
    for (let node of this.get_nodes()) {
      coordinates.push(node.pos);
    }
    return coordinates
  }
  
  get_smooth_coordinates() {
    let smooth_coordinates = [];
    for (let index_side=0; index_side < this.segments.length / 2; index_side++) {
      let nodes0 = this.segments[2 * index_side].nodes;
      let nodes1 = this.segments[2 * index_side + 1].nodes;
      let nodes_side = nodes0.concat(nodes1.slice(1));
      let coordinates = [];
      for (let node of nodes_side) {
        coordinates.push(node.pos);
      }
      let scoordinates = smooth_curve(coordinates);
      smooth_coordinates = smooth_coordinates.concat(scoordinates);
    }
    return smooth_coordinates;
  }
      
  move_node(node, movement) {
    if (!node.movable) { return }
    node.move(movement);
    this.update_linked_nodes(node);
  }
    
  set_pos_node(node, position) {
    if (!node.movable) { return }
    node.set_pos(position);
    this.update_linked_nodes(node);
  }
                        
  update_linked_nodes(node) {
    // update linked segment(s)
    let nodes_link_to_updated = [node];
    let nodes_updated = [node];

    while (nodes_link_to_updated.length > 0) {
      let node_link_to_updated = nodes_link_to_updated.pop(0);
      for (let link of this.links) {
        if (link.segment_source.nodes.includes(node_link_to_updated)) {
          let linked_node = link.get_linked_node(node_link_to_updated);
          if (!nodes_updated.includes(linked_node)) {
            link.update_linked_segment(node_link_to_updated);
            nodes_updated.push(linked_node);
            nodes_link_to_updated.push(linked_node);
          }
        }
      }
    }
  }

  add_node(nodes, add_linked_node=true) {
    // add node
    for (let segment of this.segments) {
      if (segment.nodes.includes(nodes[0]) && segment.nodes.includes(nodes[1])) {
        let link = this.get_link_from_segment(segment);
        let linked_nodes = [link.get_linked_node(nodes[0]),
                            link.get_linked_node(nodes[1])];

        // place new node in between current and next node
        let new_node_pos = p5.Vector.add(nodes[0].pos, nodes[1].pos
                                          ).mult(0.5);
        let new_node = new Node(new_node_pos.x, new_node_pos.y);
        let node0_index = segment.nodes.indexOf(nodes[0]);
        let node1_index = segment.nodes.indexOf(nodes[1]);
        segment.nodes.splice(Math.min(node0_index,node1_index) + 1, 0, new_node);

        if (add_linked_node) {
          this.add_node(linked_nodes, false);
          return new_node;
        }
        break
      }
    }
  }
    
  get_next_node(node) {
    let movable_nodes = this.get_movable_nodes()
    if (movable_nodes.includes(node)) {
      return movable_nodes[(movable_nodes.indexOf(node) + 1) % movable_nodes.length];
    } else {
      return movable_nodes[0];
    }
  }
    
  get_linked_nodes(node) {
    let nodes = [node];
    for (let _node of nodes) {
      for (let link of this.links) {
        if (link.segment_source.nodes.includes(_node)) {
          let linked_node = link.get_linked_node(_node);
          if (!nodes.includes(linked_node)) {
            nodes.push(linked_node);
          }
        }
      }
    }
    return nodes;
  }
  
  get_link_from_segment(segment) {
    for (let link of this.links) {
      if (segment == link.segment_source) {
        return link;
      }
    }
    return null;
  }
}

class Tile {
  constructor(pos, rot=0, mirror=1) {
    rot = modulo(rot, 2*PI);
    if ((2*PI - rot) < 0.01) {
      rot = 0;
    }
    this.pos = pos;
    this.rot = rot;
    this.mirror = mirror;
  }
  
  move_coordinates(coordinates) {
    let moved_coordinates = [];
    for (let coordinate of coordinates) {
      let moved_coordinate = coordinate.copy();
      moved_coordinate.mult([this.mirror, 1]);
      moved_coordinate.rotate(-this.rot);
      moved_coordinate.add(this.pos);
      moved_coordinates.push(moved_coordinate);
    }
    return moved_coordinates;
  }
}

class Pattern {
  constructor(tiles, combination, shape, name=""){
    this.tiles = tiles;
    this.combination = combination;
    this.shape = shape;
    this.name = name;
  }
}
    
    
function create_shape(combination, movable_corner=true) {
  let radius = 1;
  let nodes_per_segment = 3;
  let segment_per_side = 2;
  let nr_sides = combination.length;
  let height = radius * cos(PI / nr_sides);
  let nodes_per_side = (nodes_per_segment - 1) * segment_per_side;
  // minus 1 because of the overlapping node per segment

  // create nodes
  let left_corner_pos = createVector(-1 * tan(PI / nr_sides) * height, height);
  let right_corner_pos = p5.Vector.mult(left_corner_pos, [-1, 1]);

  // right corner is an overlapping node, added for correct spacing and then removed
  let nodes_pos = linspace_vector(left_corner_pos, right_corner_pos, nodes_per_side + 1);
  nodes_pos.pop();
  
  let nodes = [];
  for (let index_side = 0; index_side < nr_sides; index_side++) {
    let angle = 2 * PI / nr_sides * index_side;
    for (let node_pos of nodes_pos) {
      let node_pos_rot = p5.Vector.rotate(node_pos, -angle);
      nodes.push(new Node(node_pos_rot.x, node_pos_rot.y));
    }
    if (!movable_corner) {
      nodes[nodes.length-nodes_pos.length].movable = false;
    }
  }
    
  // create segments
  let segments = [];
  for (let index_side = 0; index_side < nr_sides; index_side++) {
    let angle = 2 * PI / nr_sides * index_side;
    for (let s = 0; s < segment_per_side; s++) {
      let index_segment = index_side * segment_per_side + s;
      let segment_nodes = [];
      for (let i = 0; i < nodes_per_segment; i++) {
        let index_node = (index_segment * (nodes_per_segment - 1) + i) % nodes.length;
        segment_nodes.push(nodes[index_node]);
      }
      segments.push(new Segment(segment_nodes,
                                angle,
                                height))
    }
  }

  // create links
  links = []
  for (let index_side = 0; index_side < nr_sides; index_side++) {
    if (index_side == combination[index_side]) {  // side linked to itself
      links.push(new Link(segments[2 * index_side],
                        segments[2 * index_side + 1],
                        true,
                        true));
      links.push(new Link(segments[2 * index_side + 1],
                        segments[2 * index_side],
                        true,
                        true));
      segments[2 * index_side + 1].nodes[0].movable = false;
    } else if (combination[index_side] >= 0) { // side linked to other side of shape
      links.push(new Link(segments[2 * index_side],
                        segments[2 * combination[index_side] + 1],
                        true,
                        true));
      links.push(new Link(segments[2 * index_side + 1],
                        segments[2 * combination[index_side]],
                        true,
                        true));
    } else { // side linked to other side of flipped shape
      links.push(new Link(segments[2 * index_side],
                        segments[2 * (-combination[index_side] - 1)],
                        false,
                        true));
      links.push(new Link(segments[2 * index_side + 1],
                        segments[2 * (-combination[index_side] - 1) + 1],
                        false,
                        true));
    }
  }
  let shape = new Shape(segments=segments, links=links);
  return shape; 
}

function linspace(startValue, stopValue, cardinality) {
  var arr = [];
  var step = (stopValue - startValue) / (cardinality - 1);
  for (var i = 0; i < cardinality; i++) {
    arr.push(startValue + (step * i));
  }
  return arr;
}    
    
function linspace_vector(v0, v1, N) {
  vs = [];
  for (let n=0; n<N; n++) {
    vs.push(p5.Vector.lerp(v0, v1, n / (N-1)));
  }
  return vs;
}

function tile_in_set(tiles, new_tile, eps=1e-5) {
  for (let tile of tiles) {
    let diff_pos = abs(tile.pos.dist(new_tile.pos));
    let diff_rot = abs(tile.rot - new_tile.rot);
    if (diff_rot > PI) {diff_rot -= 2 * PI;}
    if (diff_pos < eps) {
      if (tile.mirror == new_tile.mirror && diff_rot < eps) {
        return [true, true];
      }
      return [true, false];
    }
            
  }
  return [false, false]
}
    
function index_to_rotation(index, nr_sides) {
    return 2 * PI / nr_sides * index;
}

function make_pattern(combination, max_distance=4.5, movable_corner=true) {
  let radius = 1;
  let nr_sides = combination.length;
  let shape = create_shape(combination, movable_corner);
  let tiles = [new Tile(createVector(0,0))];
  let index_tile = 0;
  let height = radius * cos(PI / nr_sides);
  while (index_tile < tiles.length) {
    let tile = tiles[index_tile];
    for (let index_side=0; index_side<nr_sides; index_side++) {
      let direction = tile.rot + index_to_rotation(index_side, nr_sides) * tile.mirror;
      let side_match = 0;
      let mirror = 0;
      if (combination[index_side] >= 0) {
        side_match = combination[index_side];
        mirror = tile.mirror;
      } else {
        side_match = -combination[index_side] - 1;
        mirror = -tile.mirror;
      }
      let new_pos = p5.Vector.add(tile.pos, p5.Vector.mult(createVector(sin(direction), cos(direction)), 2 * height));
      let new_rot = (direction - index_to_rotation(side_match, nr_sides) * mirror + PI) % (2 * PI);
      let new_tile = new Tile(new_pos, new_rot, mirror);
      let inset = tile_in_set(tiles, new_tile);
      if (new_tile.pos.mag() < (max_distance * height)){
        if (!inset[0]) {
          tiles.push(new_tile);
        } else if (!inset[1]) {
          throw "Combination does not result in a valid pattern";
        }
      }
    }
    index_tile += 1;
  }
  let pattern = new Pattern(tiles, combination, shape);
  return pattern;
}
    
function smooth_curve(points, nr_of_subdivisions=5) {
  // based on https://stackoverflow.com/a/27650158
  let nr_of_points = points.length;
  let t = range(0, nr_of_points-1);
  let x = [];
  let y = [];
  for (let pos of points) {
    x.push(pos.x)
    y.push(pos.y)
  }
  let ti = linspace(0, nr_of_points - 1, nr_of_subdivisions * nr_of_points);
  let temp = linspace(0, nr_of_points - 1, nr_of_subdivisions * nr_of_points);

  let xs = [];
  let ys = [];
  CSPL.getNaturalKs(t,x,xs);
  CSPL.getNaturalKs(t,y,ys);
  let xi = CSPL.evalPoints(ti, t, x, xs);
  let yi = CSPL.evalPoints(ti, t, y, ys);
  
  let points_smooth = [];
  for (let i=0; i<xi.length; i++) {
    points_smooth.push(createVector(xi[i],yi[i]));
  }
  return points_smooth
}

function range(start, end) {
  return Array(end - start + 1).fill().map((_, idx) => start + idx)
}

function modulo(a, n) {
  return ((a % n ) + n ) % n;
}
    
    
var objectId = (function () {
    var allObjects = [];

    var f = function(obj) {
        if (allObjects.indexOf(obj) === -1) {
            allObjects.push(obj);
        }
        return allObjects.indexOf(obj);
    }
    f.clear = function() {
      allObjects = [];
    };
    return f;
})();
