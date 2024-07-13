import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

class DatabaseError(Exception):
    pass

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance.init_pool()
            return cls._instance

    def init_pool(self, db_name='gym_database.db', pool_size=5):
        self.db_name = db_name
        self.pool = [sqlite3.connect(db_name) for _ in range(pool_size)]
        self.available = threading.Semaphore(pool_size)
        self.create_tables()

    @contextmanager
    def get_connection(self):
        self.available.acquire()
        connection = self.pool.pop()
        try:
            yield connection
        finally:
            self.pool.append(connection)
            self.available.release()

    def execute_query(self, query, parameters=(), fetch=False):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                conn.commit()
                if fetch:
                    return cursor.fetchall()
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Query execution failed: {e}")

    def fetch_one(self, query, parameters=()):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                return cursor.fetchone()
            except sqlite3.Error as e:
                raise DatabaseError(f"Fetch one failed: {e}")

    def fetch_all(self, query, parameters=()):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                return cursor.fetchall()
            except sqlite3.Error as e:
                raise DatabaseError(f"Fetch all failed: {e}")

    def create_tables(self):
        queries = [
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                name TEXT,
                barcode TEXT UNIQUE,
                plan TEXT,
                start_date TEXT,
                end_date TEXT,
                last_visit TEXT,
                visits INTEGER DEFAULT 0,
                phone TEXT,
                email TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                duration INTEGER,
                price REAL
            )''',
            '''CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY,
                member_id INTEGER,
                visit_date TEXT,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY,
                name TEXT,
                status TEXT,
                last_maintenance TEXT
            )'''
        ]
        for query in queries:
            self.execute_query(query)

    def add_user(self, username, password, role):
        query = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"
        self.execute_query(query, (username, password, role))

    def get_user(self, username):
        query = "SELECT * FROM users WHERE username = ?"
        return self.fetch_one(query, (username,))

    def add_member(self, name, barcode, plan, start_date, end_date, phone, email):
        query = """INSERT INTO members (name, barcode, plan, start_date, end_date, phone, email) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self.execute_query(query, (name, barcode, plan, start_date, end_date, phone, email))

    def update_member(self, member_id, name, plan, phone, email):
        query = """UPDATE members SET name = ?, plan = ?, phone = ?, email = ? 
                   WHERE id = ?"""
        self.execute_query(query, (name, plan, phone, email, member_id))

    def delete_member(self, member_id):
        query = "DELETE FROM members WHERE id = ?"
        self.execute_query(query, (member_id,))

    def add_plan(self, name, duration, price):
        query = "INSERT INTO plans (name, duration, price) VALUES (?, ?, ?)"
        self.execute_query(query, (name, duration, price))

    def update_plan(self, plan_id, name, duration, price):
        query = "UPDATE plans SET name = ?, duration = ?, price = ? WHERE id = ?"
        self.execute_query(query, (name, duration, price, plan_id))

    def delete_plan(self, plan_id):
        query = "DELETE FROM plans WHERE id = ?"
        self.execute_query(query, (plan_id,))

    def record_visit(self, member_id, visit_date):
        query = "INSERT INTO visits (member_id, visit_date) VALUES (?, ?)"
        self.execute_query(query, (member_id, visit_date))

    def get_active_members_count(self):
        query = "SELECT COUNT(*) FROM members WHERE end_date >= date('now')"
        return self.fetch_one(query)[0]

    def get_total_members_count(self):
        query = "SELECT COUNT(*) FROM members"
        return self.fetch_one(query)[0]

    def get_revenue_by_plan(self):
        query = """
            SELECT p.name, COUNT(m.id) as member_count, SUM(p.price) as total_revenue
            FROM members m
            JOIN plans p ON m.plan = p.name
            GROUP BY p.name
        """
        return self.fetch_all(query)

    def get_visits_last_30_days(self):
        query = """
            SELECT date(visit_date) as visit_day, COUNT(*) as visit_count
            FROM visits
            WHERE visit_date >= date('now', '-30 days')
            GROUP BY visit_day
            ORDER BY visit_day
        """
        return self.fetch_all(query)

    def add_equipment(self, name, status):
        query = "INSERT INTO equipment (name, status, last_maintenance) VALUES (?, ?, ?)"
        self.execute_query(query, (name, status, datetime.now().strftime("%Y-%m-%d")))

    def update_equipment(self, equipment_id, name, status):
        query = "UPDATE equipment SET name = ?, status = ? WHERE id = ?"
        self.execute_query(query, (name, status, equipment_id))

    def delete_equipment(self, equipment_id):
        query = "DELETE FROM equipment WHERE id = ?"
        self.execute_query(query, (equipment_id,))

    def record_maintenance(self, equipment_id):
        query = "UPDATE equipment SET last_maintenance = ?, status = 'صالح للاستخدام' WHERE id = ?"
        self.execute_query(query, (datetime.now().strftime("%Y-%m-%d"), equipment_id))
