SHELL := /bin/bash

MPLBACKEND?=Agg
export MPLBACKEND

MODULES=starfish data_formatting_examples

DOCKER_IMAGE?=spacetx/starfish
DOCKER_BUILD?=1

VERSION=$(shell sh -c "git describe --exact --dirty 2> /dev/null")

define print_help
    @printf "    %-28s   $(2)\n" $(1)
endef

define create_venv
    if [[ "$(TRAVIS)" = "" ]]; then \
        python -m venv $(1); \
    else \
        virtualenv -p $$(which python) $(1); \
    fi
endef


all:	fast

### UNIT #####################################################
#
fast:	lint mypy fast-test docs-html

lint:   lint-non-init lint-init

lint-non-init:
	flake8 --ignore 'E252, E301, E302, E305, E401, W503, E731, F811' --exclude='*__init__.py' $(MODULES)

lint-init:
	flake8 --ignore 'E252, E301, E302, E305, E401, F401, W503, E731, F811' --filename='*__init__.py' $(MODULES)

test:
	pytest -v -n 8 --cov starfish

fast-test:
	pytest -v -n 8 --cov starfish -m 'not slow'

slow-test:
	pytest -v -n 8 --cov starfish -m 'slow'

mypy:
	mypy --ignore-missing-imports $(MODULES)

help-unit:
	$(call print_help, all, alias for fast)

.PHONY: all fast lint lint-non-init lint-init test mypy help-unit
#
##############################################################

### DOCS #####################################################
#
docs-%:
	make -C docs $*

help-docs:
	$(call print_help, docs-TASK, alias for 'make TASK' in the docs subdirectory)

.PHONY: help-docs
#
##############################################################

### REQUIREMENTS #############################################
#
check-requirements:
	if [[ $$(git status --porcelain REQUIREMENTS*) ]]; then \
	    echo "Modifications found in REQUIREMENTS files"; exit 2; \
	fi

refresh-all-requirements:
	@echo -n '' >| REQUIREMENTS-STRICT.txt
	@if [ $$(uname -s) == "Darwin" ]; then sleep 1; fi  # this is require because Darwin HFS+ only has second-resolution for timestamps.
	@touch REQUIREMENTS.txt
	@$(MAKE) REQUIREMENTS-STRICT.txt

REQUIREMENTS-STRICT.txt : REQUIREMENTS.txt
	[ ! -e .$<-env ] || exit 1
	$(call create_venv, .$<-env)
	.$<-env/bin/pip install -r $@
	.$<-env/bin/pip install -r $<
	echo "# You should not edit this file directly.  Instead, you should edit one of the following files ($^) and run make $@" >| $@
	.$<-env/bin/pip freeze >> $@
	cp -f $@ starfish/REQUIREMENTS-STRICT.txt
	rm -rf .$<-env

help-requirements:
	$(call print_help, refresh_all_requirements, regenerate requirements files)
	$(call print_help, check_requirements, fail if requirements files have been modified)

.PHONY: refresh_all_requirements starfish/REQUIREMENTS-STRICT.txt
#
##############################################################

### INTEGRATION ##############################################
#
include notebooks/subdir.mk

slow: fast run-notebooks docker

docker:
	docker build -t $(DOCKER_IMAGE) .
	docker run -ti --rm $(DOCKER_IMAGE) build --fov-count 1 --primary-image-dimensions '{"z": 1}' /tmp/

help-integration:
	$(call print_help, slow, alias for 'fast run-notebooks docker')
	$(call print_help, run-notebooks, run all files matching 'notebooks/py/*.py')
	$(call print_help, docker, build docker and run a simple container)

.PHONY: slow docker
#
##############################################################

### INSTALL ##################################################
#
install-dev:
	pip install --force-reinstall --upgrade -r REQUIREMENTS-STRICT.txt
	pip install -e .
	pip install -r REQUIREMENTS-CI.txt
	pip freeze

install-src:
	pip install --force-reinstall --upgrade -e .
	pip freeze

install-released-notebooks-support:
	pip install starfish
	pip install -r REQUIREMENTS-CI.txt
	pip freeze

help-install:
	$(call print_help, install-dev, pip install from the current directory with pinned requirements and tooling for CI)
	$(call print_help, install-src, pip install from the current directory)
	$(call print_help, install-released-notebooks, pip install tooling to run notebooks against the released version of starfish)

.PHONY: install-dev install-src install-released-notebooks-support help-install
#
###############################################################

