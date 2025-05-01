#!/bin/bash
cd accommodationSearchApp
python -m gunicorn accommodationSearchApp.wsgi:application --bind 0.0.0.0:$PORT 