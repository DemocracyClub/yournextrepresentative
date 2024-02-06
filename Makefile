export DJANGO_SETTINGS_MODULE?=ynr.settings.sopn_testing


.PHONY: sopn-runserver
sopn-runserver:
	python manage.py runserver

.PHONY: sopn-shell
sopn-shell:
	python manage.py shell_plus

.PHONY: migrate-db
migrate-db:
	python manage.py migrate

.PHONY: test-sopns
test-sopns: migrate-db
	python manage.py sopn_tooling_compare_raw_people --election-slugs= --ballot= --date 2021-05-06

.PHONY: download-sopns
download-sopns:
	python manage.py migrate --no-input
	python manage.py sopn_tooling_create_official_documents --election-slugs= --date 2021-05-06

.PHONY: populate-sopn-testing-database
populate-sopn-testing-database: migrate-db
	python manage.py candidates_import_from_live_site

.PHONY: delete-test-sopns
delete-test-sopns:
	python manage.py sopn_tooling_clear_existing_objects
	rm -rf ./ynr/media/sopn_testing/

.PHONY: create-baseline-file
create-baseline-file:
	python manage.py sopn_tooling_write_baseline

.PHONY: copy-baseline-file
copy-baseline-file:
	cp ynr/apps/sopn_parsing/tests/data/sopn_baseline.json ynr/apps/sopn_parsing/tests/data/sopn_baseline_copy.json

.PHONY: prod-import-sopns
prod-import-sopns:
	cd deploy; \
	ansible-playbook import_sopns.yml
