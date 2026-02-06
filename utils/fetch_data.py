import json
import time
import csv
import sys
import argparse
from copy import deepcopy

import requests

DEFAULT_URL = "https://share.tcbi.qq.com/api/v1/share/page/data"

COOKIE = ""

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://share.tcbi.qq.com",
    "Referer": "https://share.tcbi.qq.com/page/share?pageId=10564191&projectId=11048365&token=***&scope=page&canvasType=GRID",
    "User-Agent": "Mozilla/5.0",
}

if COOKIE:
    HEADERS["Cookie"] = COOKIE

BASE_PAYLOAD = {
    "ExtraParam": "{\"limit\":1000,\"pageId\":10564191,\"widgetId\":\"table_fio2ko\",\"options\":{\"openList\":[]},\"reportId\":\"2xO6_Mv2-sgNK-4-5W-9PpK-TOMPe6atMHw7IRD_\",\"isAdHocRequest\":true,\"adHocCountConfig\":{\"countTypeMap\":{},\"customConfigMap\":{},\"calcFormulaCheckVOMap\":{}}}",
    "PageSize": 1000,
    "PageNum": 0,
    "UsePageLimit": True,
    "NeedDefaultSort": True,
    "ProjectId": 11048365,
    "WhereList": [],
    "WidgetType": "table",
    "IndexList": [],
    "DimList": [
        {"OrderBy":{"Value":"desc"},"Field":"日期","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"DATE","Granularity":None,"FieldName":"日期","FieldType":"datetime","FieldAlias":"dim_日期_1"},
        {"Field":"新增用户数","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"新增用户数","FieldType":"string","FieldAlias":"dim_新增用户数_1"},
        {"Field":"日活用户数","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"日活用户数","FieldType":"string","FieldAlias":"dim_日活用户数_1"},
        {"Field":"次日留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"次日留存率","FieldType":"string","FieldAlias":"dim_次日留存率_1"},
        {"Field":"3日留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"3日留存率","FieldType":"string","FieldAlias":"dim_3日留存率_1"},
        {"Field":"3日内留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"3日内留存率","FieldType":"string","FieldAlias":"dim_3日内留存率_1"},
        {"Field":"7日留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"7日留存率","FieldType":"string","FieldAlias":"dim_7日留存率_1"},
        {"Field":"7日内留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"7日内留存率","FieldType":"string","FieldAlias":"dim_7日内留存率_1"},
        {"Field":"14日留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"14日留存率","FieldType":"string","FieldAlias":"dim_14日留存率_1"},
        {"Field":"14日内留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"14日内留存率","FieldType":"string","FieldAlias":"dim_14日内留存率_1"},
        {"Field":"30日留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"30日留存率","FieldType":"string","FieldAlias":"dim_30日留存率_1"},
        {"Field":"30日内留存率","EmptyValueConfig":{"Number":{"Type":"-","Custom":""},"String":{"Type":"-","Custom":""}},"FieldComplexType":"STRING","Granularity":None,"FieldName":"30日内留存率","FieldType":"string","FieldAlias":"dim_30日内留存率_1"},
    ],
    "DataTableId": "b1fb3ce1621141acaec15c184661c599",
    "Token": "885a8e02-d076-462a-ab9a-0c088ea23512",
    "AsyncRequest": False,
    "Uin": None,
    "SubAccountUin": None,
    "RequestId": "script",
    "Language": "zh-CN",
}

def post(payload: dict, url: str) -> dict:
    print(f"url={url} pageNum={payload.get('PageNum')} pageSize={payload.get('PageSize')}")
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        print(f"status={r.status_code}")
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"request_error={e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(f"response_text={e.response.text}")
            except Exception:
                pass
        raise

def extract_urls(obj):
    urls = []
    def is_url(s):
        return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                key_lower = str(k).lower()
                if is_url(v):
                    if any(t in key_lower for t in ["image", "img", "cover", "thumb", "avatar", "url", "pic"]):
                        urls.append(v)
                # attempt to parse nested json strings
                if isinstance(v, str) and v.strip().startswith("{") and v.strip().endswith("}"):
                    try:
                        vv = json.loads(v)
                        walk(vv)
                    except Exception:
                        pass
                else:
                    walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)
        else:
            if is_url(x):
                urls.append(x)
    walk(obj)
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

def find_first_list(obj):
    """在 JSON 里递归找“最像行数据”的 list（list[dict] 或 list[list]）。"""
    if isinstance(obj, list):
        if not obj:
            return None
        # list[dict] 且 dict 有多个字段 —— 常见行结构
        if isinstance(obj[0], dict) and len(obj[0]) >= 2:
            return obj
        # list[list] 且每行长度>1 —— 也可能是行
        if isinstance(obj[0], list) and len(obj[0]) >= 2:
            return obj
        # 否则继续递归
        for it in obj:
            got = find_first_list(it)
            if got is not None:
                return got
        return None

    if isinstance(obj, dict):
        for k, v in obj.items():
            got = find_first_list(v)
            if got is not None:
                return got
    return None

def dump_all(url: str):
    all_rows = []
    page = 0

    # 用 DimList 作为表头（如果响应不给列名，这个也够用了）
    headers = [d.get("FieldName") or d.get("Field") for d in BASE_PAYLOAD["DimList"]]

    while True:
        payload = deepcopy(BASE_PAYLOAD)
        payload["PageNum"] = page

        resp = post(payload, url)

        # 落一份样例响应，便于你/我确认字段（只落第一页）
        if page == 0:
            with open("resp_page0.json", "w", encoding="utf-8") as f:
                json.dump(resp, f, ensure_ascii=False, indent=2)
            # also dump possible urls in the first page's data for quick inspection
            try:
                urls0 = extract_urls(resp.get("Response", {}).get("Data", resp.get("Response", {})))
                with open("urls_page0.txt", "w", encoding="utf-8") as f:
                    for u in urls0:
                        f.write(u + "\n")
            except Exception:
                pass

        if not isinstance(resp, dict) or "Response" not in resp:
            raise RuntimeError("Unexpected response shape; see resp_page0.json")

        r0 = resp.get("Response", {})
        msg = r0.get("Msg", "")
        data = r0.get("Data", r0)  # 有些返回直接在 Response 下

        # 如果 AsyncRequest 实际仍返回异步任务，你会在 resp_page0.json 里看到 taskId/requestId 一类字段
        # 这里先直接找“行数据 list”
        rows = find_first_list(data)

        if not rows:
            # 没找到行数据：直接停止，并让你看 resp_page0.json 决定怎么改解析
            print("No rows found. Please inspect resp_page0.json for the actual rows field.")
            break

        # 统一行格式：list[dict] -> dict；list[list] -> 按 headers 映射成 dict
        if isinstance(rows[0], dict):
            all_rows.extend(rows)
            got_n = len(rows)
            # enrich image urls for dict rows
            for r in all_rows[-got_n:]:
                urls = extract_urls(r)
                if urls:
                    r["PrimaryImageURL"] = urls[0]
                    r["ImageURLs"] = ",".join(urls)
        else:
            for row in rows:
                rec = {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
                all_rows.append(rec)
            got_n = len(rows)

        print(f"page={page} rows={got_n} total={len(all_rows)}")

        # 翻页停止条件：这一页不足 PageSize 或者为空
        if got_n == 0 or got_n < payload["PageSize"]:
            break

        page += 1
        time.sleep(0.2)

        if page > 100000:
            raise RuntimeError("Too many pages; pagination logic likely wrong.")

    # 导出 JSON
    with open("ghost_generate_all.json", "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    # 导出 CSV（dict list）
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        # 如果后面行有新字段，补齐
        for r in all_rows[1:]:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with open("ghost_generate_all.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_rows)

    print(f"done. rows={len(all_rows)} -> ghost_generate_all.csv / ghost_generate_all.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default=DEFAULT_URL)
    parser.add_argument("--pagesize", type=int, default=1000)
    args = parser.parse_args()
    BASE_PAYLOAD["PageSize"] = args.pagesize
    dump_all(args.url)
