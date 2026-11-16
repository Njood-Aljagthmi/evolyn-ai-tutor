import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from db import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
conn.close()
print("Tables:", tables)
