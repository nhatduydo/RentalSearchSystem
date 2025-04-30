#!/bin/bash
python -m gunicorn SystemForSearchingAccommodations.wsgi:application 