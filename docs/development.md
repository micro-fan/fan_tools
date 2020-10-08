
## Local testing

First run `tox -e py38-django31 -- --keep-db` to leave postgresql server container running.

After that you can run any tests you want fast with `--skip-docker` flag.
Eg. `tox -e py38-django31 django_tests/test_django.py -- --skip-docker`
