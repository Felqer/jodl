#!/bin/bash /Users/FWerpers/.virtualenvs/jodlHack/bin/fwpy
# coding: utf-8

import googlemaps
import ConfigParser
import json

# API key stored in config file
config = ConfigParser.RawConfigParser()
config.read('config.cfg')
API_key = config.get('Credentials', 'API_key')

gmaps = googlemaps.Client(key=API_key)

def get_coords(address):
	r = gmaps.geocode(address)
	location = r[0]['geometry']['location']
	lat = location['lat']
	lng = location['lng']
	return((lat, lng))

def get_address(coords):
	r = gmaps.reverse_geocode(coords)
	addr = r[0]['formatted_address']
	return addr

def get_jodl_location(coords, acc):
	r = gmaps.reverse_geocode(coords)
	city = r[5]['address_components'][0]['short_name']
	country = r[-1]['address_components'][0]['short_name']

	lat = coords[0]
	lng = coords[1]

	loc = {
		'loc_accuracy': acc,
		'city': city,
		'loc_coordinates': {
		'lat': lat,
		'lng': lng
		},
		'country': country
	}
	return loc

