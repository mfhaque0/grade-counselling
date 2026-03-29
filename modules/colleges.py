import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database/colleges.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_colleges(limit=None):
    conn = get_db_connection()
    query = 'SELECT * FROM colleges ORDER BY id ASC'
    if limit: query += f' LIMIT {limit}'
    colleges = conn.execute(query).fetchall()
    conn.close()
    return colleges

def get_college_by_id(college_id):
    conn = get_db_connection()
    college = conn.execute('SELECT * FROM colleges WHERE id = ?', (college_id,)).fetchone()
    conn.close()
    return college