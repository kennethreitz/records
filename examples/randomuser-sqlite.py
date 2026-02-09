#!/usr/bin/env python3
# coding: utf-8

import json
import requests
import records

# Fetch random user data from randomuser.me API
response = requests.get('http://api.randomuser.me/0.6/?nat=us&results=10')
user_data = response.json()['results']

# Database connection string
DATABASE_URL = 'sqlite:///users.db'

# Initialize the database
db = records.Database(DATABASE_URL)

# Create the 'persons' table
db.query('DROP TABLE IF EXISTS persons')
db.query('CREATE TABLE persons (key INTEGER PRIMARY KEY, fname TEXT, lname TEXT, email TEXT)')

# Insert user data into the 'persons' table
for record in user_data:
    user = record['user']
    key = user['registered']
    fname = user['name']['first']
    lname = user['name']['last']
    email = user['email']
    db.query(
        'INSERT INTO persons (key, fname, lname, email) VALUES (:key, :fname, :lname, :email)',
        key=key, fname=fname, lname=lname, email=email
    )

# Retrieve and print the contents of the 'persons' table as CSV
rows = db.query('SELECT * FROM persons')
print(rows.export('csv'))
