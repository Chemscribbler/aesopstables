#!/bin/bash

flask db upgrade

gunicorn --bind=0.0.0.0:5000 aesopstables:app