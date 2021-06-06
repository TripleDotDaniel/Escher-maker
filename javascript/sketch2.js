let pattern;
let active_node;
let track_mouse = false;

let settings = {
  shape_radius: 80,
  rotation: 0,
  size_node: 10,
  select_distance: 20,
  projection: "Spherical",
  smoothed_curves: true,
  borders: true,
  show_nodes: true,
  background_color: [220, 220, 220],
  tile_color: [144, 191, 42],
  tile_flipped_color: [3, 120, 166],
  border_color: [255, 255, 255],
  movable_node_color: [255, 255, 255],
  unmovable_node_color: [100, 100, 100],
  active_node_color: [255.0, 0, 0],
  linked_node_color: [255.0, 100, 100],
};
let button_functions = {
  export_figure: export_figure,
  reset_pattern: reset_pattern,
  save_pattern: save_pattern,
  load_pattern: load_pattern,
};

function preload() {
  let params = getURLParams();
  if (params.pattern == null) {
    params.pattern = 'base_pattern_2';
  }
  print(params.pattern)
  pattern = load_pattern(params.pattern + '.json');
}

function setup() {
  active_node = pattern.shape.get_next_node([]);


  // create gui (dat.gui)
  let gui = new dat.GUI({ name: "EscherMaker" });
  gui.useLocalStorage = true;
  gui.add(button_functions, "reset_pattern").name("Reset pattern");
  gui.add(button_functions, "save_pattern").name("Save pattern");
  gui.add(button_functions, "load_pattern").name("Load pattern");
  gui.add(button_functions, "export_figure").name("Export figure");

  var f_display = gui.addFolder("Display");
  f_display.add(settings, "projection", ["Spherical", "Flat"]).name("Projection").listen();
  f_display.add(settings, "smoothed_curves").name("Smooth curves").listen();
  f_display.add(settings, "borders").name("Show borders").listen();
  f_display.add(settings, "show_nodes").name("Show nodes").listen();
  f_display.add(settings, "shape_radius").min(10).max(200).name("Zoom").listen();
  f_display.add(settings, "rotation").min(-180).max(180).name("Rotate").listen();

  var f_color = gui.addFolder("Colors");
  f_color.addColor(settings, "tile_color").name("Tile").listen();
  f_color.addColor(settings, "tile_flipped_color").name("Flipped tile").listen();
  f_color.addColor(settings, "border_color").name("Border").listen();
  f_color.addColor(settings, "background_color").name("Background").listen();

  // touch control (hammer.js)
  var hammer = new Hammer(document.body, { preventDefault: true });
  hammer.get("pinch").set({ enable: true });
  hammer.get("rotate").set({ enable: true });
  hammer.on("pinch", scale_screen);
  hammer.on("rotate", rotate_screen);

  createCanvas(windowWidth, windowHeight);
}

function draw() {
  handle_keypresses();
  if (track_mouse) {
    let mouse_pos = screen_pos_to_pattern_pos(createVector(mouseX, mouseY));
    pattern.shape.set_pos_node(active_node, mouse_pos);
  }

  background(settings.background_color);
  draw_pattern(pattern);
  if (settings.show_nodes) {
    draw_nodes(pattern);
  }
}

function draw_pattern(pattern) {
  let tile_shapes = [];
  let shape_points = pattern.shape.get_coordinates(settings.smoothed_curves);
  for (let tile of pattern.tiles) {
    let shape_points_moved = tile.move_coordinates(shape_points);
    let color = [...settings.tile_color];
    if (tile.mirror < 0) {
      color = [...settings.tile_flipped_color];
    }
    for (let i = 0; i < color.length; i++) {
      color[i] *= (2 * PI + 1 - tile.rot) / (2 * PI + 1);
    }
    fill(color);
    if (settings.borders) {
      stroke(settings.border_color);
    } else {
      noStroke();
    }
    draw_polygon(shape_points_moved);
  }
}

function draw_nodes(pattern) {
  let nodes = pattern.shape.get_nodes();

  for (let node of nodes) {
    if (node.movable) {
      fill(settings.movable_node_color);
    } else {
      fill(settings.unmovable_node_color);
    }
    let pos = pattern_pos_to_screen_pos(node.pos);
    ellipse(pos.x, pos.y, settings.size_node, settings.size_node);
  }

  fill(settings.linked_node_color);
  let linked_nodes = pattern.shape.get_linked_nodes(active_node);
  for (let node of linked_nodes) {
    let pos = pattern_pos_to_screen_pos(node.pos);
    ellipse(pos.x, pos.y, settings.size_node, settings.size_node);
  }

  fill(settings.active_node_color);
  let pos = pattern_pos_to_screen_pos(active_node.pos);
  ellipse(pos.x, pos.y, settings.size_node, settings.size_node);
}

function draw_polygon(coordinates) {
  beginShape();
  for (let coordinate of coordinates) {
    let pos = pattern_pos_to_screen_pos(coordinate);
    vertex(pos.x, pos.y);
  }
  endShape(CLOSE);
}

