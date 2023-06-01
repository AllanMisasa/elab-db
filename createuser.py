from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3

# Open a connection to the SQLite database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Execute the query to insert a new row into the students table
cursor.execute(
    "INSERT INTO students (username, salt, password) VALUES (?, ?, ?)",
    ("csjo49211", "", ""),
)

# Commit the changes and close the database connection
conn.commit()
cursor.close()
conn.close()