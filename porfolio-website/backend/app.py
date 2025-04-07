import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import base64

# Ensure the app name matches potentially how Render runs it (if it looks for 'app')
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    # Using a 'with' statement ensures the connection is closed automatically
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            # Projects Table
            cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                title TEXT,
                                desc TEXT,
                                clickable BLOB,
                                clickable_type TEXT)''')

            # Blogs Table
            cursor.execute('''CREATE TABLE IF NOT EXISTS blogs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                title TEXT,
                                desc TEXT,
                                img BLOB)''')

            # ★★★ NEW Resources Table ★★★
            cursor.execute('''CREATE TABLE IF NOT EXISTS resources (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                title TEXT NOT NULL,
                                description TEXT,
                                pdf_filename TEXT UNIQUE NOT NULL)''') # Added NOT NULL constraints and UNIQUE for filename

            conn.commit() # Commit changes
            print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")


@app.route('/get_projects', methods=['GET'])
def get_projects():
    """Fetches all projects from the database."""
    try:
        with sqlite3.connect('database.db') as conn:
            conn.row_factory = sqlite3.Row # Return rows that behave like dictionaries
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, desc, clickable, clickable_type FROM projects ORDER BY id DESC") # Order by newest first
            projects_raw = cursor.fetchall()

            projects = []
            for project in projects_raw:
                # Convert row to dict, handle potential None for clickable BLOB
                project_dict = dict(project)
                if project_dict['clickable']:
                    project_dict['clickable'] = base64.b64encode(project_dict['clickable']).decode('utf-8')
                else:
                     project_dict['clickable'] = None # Ensure None if blob is NULL

                projects.append(project_dict)

            return jsonify(projects)
    except sqlite3.Error as e:
        print(f"Database error fetching projects: {e}")
        return jsonify({"error": "Database error fetching projects"}), 500

@app.route('/add_project', methods=['POST'])
def add_project():
    """Adds a new project to the database."""
    data = request.json
    title = data.get('title')
    desc = data.get('desc')
    clickable_data = data.get('clickable')
    clickable_type = data.get('clickable_type')

    if not all([title, desc, clickable_data, clickable_type]):
         return jsonify({'error': 'Missing required fields for project'}), 400

    # Handle clickable content (potential Base64)
    clickable_binary = None
    if isinstance(clickable_data, str):
        try:
            # Try decoding if it looks like Base64 (more robust check might be needed)
            if len(clickable_data) % 4 == 0 and clickable_type == 'image': # Basic check
                 clickable_binary = base64.b64decode(clickable_data, validate=True)
            else: # Assume it's a URL or other text
                 clickable_binary = clickable_data.encode('utf-8')
        except (base64.binascii.Error, ValueError):
            # If decoding fails, treat as plain text/URL
            print("Warning: clickable data looked like base64 but failed decoding. Storing as text.")
            clickable_binary = clickable_data.encode('utf-8')
    elif clickable_data is not None: # Handle cases where it might not be a string (less likely via JSON)
        clickable_binary = str(clickable_data).encode('utf-8')

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO projects (title, desc, clickable, clickable_type) VALUES (?, ?, ?, ?)",
                           (title, desc, clickable_binary, clickable_type))
            conn.commit()
            return jsonify({'message': 'Project added successfully'}), 201 # 201 Created
    except sqlite3.Error as e:
        print(f"Database error adding project: {e}")
        # conn.rollback() # 'with' statement handles rollback on exception
        return jsonify({'error': 'Database error adding project'}), 500

@app.route('/show_blogs', methods=['GET'])
def show_blogs():
    """Fetches all blog posts from the database."""
    try:
        with sqlite3.connect('database.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, desc, img FROM blogs ORDER BY id DESC") # Order by newest first
            blogs_raw = cursor.fetchall()

            blogs = []
            for blog in blogs_raw:
                blog_dict = dict(blog)
                # Handle potential None for img BLOB
                if blog_dict['img']:
                    blog_dict['img'] = base64.b64encode(blog_dict['img']).decode('utf-8')
                else:
                    blog_dict['img'] = None # Ensure None if blob is NULL
                blogs.append(blog_dict)

            return jsonify(blogs)
    except sqlite3.Error as e:
        print(f"Database error fetching blogs: {e}")
        return jsonify({"error": "Database error fetching blogs"}), 500

@app.route('/add_blog', methods=['POST'])
def add_blog():
    """Adds a new blog post to the database."""
    data = request.json
    title = data.get('title')
    desc = data.get('desc')
    img_data = data.get('img') # Optional image data

    if not title or not desc:
         return jsonify({'error': 'Missing title or description for blog post'}), 400

    # Handle image content (potential Base64)
    img_binary = None
    if isinstance(img_data, str) and img_data.strip(): # Check if string and not empty
        try:
            # Basic check if it might be base64 data URI e.g., data:image/jpeg;base64,...
            if img_data.startswith('data:image') and ';base64,' in img_data:
                header, encoded = img_data.split(';base64,', 1)
                img_binary = base64.b64decode(encoded, validate=True)
            # Check if maybe just base64 string without header
            elif len(img_data) > 100 and len(img_data) % 4 == 0: # Heuristic
                img_binary = base64.b64decode(img_data, validate=True)
            else:
                # Assuming it's a URL or non-base64 string, store as text (though BLOB isn't ideal for URLs)
                print("Warning: Blog image data provided but doesn't look like base64. Storing as text.")
                img_binary = img_data.encode('utf-8')
        except (base64.binascii.Error, ValueError):
             print("Warning: Blog image data failed base64 decoding. Storing as text.")
             img_binary = img_data.encode('utf-8')

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO blogs (title, desc, img) VALUES (?, ?, ?)",
                           (title, desc, img_binary))
            conn.commit()
            return jsonify({'message': 'Blog added successfully'}), 201 # 201 Created
    except sqlite3.Error as e:
        print(f"Database error adding blog: {e}")
        return jsonify({'error': 'Database error adding blog'}), 500

# ★★★ START: New Endpoints for Resources ★★★

@app.route('/get_resources', methods=['GET'])
def get_resources():
    """Fetches all resources from the database."""
    try:
        with sqlite3.connect('database.db') as conn:
            conn.row_factory = sqlite3.Row # Return rows that behave like dictionaries
            cursor = conn.cursor()
            # Fetch resources, ordered by title alphabetically
            cursor.execute("SELECT id, title, description, pdf_filename FROM resources ORDER BY title COLLATE NOCASE")
            resources_raw = cursor.fetchall()
            # Convert Row objects to standard dictionaries
            resources = [dict(row) for row in resources_raw]
            return jsonify(resources)
    except sqlite3.Error as e:
        print(f"Database error fetching resources: {e}")
        return jsonify({"error": "Database error fetching resources"}), 500

@app.route('/add_resource', methods=['POST'])
def add_resource():
    """Adds a new resource (linking to a PDF filename) to the database."""
    data = request.json
    title = data.get('title')
    description = data.get('description')
    pdf_filename = data.get('pdf_filename') # Expecting just the filename string

    # Validate required fields
    if not title or not description or not pdf_filename:
        return jsonify({'error': 'Missing required fields (title, description, pdf_filename)'}), 400

    # Optional: Basic validation for filename format
    if not isinstance(pdf_filename, str) or not pdf_filename.lower().endswith('.pdf'):
         return jsonify({'error': 'Invalid pdf_filename format. Must be a string ending in .pdf'}), 400

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            # Insert data into the resources table
            cursor.execute("INSERT INTO resources (title, description, pdf_filename) VALUES (?, ?, ?)",
                           (title, description, pdf_filename))
            conn.commit()
            # Return success message with 201 Created status
            return jsonify({'message': 'Resource added successfully'}), 201
    except sqlite3.IntegrityError: # Specific error for UNIQUE constraint violation
         # Rollback is handled automatically by 'with' statement on exception
         print(f"Integrity Error: Failed to add resource. Filename '{pdf_filename}' might already exist.")
         return jsonify({'error': f'Failed to add resource. Filename "{pdf_filename}" already exists.'}), 409 # 409 Conflict
    except sqlite3.Error as e:
        # General database error
        print(f"Database error adding resource: {e}")
        return jsonify({'error': 'Database error adding resource'}), 500

# ★★★ END: New Endpoints for Resources ★★★


if __name__ == '__main__':
    print("Initializing database...")
    init_db() # Ensure tables exist before starting app
    print("Starting Flask server...")
    # Recommended host/port for Render
    # Render sets the PORT environment variable, use it if available, otherwise default
    port = int(os.environ.get('PORT', 10000)) # Need to import os at the top
    app.run(host='0.0.0.0', port=port)