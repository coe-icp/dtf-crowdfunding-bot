import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # جدول کاربران برای ذخیره اطلاعات، کیف پول و امتیازهای سه گانه
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            evm_wallet TEXT,
            referred_by INTEGER,
            bronze_points INTEGER DEFAULT 1,
            gold_points INTEGER DEFAULT 0,
            diamond_points INTEGER DEFAULT 0,
            deposit_status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
