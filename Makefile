export DJANGO_SETTINGS_MODULE?=ynr.settings.sopn_testing

.PHONY: migrate-db
migrate-db:
	python manage.py migrate

.PHONY: test-sopns
test-sopns: migrate-db
	python manage.py sopn_tooling_write_baseline
	python manage.py sopn_tooling_compare_raw_people

.PHONY: download-sopns
download-sopns:
	python manage.py migrate --no-input
	python manage.py sopn_tooling_create_official_documents

.PHONY: populate-sopn-testing-database
populate-sopn-testing-database: migrate-db
	python manage.py candidates_import_from_live_site

.PHONY: delete-test-sopns
delete-test-sopns:
	python manage.py sopn_tooling_clear_existing_objects
	rm -rf ./ynr/media/sopn_testing/
