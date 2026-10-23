"""
db_config.py
MySQL database configuration, schema initialisation, and matrix user/department lookup.
Supports MySQL database connection via mysql.connector / pymysql with seamless SQLite fallback.
"""
import os
import sqlite3
import logging
import hashlib
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Environment variables for MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "jadisan_db")

_USE_SQLITE = False
_sqlite_path = os.path.join(os.path.dirname(__file__), "jadisan_admin.db")


def hash_password(password: str) -> str:
    """Return SHA256 hash of password for simple secure comparison."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_db_connection():
    """Returns a DB connection (MySQL if available, or SQLite fallback)."""
    global _USE_SQLITE
    if not _USE_SQLITE:
        try:
            import mysql.connector # type: ignore
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                connect_timeout=3,
            )
            return conn, "mysql"
        except Exception as exc:
            logger.info("MySQL connection unavailable (%s). Using SQLite database fallback at %s", exc, _sqlite_path)
            _USE_SQLITE = True

    conn = sqlite3.connect(_sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"


def init_db():
    """Initialise database tables and seed matrix departments and admin users."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "mysql":
        # Create departments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description VARCHAR(255)
            ) ENGINE=InnoDB;
        """)
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                tier VARCHAR(50) NOT NULL,
                department_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)
    else:
        # SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                tier TEXT NOT NULL,
                department_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    conn.commit()

    # Check if departments seeded
    cursor.execute("SELECT COUNT(*) FROM departments;")
    row = cursor.fetchone()
    count = row[0] if isinstance(row, (list, tuple)) else row['COUNT(*)'] if hasattr(row, 'keys') else 0
    if count == 0:
        seed_departments = [
            ("ROADS", "Roads & Public Works", "Potholes, asphalt repair, street damage"),
            ("WATER", "Water Supply Board", "Pipe leaks, water supply outages, water quality"),
            ("SANITATION", "Sanitation Department", "Garbage collection, waste management, litter"),
            ("ELECTRICAL", "Electrical Department", "Streetlights, power cables, transformer issues"),
            ("SEWERAGE", "Sewerage Board", "Drainage overflow, sewer blockage, manholes"),
            ("GENERAL", "General Municipal Office", "Civic complaints, general administrative grievances"),
        ]
        for code, name, desc in seed_departments:
            if db_type == "mysql":
                cursor.execute("INSERT IGNORE INTO departments (code, name, description) VALUES (%s, %s, %s)", (code, name, desc))
            else:
                cursor.execute("INSERT OR IGNORE INTO departments (code, name, description) VALUES (?, ?, ?)", (code, name, desc))

    # Check if users seeded
    cursor.execute("SELECT COUNT(*) FROM users;")
    row = cursor.fetchone()
    count = row[0] if isinstance(row, (list, tuple)) else row['COUNT(*)'] if hasattr(row, 'keys') else 0
    if count == 0:
        pw_hash = hash_password("password123")
        seed_users = [
            ("ward_roads", pw_hash, "Rajesh Kumar (Junior Engineer)", "Ward Officer", "Ward", "Roads & Public Works", "+919876543210", "r.kumar@corp.gov.in"),
            ("ward_water", pw_hash, "Sita Ram (Assistant Engineer)", "Ward Officer", "Ward", "Water Supply Board", "+919876543211", "s.ram@water.gov.in"),
            ("zonal_roads", pw_hash, "Arun Varma (Zonal Exec. Engineer)", "Zone Officer", "Zone", "Roads & Public Works", "+919876543212", "a.varma@corp.gov.in"),
            ("zonal_water", pw_hash, "Meena Kumari (Zonal Engineer)", "Zone Officer", "Zone", "Water Supply Board", "+919876543213", "m.kumari@water.gov.in"),
            ("district_roads", pw_hash, "V. Swaminathan (Superintending Engineer)", "District Officer", "District", "Roads & Public Works", "+919876543214", "v.swami@corp.gov.in"),
            ("district_water", pw_hash, "P. Jayaraman (Chief District Engineer)", "District Officer", "District", "Water Supply Board", "+919876543215", "p.jaya@water.gov.in"),
            ("commissioner", pw_hash, "Dr. K. Vijayaraghavan IAS", "Commissioner", "Commissioner", "General Municipal Office", "+919876543216", "commissioner@corp.gov.in"),
        ]
        for username, p_hash, name, role, tier, dept, phone, email in seed_users:
            if db_type == "mysql":
                cursor.execute(
                    "INSERT IGNORE INTO users (username, password_hash, full_name, role, tier, department_name, phone, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (username, p_hash, name, role, tier, dept, phone, email)
                )
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO users (username, password_hash, full_name, role, tier, department_name, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, p_hash, name, role, tier, dept, phone, email)
                )

    conn.commit()
    conn.close()
    logger.info("Database matrix initialised successfully (%s).", db_type)


def register_user(username: str, password: str, full_name: str, role: str = "Zone Officer", tier: str = "Zone", department_name: str = "General Municipal Office") -> Dict[str, Any]:
    """Register a new Zone Officer account in MySQL/SQLite database."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)

    try:
        if db_type == "mysql":
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, tier, department_name) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, pw_hash, full_name, role, tier, department_name)
            )
        else:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, tier, department_name) VALUES (?, ?, ?, ?, ?, ?)",
                (username, pw_hash, full_name, role, tier, department_name)
            )
        conn.commit()
    finally:
        conn.close()

    logger.info("Registered new user %s (%s).", username, full_name)
    return {
        "username": username,
        "full_name": full_name,
        "role": role,
        "tier": tier,
        "department_name": department_name
    }



