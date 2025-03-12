# Check if python3 is available, else fallback to python
PYTHON = python3
ifeq ($(shell command -v python3),)
  PYTHON = python
endif

# command: make load-all-fixtures
load-all-fixtures:
	$(PYTHON) manage.py loaddata categories_fixture.json
	$(PYTHON) manage.py loaddata subcategories_fixture.json
	for i in $$(seq 1 9); do \
		$(PYTHON) manage.py loaddata knowledge_fixtures/knowledge_fixture_$$i.json; \
		$(PYTHON) manage.py loaddata knowledge_content_fixtures/knowledgecontent_fixture_$$i.json; \
	done