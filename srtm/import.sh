#!/usr/bin/env bash

# raster2pgsql -a -e -s 4326 -t 100x100 unzipped/*.hgt elevations | psql
raster2pgsql -d -M -C -I -F -s 4326 -t 25x25 unzipped/*.hgt elevation | psql -d ogn