def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate admin user against MySQL/SQLite database."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)

    if db_type == "mysql":
        cursor.execute(
            "SELECT id, username, full_name, role, tier, department_name, phone, email FROM users WHERE username = %s AND password_hash = %s",
            (username, pw_hash)
        )
        row = cursor.fetchone()
    else:
        cursor.execute(
            "SELECT id, username, full_name, role, tier, department_name, phone, email FROM users WHERE username = ? AND password_hash = ?",
            (username, pw_hash)
        )
        row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    if isinstance(row, sqlite3.Row):
        return dict(row)
    else:
        return {
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "tier": row[4],
            "department_name": row[5],
            "phone": row[6],
            "email": row[7],
        }


def get_matrix_officer(department: str, tier: str) -> Dict[str, Any]:
    """
    Returns the specific matrix officer details (e.g. Zonal Roads Officer)
    combining Department + Tier level.
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "mysql":
        cursor.execute(
            "SELECT full_name, role, tier, department_name, phone, email FROM users WHERE department_name = %s AND tier = %s LIMIT 1",
            (department, tier)
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "SELECT full_name, role, tier, department_name, phone, email FROM users WHERE tier = %s LIMIT 1",
                (tier,)
            )
            row = cursor.fetchone()
    else:
        cursor.execute(
            "SELECT full_name, role, tier, department_name, phone, email FROM users WHERE department_name = ? AND tier = ? LIMIT 1",
            (department, tier)
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "SELECT full_name, role, tier, department_name, phone, email FROM users WHERE tier = ? LIMIT 1",
                (tier,)
            )
            row = cursor.fetchone()

    conn.close()

    if row:
        if isinstance(row, sqlite3.Row):
            return dict(row)
        return {
            "full_name": row[0],
            "role": row[1],
            "tier": row[2],
            "department_name": row[3],
            "phone": row[4],
            "email": row[5],
        }

    # Default fallback matrix title
    return {
        "full_name": f"{tier} Officer — {department}",
        "role": f"{tier} Officer",
        "tier": tier,
        "department_name": department,
        "phone": "+919876543210",
        "email": "officer@corp.gov.in"
    }


def get_all_departments() -> List[Dict[str, Any]]:
    """Return all departments."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, code, name, description FROM departments")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            results.append(dict(r))
        else:
            results.append({"id": r[0], "code": r[1], "name": r[2], "description": r[3]})
    return results
