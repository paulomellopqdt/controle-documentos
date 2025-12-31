import sqlite3

conn = sqlite3.connect("controle_docs.sqlite")
for name, sql in conn.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
):
    print("\n---", name, "---\n", sql)
