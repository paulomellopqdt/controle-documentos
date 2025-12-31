import sqlite3
import psycopg

SQLITE_PATH = "controle_docs.sqlite"

# >>> PREENCHA COM SEUS DADOS (USE A SENHA NOVA ROTACIONADA) <<<
PG_HOST = "db.buseivqfsrunktqbeasn.supabase.co"
PG_PORT = 5432
PG_DB   = "postgres"
PG_USER = "postgres"
PG_PASS = "B0nf@d1n12018"


def fetch_all_sqlite(conn, table: str):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return cols, rows


def migrate_table(pg_conn, table: str, cols, rows):
    if not rows:
        print(f"[{table}] sem dados, pulando.")
        return

    col_list = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f"INSERT INTO public.{table} ({col_list}) VALUES ({placeholders})"

    with pg_conn.cursor() as cur:
        # limpa para evitar duplicar (ordem importa por FKs)
        cur.execute(f"TRUNCATE TABLE public.{table} RESTART IDENTITY CASCADE;")

        cur.executemany(sql, rows)

    print(f"[{table}] inseriu {len(rows)} linhas.")


def main():
    # SQLite
    sconn = sqlite3.connect(SQLITE_PATH)
    sconn.row_factory = None

    # Postgres (Supabase)
    pg_conn = psycopg.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        connect_timeout=10,
    )

    try:
        # Ordem correta (por causa de chaves estrangeiras)
        for table in ["casos", "master_oms", "retornos_om", "arquivados"]:
            cols, rows = fetch_all_sqlite(sconn, table)
            migrate_table(pg_conn, table, cols, rows)

        pg_conn.commit()
        print("\n✅ Migração concluída com sucesso.")
    except Exception as e:
        pg_conn.rollback()
        print("\n❌ Erro na migração. Nada foi gravado.")
        raise
    finally:
        sconn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
