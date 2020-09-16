SHELL := /bin/bash

env:
	( \
       python3 -m venv env; \
       . env/bin/activate; \
       pip install -r requirements.txt; \
    )
threads:
	( \
       . env/bin/activate; \
       python3 app/main.py; \
    )
	
async:
	( \
       . env/bin/activate; \
       python3 app/main_async.py; \
    )
