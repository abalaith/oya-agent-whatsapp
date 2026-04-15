import os
import json

try:
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    if action in ("query_db", "list_tables"):
        import psycopg2
        import psycopg2.extras

        db_url = os.environ["RETOOL_DB_URL"]
        conn = psycopg2.connect(db_url)
        conn.set_session(readonly=True)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if action == "query_db":
            sql = inp.get("sql", "").strip()
            if not sql:
                print(json.dumps({"error": "sql parameter is required for query_db"}))
            elif not sql.upper().startswith("SELECT"):
                print(json.dumps({"error": "Only SELECT queries are allowed"}))
            else:
                cur.execute(sql)
                rows = [dict(r) for r in cur.fetchall()]
                print(json.dumps({"rows": rows, "count": len(rows)}, default=str))

        elif action == "list_tables":
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            tables = [r["table_name"] for r in cur.fetchall()]
            print(json.dumps({"tables": tables}))

        cur.close()
        conn.close()

    else:
        print(json.dumps({"error": f"Unknown action: {action}. Use one of: query_db, list_tables"}))

except Exception as e:
    print(json.dumps({"error": str(e)}))
