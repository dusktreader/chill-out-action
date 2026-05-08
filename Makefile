VERSION_SCRIPT := uv run --script scripts/version.py

default: help


## ==== Lint ===========================================================================================================

lint: lint-yaml ## Run all linters

lint-yaml: ## Lint all YAML files with yamllint
	uvx yamllint -c .yamllint.yaml action.yml .github/


## ==== Version Management =============================================================================================

bump/%: ## Bump the version in action.yml (major | minor | patch)
	$(VERSION_SCRIPT) bump --type $(notdir $@)

publish: ## Tag, push, and create the GitHub release from CHANGELOG.md
	$(VERSION_SCRIPT) publish

publish-dry-run: ## Show what publish would do without making any changes
	$(VERSION_SCRIPT) publish --dry-run


## ==== Helpers ========================================================================================================

help: ## Show this help message
	@awk "$$PRINT_HELP_PREAMBLE" $(MAKEFILE_LIST)


# ..... Make configuration .............................................................................................

.ONESHELL:
SHELL := /bin/bash
.PHONY: default \
	lint lint-yaml \
	bump/% publish publish-dry-run \
	help


# ..... Color table for pretty printing ................................................................................

RED    := \033[31m
GREEN  := \033[32m
YELLOW := \033[33m
BLUE   := \033[34m
TEAL   := \033[36m
GRAY   := \033[90m
CLEAR  := \033[0m
ITALIC := \033[3m


# ..... Help printer ...................................................................................................

define PRINT_HELP_PREAMBLE
BEGIN {
	print "Usage: $(YELLOW)make <target>$(CLEAR)"
	print
	print "Targets:"
}
/^## =+ .+( =+)?/ {
    s = $$0
    sub(/^## =+ /, "", s)
    sub(/ =+/, "", s)
	printf("\n  %s:\n", s)
}
/^## -+ .+( -+)?/ {
    s = $$0
    sub(/^## -+ /, "", s)
    sub(/ -+/, "", s)
	printf("\n    $(TEAL)> %s$(CLEAR)\n", s)
}
/^[$$()% 0-9a-zA-Z_\/-]+(\\:[$$()% 0-9a-zA-Z_\/-]+)*:.*?##/ {
    t = $$0
    sub(/:.*/, "", t)
    h = $$0
    sub(/.?*##/, "", h)
    printf("    $(YELLOW)%-19s$(CLEAR) $(GRAY)$(ITALIC)%s$(CLEAR)\n", t, h)
}
endef
export PRINT_HELP_PREAMBLE
