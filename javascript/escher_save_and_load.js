function export_figure(filename, show_prompt=true) {
  if (filename == null) {
     filename = "Escher_pattern.png";
  }
  if (show_prompt) {
    filename = prompt("Export figure as:", filename);
    if (filename == null) {
        return false;
    }
  }
  let prev_show_nodes = settings.show_nodes;
  settings.show_nodes = false;
  draw();
  saveCanvas(filename);
  settings.show_nodes = prev_show_nodes;
}

function save_pattern(filename, show_prompt=true) {
  if (filename == null) {
     filename = "Escher_pattern.json";
  }
  if (show_prompt) {
    filename = prompt("Save pattern as:", filename);
    if (filename == null) {
        return false;
    }
  }
  let pattern_list = make_object_list(pattern);
  let combined = {pattern: pattern_list, settings: settings};
  saveJSON(combined, filename);

  // recreate pattern because the pattern object was changed in the process to create the JSON
  pattern = object_from_object_list(pattern_list);
  active_node = pattern.shape.get_next_node([]);
  return true;
}

function load_pattern(filename) {
    // if filename is given load from server, else open prompt to load from local disk
    if (filename != null) {
        loadJSON('patterns/' + filename, process_loaded_JSON, load_pattern_error_callback);
    } else {
        if (!confirm("Are you sure you want to load a pattern?\nThe current pattern will be lost.")) {
            return
        }
        var input = document.createElement('input');
        input.type = 'file';
        input.onchange = e => {
            // getting a hold of the file reference
            var file = e.target.files[0];
            var reader = new FileReader();
            reader.readAsText(file,'UTF-8');
            reader.onload = readerEvent => {
                var content = readerEvent.target.result;
                process_loaded_JSON(JSON.parse(content));
            }
        }
        input.click();
    }
}

function process_loaded_JSON(json_data) {
    pattern = object_from_object_list(json_data.pattern);
    for (let key of Object.keys(json_data.settings)) {
        settings[key] = json_data.settings[key];
    }
    active_node = pattern.shape.get_next_node([]);
}

function load_pattern_error_callback(error) {
    print(error)
}

function make_object_list(object) {
  let object_list = [object];
  let index = 0
  while (index < object_list.length) {
    object = object_list[index];
    let keys = Object.keys(object);
    for (let key of keys) {
      object[key] = object_to_ref(object[key], object_list);
    }
    index++;
  }
  for (let object of object_list) {
    object.type = object.constructor.name;
  }
  return object_list;
}

function object_to_ref(object, object_list) {
  // handle arrays
  if (Array.isArray(object)) {
    let output = [];
    for (let element of object) {
      output.push(object_to_ref(element, object_list));
    }
    return output;
  }

  // handle non-objects
  if (typeof object !== 'object') {
    return object;
  }

  // handle P5 vectors
  if (object instanceof p5.Vector) {
    return ["P5vector", [object.x, object.y]]
  }

  // handle other objects
  let index = object_list.indexOf(object);
  if (index == -1) {
    object_list.push(object);
    index = object_list.length-1;
  }
  return ["Object_ref", index];
}

function object_from_object_list(object_list) {
  const classes = {
    Node,
    Segment,
    Link,
    Shape,
    Tile,
    Pattern
  }
  for (const [index, object] of object_list.entries()) {
    if (object.hasOwnProperty("type")) {
      let temp_object = new classes[object.type]();
      for (let key of Object.keys(object)) {
        temp_object[key] = object[key];
      }
      object_list[index] = temp_object;
    }
  }

  for (let object of object_list) {
    for (let key of Object.keys(object)) {
      object[key] = ref_to_object(object[key], object_list);
    }
  }
  return object_list[0];
}

function ref_to_object(ref, object_list) {
  // handle non references or arrays
  if (!Array.isArray(ref)) {
    return ref;
  }

  // handle P5 vectors
  if (ref[0] === "P5vector") {
    return createVector(ref[1][0], ref[1][1]);
  }

  // handle object references
  if (ref[0] === "Object_ref") {
    return object_list[ref[1]];
  }

  // handle arrays
  let output = [];
  for (let element of ref) {
    output.push(ref_to_object(element, object_list));
  }
  return output;
}