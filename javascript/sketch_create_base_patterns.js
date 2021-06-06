let combinations = [
  [[0, 1, 2], false],
  [[0, 2, 1], false],
  [[0, -3, -2], false],
  [[0, 1, 2, 3], true],
  [[0, 3, 2, 1], false],
  [[1, 0, 3, 2], false],
  [[2, 3, 0, 1], true],
  [[0, 1, -4, -3], true],
  [[0, -4, 2, -2], true],
  [[-2, -1, -4, -3], true],
  [[2, -4, 0, -2], true],
  [[-3, -4, -1, -2], false],
  [[0, 1, 5, 3, 4, 2], true],
  [[1, 0, 3, 2, 5, 4], false],
  [[3, 4, 5, 0, 1, 2], true],
  [[0, 1, 5, -5, -4, 2], true],
  [[0, -4, -6, -2, 4, -3], true],
  [[-2, -1, 5, -5, -4, 2], true],
];
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
let pattern;

function pause(msec) {
    // based on https://stackoverflow.com/a/53841885
    return new Promise(
        (resolve, reject) => {
            setTimeout(resolve, msec || 1000);
        }
    );
}

async function create_and_save_patterns() {
  let i = 0;

  for (let combination of combinations) {
    createP(`Save base pattern ${i + 1}`);
    pattern = make_pattern(combination[0], 20, combination[1]);
    pattern.name = `Pattern ${i + 1} (${combination[0].length}-sided)`;
    result  = save_pattern(`base_pattern_${i + 1}.json`, false);
    if (!result) {break}
    await pause(1000);
    i++;
  }
  createP('Done')
}
function setup() {
    create_and_save_patterns();
}
