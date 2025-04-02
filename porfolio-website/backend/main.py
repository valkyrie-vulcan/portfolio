from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import base64

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        desc TEXT,
                        clickable BLOB,
                        clickable_type TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS blogs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        desc TEXT,
                        img BLOB)''')
    conn.commit()
    conn.close()

@app.route('/get_projects', methods=['GET'])
def get_projects():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, desc, clickable, clickable_type FROM projects")
    projects_raw = cursor.fetchall()
    conn.close()
    
    # Convert to a list of dictionaries and handle binary data
    projects = []
    for project in projects_raw:
        project_dict = {
            'id': project[0],
            'title': project[1],
            'desc': project[2],
            'clickable': base64.b64encode(project[3]).decode('utf-8') if project[3] else None,
            'clickable_type': project[4]
        }
        projects.append(project_dict)
    
    return jsonify(projects)

@app.route('/add_project', methods=['POST'])
def add_project():
    data = request.json
    title = data.get('title')
    desc = data.get('desc')
    
    # Handle clickable content
    clickable_data = data.get('clickable')
    if isinstance(clickable_data, str):
        # If it's a base64 string, decode it
        try:
            clickable = base64.b64decode(clickable_data)
        except:
            # If not valid base64, just encode the string
            clickable = clickable_data.encode('utf-8')
    else:
        clickable = clickable_data
    
    clickable_type = data.get('clickable_type')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO projects (title, desc, clickable, clickable_type) VALUES (?, ?, ?, ?)",
                   (title, desc, clickable, clickable_type))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Project added successfully'})

@app.route('/show_blogs', methods=['GET'])
def show_blogs():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, desc, img FROM blogs")
    blogs_raw = cursor.fetchall()
    conn.close()
    
    # Convert to a list of dictionaries and handle binary data
    blogs = []
    for blog in blogs_raw:
        blog_dict = {
            'id': blog[0],
            'title': blog[1],
            'desc': blog[2],
            'img': base64.b64encode(blog[3]).decode('utf-8') if blog[3] else None
        }
        blogs.append(blog_dict)
    
    return jsonify(blogs)

@app.route('/add_blog', methods=['POST'])
def add_blog():
    data = request.json
    title = data.get('title')
    desc = data.get('desc')
    
    # Handle image content
    img_data = data.get('img')
    if isinstance(img_data, str):
        # If it's a base64 string, decode it
        try:
            img = base64.b64decode(img_data)
        except:
            # If not valid base64, just encode the string
            img = img_data.encode('utf-8')
    else:
        img = img_data
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO blogs (title, desc, img) VALUES (?, ?, ?)", 
                   (title, desc, img))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Blog added successfully'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)