### Deployment ################################################
#
# General release steps:
# --------------------------------------------------------------
#  (0) Check out the latest version of the branch for releasing.
#
#  (1) `make release-changelog` to print a suggested update to
#      CHANGELOG.md. Replace "XXX" with your intended tag.
#
#  (2) Commit all files and remove any untracked files.
#      `git status` should show nothing.
#
#  (3) Create an annotated tag (with -a or -s)
#
#  (4) Run `make release-prep` which:
#     - checks the tag
#     - creates a virtualenv
#     - builds and installs the sdist
#
#  (5) `make release-verify` which:
#     - runs tests
#     - builds docker
#  (6a) if everything succeeds: run `make release-upload`
#       and execute the commands in order.
#  (6b) if anything goes wrong, rollback the various steps:
#     - delete on docker hub
#     - delete local docker image
#     - delete tag locally
#     - make clean

# private: assert a clean tag on the current commit
release-check:
	@if test -z "$(VERSION)"; then                    \
		echo VERSION is not set.;                 \
		echo Please create a git tag;             \
		exit 100;                                 \
	elif [[ "$(VERSION)" == *"dirty"* ]] ; then       \
		echo VERSION is dirty.;                   \
		echo Please commit all files and re-tag.; \
		exit 101;                                 \
	else                                              \
		echo "===============================";   \
		echo "Releasing version: $(VERSION)";     \
		echo "===============================";   \
	fi;

# private: assert no existing release-env directory
release-ready:
	@if test -e release-env ; then                    \
		echo "Previous release found.";           \
		echo "Run 'make clean'";                  \
		exit 103;                                 \
	fi;

# private: create a virtualenv for testing the release
release-env: release-env/bin/activate release-env/bin/make_shell

# private: call virtualenv and pip install
release-env/bin/activate:
	$(call create_venv, release-env)
	release-env/bin/pip install -r REQUIREMENTS-CI.txt
	touch release-env/bin/activate

# private: create make_shell for activating the virtualenv below
release-env/bin/make_shell:
	echo '#!/bin/bash' > $@
	echo 'source release-env/bin/activate' >> $@
	echo 'bash "$$@"' >> $@
	chmod a+x $@

# public: print a changelog to stdout
release-changelog:
	@if test -n "$(VERSION)"; then                    \
		echo VERSION is set to $(VERSION)         \
		echo Create your changelog before tagging.\
		exit 102;                                 \
	fi;
	@echo "##" "[XXX]" - $(shell sh -c "date +'%Y-%m-%d'")
	@git log $(shell sh -c "git describe --tags --abbrev=0")..HEAD --pretty=format:"- %s"
	@echo; cat CHANGELOG.md; echo "[XXX]: https://github.com/spacetx/starfish/releases/tag/XXX"

# public: generate a tag from the current commit & changelog
release-tag:
	@if test -n "$(TAG)"; then                     \
		echo TAG is not set.;                  \
		echo Use 'make TAG=x.y.z release-tag'; \
		exit 104;                              \
	fi;

# public: generate the release build
release-prep: release-check release-ready release-env
	release-env/bin/python setup.py clean
	release-env/bin/python setup.py sdist
	release-env/bin/pip install dist/starfish-$(VERSION).tar.gz

# public: run tests on the current release build
release-verify: export SHELL=release-env/bin/make_shell
release-verify: release-check slow release-docker

# public: tag the docker images
release-docker: release-check
	docker tag $(DOCKER_IMAGE) $(DOCKER_IMAGE):$(VERSION)
	docker tag $(DOCKER_IMAGE) $(DOCKER_IMAGE):$(VERSION)-$(DOCKER_BUILD)

# public: print commands for uploading artifacts
release-upload: release-check
	@printf '\n# Please execute the following steps\n'
	@echo git push origin $(VERSION)
	@echo docker push $(DOCKER_IMAGE)
	@echo docker push $(DOCKER_IMAGE):$(VERSION)
	@echo docker push $(DOCKER_IMAGE):$(VERSION)-$(DOCKER_BUILD)
	@echo twine upload dist/starfish-$(VERSION).tar.gz

clean:
	rm -rf release-env
	rm -rf starfish.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .eggs
	rm -f .cover*

help-deployment:
	$(call print_help, release-prep, Builds and installs the current tagged version)
	$(call print_help, release-verify, Runs tests on the tagged version)
	$(call print_help, release-upload, Prints commands for uploading release artifacts)
	$(call print_help, clean, Deletes build-related directories)

.PHONY: clean release-prep release-verify release-upload release-check
#
###############################################################
help: help-main help-parts
help-main:
	@echo Main starfish make targets:
	@echo =======================================================================================
	$(call print_help, help, print this text)
help-parts: help-unit help-docs help-requirements help-integration help-install help-deployment
	@echo =======================================================================================
	@echo Default: all

.PHONY: help help-unit help-requirements help-integration help-install help-release