function handle_keypresses() {
  if (keyIsPressed) {
    let movement = 0.05;
    if (keyCode === LEFT_ARROW) {
      pattern.shape.move_node(active_node, createVector(-movement, 0));
    } else if (keyCode === RIGHT_ARROW) {
      pattern.shape.move_node(active_node, createVector(movement, 0));
    } else if (keyCode === UP_ARROW) {
      pattern.shape.move_node(active_node, createVector(0, movement));
    } else if (keyCode === DOWN_ARROW) {
      pattern.shape.move_node(active_node, createVector(0, -movement));
    }
  }
}

function keyPressed() {
  if (key == "z") {
    active_node = pattern.shape.get_next_node(active_node);
  }
  if (key == "x") {
    select_next_pattern();
  }
}

function getNextItem(array, currentItem) {
  const currentIndex = array.indexOf(currentItem);
  const nextIndex = (currentIndex + 1) % array.length;
  return array[nextIndex];
}

function mousePressed() {
  if (mouseButton === LEFT) {
    let mouse_pos = createVector(mouseX, mouseY);
    select_active_node(mouse_pos);
  }
  if (mouseButton === CENTER) {
    let mouse_pos = createVector(mouseX, mouseY);
    add_node(mouse_pos);
  }
}

function select_active_node(point) {
  let best_d = 2 * settings.select_distance;
  let best_node;

  for (let node of pattern.shape.get_nodes()) {
    if (node.movable) {
      let node_screen_pos = pattern_pos_to_screen_pos(node.pos);
      let d = node_screen_pos.dist(point);
      if (d < best_d) {
        best_d = d;
        best_node = node;
      }
    }
  }

  if (best_d < settings.select_distance) {
    active_node = best_node;
    track_mouse = true;
  }
}

function mouseReleased() {
  track_mouse = false;
}

function add_node(point) {
  let [best_d, best_nodes] = findClosesSegment(point);
  if (best_d < settings.select_distance) {
    active_node = pattern.shape.add_node(best_nodes);
    pattern.shape.set_pos_node(active_node, screen_pos_to_pattern_pos(point));
    track_mouse = true;
  }
}

function findClosesSegment(point) {
  let nodes = pattern.shape.get_nodes();
  nodes.push(nodes[0]); // add first node to the end for wrapping
  let best_d = windowWidth;
  let best_nodes;
  for (i = 0; i + 1 < nodes.length; i++) {
    let node0_screen_pos = pattern_pos_to_screen_pos(nodes[i].pos);
    let node1_screen_pos = pattern_pos_to_screen_pos(nodes[i + 1].pos);
    let d = distanceToSegment(point, node0_screen_pos, node1_screen_pos);
    if (d < best_d) {
      best_d = d;
      best_nodes = [nodes[i], nodes[i + 1]];
    }
  }
  return [best_d, best_nodes];
}

function mouseWheel(event) {
  settings.shape_radius += event.delta / 10;
  settings.shape_radius = Math.max(10, settings.shape_radius);
  settings.shape_radius = Math.min(200, settings.shape_radius);
  return false;
}

function distanceToSegment(p, s0, s1) {
  // based on https://stackoverflow.com/a/1501725
  var L2 = p5.Vector.sub(s0, s1).magSq();
  if (L2 == 0) {
    return p.dist(s0);
  }
  var s1ms0 = p5.Vector.sub(s1, s0);
  var t = p5.Vector.sub(p, s0).dot(s1ms0) / L2;
  t = Math.max(0, Math.min(1, t));
  var projection = s1ms0.mult(t).add(s0);
  return p.dist(projection);
}

function pattern_pos_to_screen_pos(pos) {
  let new_pos = pos.copy();
  if (settings.projection === "Spherical") {
    new_pos = spherical_transform(new_pos);
  }
  new_pos.mult([settings.shape_radius, -settings.shape_radius]);
  new_pos.rotate((settings.rotation / 180) * PI);
  new_pos.add([windowWidth * 0.5, windowHeight * 0.5]);

  return new_pos;
}

function screen_pos_to_pattern_pos(pos) {
  let new_pos = pos.copy();
  new_pos.add([-windowWidth * 0.5, -windowHeight * 0.5]);
  new_pos.rotate((-settings.rotation / 180) * PI);
  new_pos.mult([1 / settings.shape_radius, -1 / settings.shape_radius]);
  return new_pos;
}

function spherical_transform(pos) {
  let circle_radius = 3;
  let c = circle_radius / (circle_radius - 1);
  let norm = pos.mag();
  if (norm > 0) {
    let scaling = (circle_radius * (1 - pow(c, -norm))) / norm;
    pos = pos.mult(scaling);
  }
  return pos;
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
}

function scale_screen(event) {
  settings.shape_radius = event.scale * 80;
}

function rotate_screen(event) {
  settings.rotation = event.rotation;
}

function reset_pattern() {
  if (confirm("Are you sure you want to reset this pattern?")) {
    pattern.shape = create_shape(pattern.combination, pattern.movable_corner);
    active_node = pattern.shape.get_next_node([]);
  }
}
