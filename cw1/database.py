import mysql.connector
import bcrypt

def connect_db():
    """Connect to MySQL server and create the database and tables."""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS danceclub")
    conn.commit()
    cursor.close()
    conn.close()
    
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="danceclub"
    )
    cursor = conn.cursor()
    
    # Create users table with created_at timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id VARCHAR(10) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        birth_date DATE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'director', 'coach', 'artist') NOT NULL,
        phone VARCHAR(255) DEFAULT NULL,
        parent_id VARCHAR(10) DEFAULT NULL,
        guardian VARCHAR(255) DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES users(user_id) ON DELETE SET NULL
    )
    ''')

    # Create injury_records table with timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS injury_records (
        injury_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(10) NOT NULL,
        injury_date DATE NOT NULL,
        injury_type VARCHAR(255) NOT NULL,
        recovery_status ENUM('recovering', 'recovered', 'not recovered') NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')

    # Create performance_records table with timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS performance_records (
        performance_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(10) NOT NULL,
        performance_date DATE NOT NULL,
        location VARCHAR(255) NOT NULL,
        performance_name VARCHAR(255) NOT NULL,
        score INT CHECK (score >= 1 AND score <= 5),
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')

    # Create attendance_records table with timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        attendance_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(10) NOT NULL,
        attendance_date DATE NOT NULL,
        status ENUM('present', 'absent', 'late') NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')

    # Create training_records table with timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_records (
        training_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(10) NOT NULL,
        training_date DATE NOT NULL,
        training_type VARCHAR(255) NOT NULL,
        duration INT NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')
    
    # Create password_resets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_resets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(100) NOT NULL,
        otp VARCHAR(6) NOT NULL,
        expiry_time DATETIME NOT NULL,
        used BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_email (email)
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("Database and tables created successfully!")

def hash_password(password):
    """Encrypt password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

def generate_user_id(role):
    """Generate a unique user ID based on the role prefix."""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="danceclub"
    )
    cursor = conn.cursor()
    
    role_prefix = {
        "admin": "AD",
        "director": "DR",
        "coach": "CH",
        "artist": "AT"
    }
    
    prefix = role_prefix.get(role, "UN")  # default Unknown
    
   # Find the latest user ID
    cursor.execute(f"SELECT user_id FROM users WHERE user_id LIKE '{prefix}%' ORDER BY user_id DESC LIMIT 1")
    last_id = cursor.fetchone()
    
    if last_id:
        last_num = int(last_id[0][2:])  # get number
        new_num = last_num + 1
    else:
        new_num = 1
    
    new_user_id = f"{prefix}{new_num:03d}"  # 3-digit format
    
    cursor.close()
    conn.close()
    
    return new_user_id


def add_user(name, birth_date, email, password, role, phone=None, guardian=None, parent_id=None):
    """Add a new user to the database with formatted user_id."""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="danceclub"
    )
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    user_id = generate_user_id(role)  # 生成用户 ID

    try:
        cursor.execute('''
            INSERT INTO users (user_id, name, birth_date, email, password, role, phone, guardian, parent_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, name, birth_date, email, hashed_password, role, phone, guardian, parent_id))
        
        conn.commit()
        print(f"✅ User {name} ({user_id}) added successfully!")
    except mysql.connector.IntegrityError:
        print(f"⚠ User {name} already exists.")
    
    cursor.close()
    conn.close()

def create_default_admin():
    """Create a default admin user if it does not exist."""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="danceclub"
    )
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = 'admin@danceclub.com'")
    admin_exists = cursor.fetchone()

    if not admin_exists:
        admin_id = generate_user_id("admin")  # 生成管理员 ID
        hashed_password = hash_password("admin")
        cursor.execute('''
            INSERT INTO users (user_id, name, birth_date, email, password, role, guardian)
            VALUES (%s, %s, %s, %s, %s, %s, NULL)
        ''', (admin_id, "Admin", "2000-01-01", "admin@danceclub.com", hashed_password, "admin"))
        conn.commit()
        print(f"✅ Default admin user created successfully! (ID: {admin_id})")
    else:
        print("⚠ Admin user already exists.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    connect_db()  # 创建数据库和表
    create_default_admin()  # 创建默认管理员

