import sqlite3
import sys
from werkzeug.security import check_password_hash

DB = 'expense_tracker.db'

def main():
    if len(sys.argv) != 3:
        print("Usage: python test_login.py <username> <password>")
        sys.exit(2)
    username = sys.argv[1].strip().lower()
    password = sys.argv[2]

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT id, name, username, password FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    if not row:
        print(f"No user found with username: {username!r}")
        conn.close()
        return

    stored_hash = row[3]
    print(f"Stored username repr: {repr(row[2])}")
    print(f"Stored password hash repr: {repr(stored_hash)}")
    match = check_password_hash(stored_hash, password)
    print(f"Password match: {match}")
    conn.close()

if __name__ == '__main__':
    main()
