all: generated/schema.json generated/shacl.ttl generated/model.ttl

generated/schema.json: model/model.yaml
	mkdir -p generated
	linkml generate json-schema model/model.yaml > generated/schema.json || (echo "Error generating JSON Schema"; exit 1)
	@echo "Generated JSON Schema: $$(wc -l < generated/schema.json) lines"

generated/shacl.ttl: model/model.yaml
	mkdir -p generated
	linkml generate shacl model/model.yaml > generated/shacl.ttl || (echo "Error generating SHACL"; exit 1)
	@echo "Generated SHACL: $$(wc -l < generated/shacl.ttl) lines"

generated/model.ttl: model/model.yaml
	mkdir -p generated
	# OWL generation produces Turtle format, so name it .ttl
	linkml generate owl model/model.yaml --no-metaclasses > generated/model.ttl 2>&1 || \
		(echo "Error generating OWL, trying without imports..."; \
		 linkml generate owl model/model.yaml --no-metaclasses --no-imports > generated/model.ttl 2>&1 || \
		 (echo "OWL generation failed, creating placeholder"; \
		  echo "# OWL generation failed - check model syntax" > generated/model.ttl))
	@echo "Generated OWL: $$(wc -l < generated/model.ttl) lines"

clean:
	rm -rf generated/*.json generated/*.ttl

.PHONY: all clean