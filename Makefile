
COLLECTION_NAMESPACE=saiello
COLLECTION_NAME=kafka
COLLECTION_VERSION=$(shell yq .version galaxy.yml)
COLLECTION_BUILD=$(COLLECTION_NAMESPACE)-$(COLLECTION_NAME)-$(COLLECTION_VERSION).tar.gz


publish: build
	venv/bin/ansible-galaxy collection publish --token $${ANSIBLE_GALAXY_TOKEN} $(COLLECTION_BUILD) 

build: $(COLLECTION_BUILD)

clean: 
	rm $(COLLECTION_BUILD)

clean-all:
	rm -f $(COLLECTION_NAMESPACE)-$(COLLECTION_NAME)-*.tar.gz

$(COLLECTION_BUILD):
	venv/bin/ansible-galaxy collection build .

version:
	@echo $(COLLECTION_VERSION)


SCENARIO ?= cluster
SCENARIO_INVENTORY = ~/.cache/molecule/$(COLLECTION_NAME)/$(SCENARIO)/inventory/ansible_inventory.yml

print_inventory:
	cat $(SCENARIO_INVENTORY)

ansible_check:
	ansible-playbook -i $(SCENARIO_INVENTORY) playbooks/service_check.yml -v