MODEL_SOURCES := model/model.yaml $(wildcard model/indicators/*.yaml)

define STRIP_JSON_SCHEMA_PY
import json
from pathlib import Path

COMPUTATION_FIELDS = {
    "weight",
    "score",
    "total_score",
    "computed_score",
    "answer_score",
    "is_bonus",
}


def strip_node(node):
    if isinstance(node, list):
        return [strip_node(item) for item in node]
    if not isinstance(node, dict):
        return node

    stripped = {}
    for key, value in node.items():
        if key == "default":
            continue
        if key == "properties" and isinstance(value, dict):
            stripped[key] = {
                prop_name: strip_node(prop_value)
                for prop_name, prop_value in value.items()
                if prop_name not in COMPUTATION_FIELDS
            }
            continue
        if key == "required" and isinstance(value, list):
            stripped[key] = [
                item for item in value
                if isinstance(item, str) and item not in COMPUTATION_FIELDS
            ]
            continue
        stripped[key] = strip_node(value)
    return stripped


path = Path("generated/schema.json")
data = json.loads(path.read_text(encoding="utf-8"))
path.write_text(json.dumps(strip_node(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")
endef
export STRIP_JSON_SCHEMA_PY

define STRIP_RESOLVED_YAML_PY
from pathlib import Path

import yaml

path = Path("generated/schema.yaml")
data = yaml.safe_load(path.read_text(encoding="utf-8"))
if isinstance(data, dict):
    data.pop("imports", None)
path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding="utf-8")
endef
export STRIP_RESOLVED_YAML_PY

define STRIP_SHACL_PY
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import SH
from rdflib.term import BNode, URIRef

COMPUTATION_FIELDS = {
    "weight",
    "score",
    "total_score",
    "computed_score",
    "answer_score",
    "is_bonus",
}


def local_name(term):
    if not isinstance(term, URIRef):
        return None
    text = str(term)
    if "#" in text:
        return text.rsplit("#", 1)[1]
    return text.rstrip("/").rsplit("/", 1)[-1]


def remove_bnode_subgraph(graph, root):
    pending = [root]
    seen = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        outgoing = list(graph.triples((current, None, None)))
        incoming = list(graph.triples((None, None, current)))
        for _, _, obj in outgoing:
            if isinstance(obj, BNode):
                pending.append(obj)
        for triple in outgoing + incoming:
            graph.remove(triple)


path = Path("generated/shacl.ttl")
graph = Graph()
graph.parse(path, format="turtle")

banned_uris = {
    term
    for triple in graph
    for term in triple
    if isinstance(term, URIRef) and local_name(term) in COMPUTATION_FIELDS
}

property_shapes_to_remove = {
    shape
    for shape, _, shape_path in graph.triples((None, SH.path, None))
    if isinstance(shape, BNode)
    and isinstance(shape_path, URIRef)
    and shape_path in banned_uris
}

for shape in property_shapes_to_remove:
    remove_bnode_subgraph(graph, shape)

for triple in list(graph.triples((None, SH.defaultValue, None))):
    graph.remove(triple)

for triple in list(graph):
    if any(isinstance(term, URIRef) and term in banned_uris for term in triple):
        graph.remove(triple)

graph.serialize(destination=path, format="turtle")
endef
export STRIP_SHACL_PY

define STRIP_MODEL_PY
from pathlib import Path

from rdflib import Graph
from rdflib.term import URIRef

COMPUTATION_FIELDS = {
    "weight",
    "score",
    "total_score",
    "computed_score",
    "answer_score",
    "is_bonus",
}


def local_name(term):
    if not isinstance(term, URIRef):
        return None
    text = str(term)
    if "#" in text:
        return text.rsplit("#", 1)[1]
    return text.rstrip("/").rsplit("/", 1)[-1]


path = Path("generated/model.ttl")
graph = Graph()
graph.parse(path, format="turtle")

banned_uris = {
    term
    for triple in graph
    for term in triple
    if isinstance(term, URIRef) and local_name(term) in COMPUTATION_FIELDS
}

for triple in list(graph):
    if any(isinstance(term, URIRef) and term in banned_uris for term in triple):
        graph.remove(triple)

graph.serialize(destination=path, format="turtle")
endef
export STRIP_MODEL_PY

define GENERATE_CALCULATION_PY
import json
import re
from pathlib import Path

import yaml

ROOT = Path(".").resolve()
MODEL_ROOT = ROOT / "model"


def load_yaml(path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def module_id_for(path):
    return path.relative_to(ROOT).as_posix()[:-5]


def resolve_import_path(module_path, import_ref):
    if ":" in import_ref and not import_ref.startswith("."):
        return None
    candidate = (module_path.parent / import_ref).resolve()
    if candidate.suffix != ".yaml":
        candidate = candidate.with_suffix(".yaml")
    return candidate if candidate.exists() else None


def load_modules():
    module_paths = [MODEL_ROOT / "model.yaml"]
    module_paths.extend(sorted((MODEL_ROOT / "indicators").glob("*.yaml")))

    modules = {}
    classes = {}
    for path in module_paths:
        data = load_yaml(path)
        imports = []
        for import_ref in data.get("imports", []):
            resolved = resolve_import_path(path, import_ref)
            if resolved is not None:
                imports.append(module_id_for(resolved))

        module_classes = data.get("classes", {})
        modules[module_id_for(path)] = {
            "imports": tuple(imports),
            "classes": module_classes,
        }
        for class_name, class_def in module_classes.items():
            classes[class_name] = (module_id_for(path), class_def)

    return modules, classes


def collect_accessible_modules(module_id, modules, seen=None, allow_root_model_recursion=True):
    if seen is None:
        seen = set()
    if module_id in seen:
        return seen
    seen.add(module_id)
    if module_id == "model/model" and not allow_root_model_recursion:
        return seen
    for imported in modules[module_id]["imports"]:
        _ = collect_accessible_modules(
            imported,
            modules,
            seen,
            allow_root_model_recursion=False,
        )
    return seen


def accessible_classes(module_id, modules, classes):
    visible_modules = collect_accessible_modules(module_id, modules)
    return {
        class_name: class_def
        for class_name, (class_module, class_def) in classes.items()
        if class_module in visible_modules
    }


def parse_ifabsent(value):
    if isinstance(value, list):
        return [parse_ifabsent(item) for item in value]
    if isinstance(value, dict):
        return {key: parse_ifabsent(item) for key, item in value.items()}
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if not isinstance(value, str):
        return value
    if value == "false":
        return False
    if value == "true":
        return True
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\((.*)\)", value)
    if not match:
        return value
    kind, inner = match.groups()
    if kind == "string":
        return inner
    if kind == "float":
        return float(inner)
    if kind == "int":
        return int(inner)
    if kind == "boolean":
        return inner.lower() == "true"
    return inner


def is_subclass_of(class_name, target_name, all_classes):
    if class_name == target_name:
        return True
    seen = set()
    current = class_name
    while current not in seen:
        seen.add(current)
        class_entry = all_classes.get(current)
        if class_entry is None:
            return False
        parent = class_entry[1].get("is_a")
        if not parent:
            return False
        if parent == target_name:
            return True
        current = parent
    return False


def get_attribute_definition(class_name, attr_name, all_classes):
    seen = set()
    current = class_name
    while current and current not in seen:
        seen.add(current)
        class_entry = all_classes.get(current)
        if class_entry is None:
            return None
        class_def = class_entry[1]
        attributes = class_def.get("attributes", {})
        if attr_name in attributes:
            return attributes[attr_name]
        current = class_def.get("is_a")
    return None


def get_own_attribute_definition(class_name, attr_name, all_classes):
    class_entry = all_classes.get(class_name)
    if class_entry is None:
        return None
    return class_entry[1].get("attributes", {}).get(attr_name)


def get_attribute_value(class_name, attr_name, all_classes):
    attr_def = get_attribute_definition(class_name, attr_name, all_classes)
    if not attr_def:
        return None
    if "ifabsent" in attr_def:
        return parse_ifabsent(attr_def["ifabsent"])
    return None


def expand_union(class_name, visible_classes):
    class_def = visible_classes.get(class_name)
    if class_def is None:
        return [class_name]
    members = class_def.get("union_of")
    if not members:
        return [class_name]
    expanded = []
    for member in members:
        expanded.extend(expand_union(member, visible_classes))
    return expanded


def extract_fixed_score(class_name, all_classes):
    class_entry = all_classes.get(class_name)
    if class_entry is None:
        return None
    description = class_entry[1].get("description", "")
    match = re.search(r"fixed score\s+([0-9]+(?:\.[0-9]+)?)", description, re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_answers(question_class, visible_classes, all_classes):
    answer_attr = get_own_attribute_definition(question_class, "answer_options", all_classes)
    if not answer_attr or "range" not in answer_attr:
        return []
    answers = []
    for answer_class in expand_union(answer_attr["range"], visible_classes):
        answers.append(
            {
                "answer_id": get_attribute_value(answer_class, "id", all_classes),
                "text": get_attribute_value(answer_class, "text", all_classes),
                "score": get_attribute_value(answer_class, "score", all_classes),
            }
        )
    return answers


def extract_questions(parameter_class, visible_classes, all_classes, applicable_question_ids):
    question_attr = get_own_attribute_definition(parameter_class, "questions", all_classes)
    if not question_attr or "range" not in question_attr:
        return []
    allowed = set(applicable_question_ids or [])
    questions = []
    for question_class in expand_union(question_attr["range"], visible_classes):
        question_id = get_attribute_value(question_class, "id", all_classes)
        if allowed and question_id not in allowed:
            continue
        questions.append(
            {
                "question_id": question_id,
                "text": get_attribute_value(question_class, "text", all_classes),
                "weight": get_attribute_value(question_class, "weight", all_classes),
                "answers": extract_answers(question_class, visible_classes, all_classes),
            }
        )
    return questions


def module_import_distances(start_module_id, modules):
    distances = {start_module_id: 0}
    queue = [start_module_id]
    while queue:
        current = queue[0]
        del queue[0]
        if current == "model/model" and current != start_module_id:
            continue
        for imported in modules[current]["imports"]:
            if imported in distances:
                continue
            distances[imported] = distances[current] + 1
            queue.append(imported)
    return distances


def resolve_parameter_class(config_module_id, parameter_ref, visible_classes, modules, all_classes):
    candidates = []
    for class_name in visible_classes:
        if not is_subclass_of(class_name, "ParameterSpecification", all_classes):
            continue
        if get_attribute_value(class_name, "id", all_classes) == parameter_ref:
            candidates.append(class_name)
    if len(candidates) == 1:
        return candidates[0]
    local_candidates = [
        class_name
        for class_name in candidates
        if all_classes[class_name][0] == config_module_id
    ]
    if len(local_candidates) == 1:
        return local_candidates[0]
    distances = module_import_distances(config_module_id, modules)
    candidates.sort(
        key=lambda class_name: (
            distances.get(all_classes[class_name][0], 10**9),
            all_classes[class_name][0],
            class_name,
        )
    )
    best_distance = distances.get(all_classes[candidates[0]][0], 10**9) if candidates else 10**9
    nearest_candidates = [
        class_name
        for class_name in candidates
        if distances.get(all_classes[class_name][0], 10**9) == best_distance
    ]
    if len(nearest_candidates) == 1:
        return nearest_candidates[0]
    if not candidates:
        raise ValueError(
            f"Expected exactly one visible ParameterSpecification for {parameter_ref}, found 0"
        )
    raise ValueError(
        f"Could not disambiguate ParameterSpecification for {parameter_ref}: {', '.join(nearest_candidates)}"
    )


def extract_parameter_application_entries(config_class, visible_classes, all_classes):
    attr_def = get_attribute_definition(config_class, "parameter_applications", all_classes)
    if not attr_def:
        return []
    if "ifabsent" in attr_def:
        parsed = parse_ifabsent(attr_def["ifabsent"])
        return parsed if isinstance(parsed, list) else []
    range_name = attr_def.get("range")
    if not range_name:
        return []
    applications = []
    for application_class in expand_union(range_name, visible_classes):
        applications.append(
            {
                "parameter_ref": get_attribute_value(application_class, "parameter_ref", all_classes),
                "weight": get_attribute_value(application_class, "weight", all_classes),
                "applicable_question_ids": get_attribute_value(application_class, "applicable_questions", all_classes),
            }
        )
    return applications


def build_indicator_payload(config_class, module_id, modules, all_classes):
    visible_classes = accessible_classes(module_id, modules, all_classes)
    indicator_id = get_attribute_value(config_class, "id", all_classes)
    indicator_payload = {
        "indicator_type": get_attribute_value(config_class, "indicator_type", all_classes),
        "product_category": get_attribute_value(config_class, "product_category", all_classes),
        "parameters": [],
    }
    for application in extract_parameter_application_entries(config_class, visible_classes, all_classes):
        parameter_ref = application["parameter_ref"]
        if not parameter_ref:
            raise ValueError(f"Missing parameter_ref in configuration {config_class}")
        applicable_question_ids = application.get("applicable_question_ids") or []
        parameter_class = resolve_parameter_class(
            module_id,
            parameter_ref,
            visible_classes,
            modules,
            all_classes,
        )
        parameter_payload = {
            "parameter_ref": parameter_ref,
            "name": get_attribute_value(parameter_class, "name", all_classes),
            "description": get_attribute_value(parameter_class, "description", all_classes),
            "weight": application.get("weight"),
            "questions": extract_questions(
                parameter_class,
                visible_classes,
                all_classes,
                applicable_question_ids or None,
            ),
        }
        if applicable_question_ids:
            parameter_payload["applicable_question_ids"] = applicable_question_ids
        fixed_score = extract_fixed_score(parameter_class, all_classes)
        if fixed_score is not None:
            parameter_payload["fixed_score"] = fixed_score
        indicator_payload["parameters"].append(parameter_payload)
    return indicator_id, indicator_payload


modules, all_classes = load_modules()
model_data = load_yaml(MODEL_ROOT / "model.yaml")
indicator_configurations = {}

for class_name, (module_id, class_def) in sorted(all_classes.items()):
    if class_name == "IndicatorProductConfiguration":
        continue
    if class_def.get("abstract"):
        continue
    if not is_subclass_of(class_name, "IndicatorProductConfiguration", all_classes):
        continue
    indicator_id, payload = build_indicator_payload(class_name, module_id, modules, all_classes)
    if indicator_id:
        indicator_configurations[indicator_id] = payload

artifact = {
    "artifact_type": "calculation",
    "model_version": model_data.get("version"),
    "indicator_configurations": indicator_configurations,
}

with open("generated/calculation.json", "w", encoding="utf-8") as handle:
    json.dump(artifact, handle, indent=2, sort_keys=True)
    _ = handle.write("\n")
endef
export GENERATE_CALCULATION_PY

all: generated/schema.yaml generated/schema.json generated/shacl.ttl generated/model.ttl generated/calculation.json

generated/schema.yaml: $(MODEL_SOURCES)
	mkdir -p generated
	linkml generate yaml model/model.yaml > generated/schema.yaml || (echo "Error generating resolved YAML schema"; exit 1)
	python3 -c "$$STRIP_RESOLVED_YAML_PY"
	@echo "Generated resolved YAML schema: $$(wc -l < generated/schema.yaml) lines"

generated/schema.json: $(MODEL_SOURCES)
	mkdir -p generated
	linkml generate json-schema model/model.yaml > generated/schema.json || (echo "Error generating JSON Schema"; exit 1)
	python3 -c "$$STRIP_JSON_SCHEMA_PY"
	@echo "Generated JSON Schema: $$(wc -l < generated/schema.json) lines"

generated/shacl.ttl: $(MODEL_SOURCES) model/completeness-constraints.ttl
	mkdir -p generated
	linkml generate shacl model/model.yaml > generated/shacl.ttl || (echo "Error generating SHACL"; exit 1)
	@echo "Generated base SHACL: $$(wc -l < generated/shacl.ttl) lines"
	python3 -c "$$STRIP_SHACL_PY"
	@echo "" >> generated/shacl.ttl
	@echo "# ============================================================================" >> generated/shacl.ttl
	@echo "# COMPLETENESS CONSTRAINTS" >> generated/shacl.ttl
	@echo "# ============================================================================" >> generated/shacl.ttl
	cat model/completeness-constraints.ttl | grep -v "^@prefix" >> generated/shacl.ttl
	@echo "Merged completeness constraints into SHACL: $$(wc -l < generated/shacl.ttl) lines"

generated/model.ttl: $(MODEL_SOURCES)
	mkdir -p generated
	# OWL generation produces Turtle format, so name it .ttl
	linkml generate owl model/model.yaml --no-metaclasses > generated/model.ttl 2> generated/model-owl.log || \
		(echo "Error generating OWL, trying without imports..."; \
		 linkml generate owl model/model.yaml --no-metaclasses --no-imports > generated/model.ttl 2>> generated/model-owl.log || \
		 (echo "OWL generation failed, creating placeholder"; \
		  echo "# OWL generation failed - check model syntax" > generated/model.ttl))
	python3 -c "$$STRIP_MODEL_PY"
	@echo "Generated OWL: $$(wc -l < generated/model.ttl) lines"

generated/calculation.json: $(MODEL_SOURCES)
	mkdir -p generated
	python3 -c "$$GENERATE_CALCULATION_PY"
	@echo "Generated calculation artifact: $$(wc -l < generated/calculation.json) lines"

clean:
	rm -rf generated/*.json generated/*.ttl generated/*.yaml

.PHONY: all clean
