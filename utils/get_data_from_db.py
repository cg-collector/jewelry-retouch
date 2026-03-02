import os
import argparse
import datetime
import json
import sys

def parse_env(env_path):
    cfg = {}
    if not os.path.exists(env_path):
        return cfg
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                cfg[k] = v
    return cfg

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

def get_conn(cfg):
    host = cfg.get("host", "localhost")
    port = int(cfg.get("port", "3306"))
    user = cfg.get("user", "")
    password = cfg.get("password", "")
    try:
        import pymysql
        conn = pymysql.connect(host=host, port=port, user=user, password=password, charset="utf8mb4", autocommit=True)
        return conn
    except Exception as e1:
        # print(f"PyMySQL failed: {e1}")
        try:
            import mysql.connector
            conn = mysql.connector.connect(host=host, port=port, user=user, password=password)
            return conn
        except Exception as e2:
            print(f"数据库连接失败 (PyMySQL: {e1}, MySQL Connector: {e2})")
            sys.exit(1)

def build_sql(start_time, end_time, limit, status, jewelry_only):
    base_where = []
    base_where.append("gr.create_at BETWEEN %s AND %s")
    if status == "completed":
        base_where.append("gr.status = 2")
    elif status == "processing":
        base_where.append("gr.status = 1")
    if jewelry_only:
        jewelry_filter = (
            "UPPER(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(oi.image_analysis, '$.product_type')), '')) IN "
            "('JEWELRY') "
            "OR JSON_UNQUOTE(JSON_EXTRACT(oi.image_analysis, '$.product_type')) LIKE '%%珠宝%%' "
            "OR JSON_UNQUOTE(JSON_EXTRACT(oi.image_analysis, '$.category')) LIKE '%%珠宝%%' "
            "OR JSON_UNQUOTE(JSON_EXTRACT(oi.image_analysis, '$.category')) LIKE '%%首饰%%'"
        )
        base_where.append(f"({jewelry_filter})")
    where_sql = " AND ".join(base_where)
    sql = f"""
SELECT
  gr.id AS record_id,
  DATE(gr.create_at) AS date,
  gr.create_at,
  gr.user_id,
  CONCAT('https://static.snappyit.ai/', gr.store_key) AS generated_image_url,
  CONCAT('https://static.snappyit.ai/', oi.store_key) AS original_image_url,
  COALESCE(ggp.messages, '') AS prompt,
  JSON_UNQUOTE(JSON_EXTRACT(oi.image_analysis, '$.product_type')) AS product_type,
  gr.status,
  gr.model
FROM
  ghost.ghost_generate_record gr
  INNER JOIN ghost.ghost_generate_history gh ON gr.history_id = gh.id AND gh.task_type = 0
  INNER JOIN ghost.ghost_image oi ON gr.original_image_id = oi.id
  LEFT JOIN ghost.ghost_generate_prompt ggp ON ggp.record_id = gr.id
WHERE
  {where_sql}
ORDER BY
  gr.create_at DESC
LIMIT {int(limit)}
"""
    return sql

def export_rows(rows, outdir):
    ensure_dir(outdir)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = os.path.join(outdir, f"ghost_jewelry_{ts}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as fw:
        for r in rows:
            fw.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    meta_path = os.path.join(outdir, f"meta_{ts}.json")
    meta = {"count": len(rows), "generated_at": ts}
    with open(meta_path, "w", encoding="utf-8") as fw:
        fw.write(json.dumps(meta, ensure_ascii=False, default=str))
    print(f"已保存: {jsonl_path}")

def to_dicts(cursor, rows):
    cols = [c[0] for c in cursor.description]
    res = []
    for row in rows:
        item = {}
        for i, v in enumerate(row):
            item[cols[i]] = v
        res.append(item)
    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=".env")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--start", default=(datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d 00:00:00"))
    parser.add_argument("--end", default=datetime.datetime.now().strftime("%Y-%m-%d 23:59:59"))
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--status", choices=["all", "completed", "processing"], default="completed")
    parser.add_argument("--jewelry_only", action="store_true")
    args = parser.parse_args()

    cfg = parse_env(args.env)
    conn = get_conn(cfg)
    sql = build_sql(args.start, args.end, args.limit, args.status, args.jewelry_only)
    rows = []
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (args.start, args.end))
        fetched = cursor.fetchall()
        rows = to_dicts(cursor, fetched)
        cursor.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    outdir = args.outdir or f"outputs/db_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    export_rows(rows, outdir)

if __name__ == "__main__":
    main()