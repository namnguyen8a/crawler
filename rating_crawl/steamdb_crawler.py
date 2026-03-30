import re
import time
import os
from urllib.parse import quote

import pandas as pd
from bs4 import BeautifulSoup

# Import thư viện chống Cloudflare
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# ── Configuration ─────────────────────────────────────────────────────────────

DEVELOPERS =[
    "Valve",
    "Larian Studios",
    "Game Science",
    "Rockstar Games",
    "Nihon Falcom",
    "Insomniac Games, Nixxes Software",
    "FromSoftware, Inc.",
    "Warhorse Studios",
    "Bloober Team SA",
    "Double Fine Productions",
    "SHIFT UP Corporation",
    "Sucker Punch Productions, Nixxes Software",
    "Sonic Team",
    "Square Enix",
    "ACQUIRE Corp",
    "KOEI TECMO GAMES CO., LTD.",
    "SANDLOT",
    "MAGES. Inc.",
    "ATLUS",
    "Ryu Ga Gotoku Studio",
]

BASE_URL = "https://steamdb.info"
DELAY = 3  # Nghỉ 3 giây giữa các lần chuyển trang để tránh bị block

# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_developers_list(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    result = {}

    for row in soup.select("tr.app"):
        tds = row.find_all("td")
        if len(tds) < 7:
            continue
        
        name_tag = tds[2].find("a", class_="b")
        if not name_tag:
            continue
            
        name = name_tag.get_text(strip=True)
        dev_url = name_tag.get("href", "")

        result[name] = {
            "global_rank": tds[0].get_text(strip=True).rstrip("."),
            "products":    tds[3].get_text(strip=True),
            "positive":    tds[4].get_text(strip=True).replace(",", ""),
            "negative":    tds[5].get_text(strip=True).replace(",", ""),
            "rating_pct":  tds[6].get_text(strip=True),
            "dev_url":     BASE_URL + dev_url.replace("+", "%20"),
        }

    return result

def parse_dev_page(html: str) -> tuple:
    soup = BeautifulSoup(html, "lxml")

    sub = soup.select_one("h2.header-subtitle")
    total_label = sub.get_text(strip=True) if sub else "Unknown"

    records =[]
    for row in soup.select("tr.app"):
        appid = row.get("data-appid", "")
        tds = row.find_all("td")
        
        if len(tds) < 10:
            continue

        name_tag = tds[2].find("a", class_="b")
        name = name_tag.get_text(strip=True) if name_tag else ""

        cat_tag = tds[2].find("span", class_="cat")
        etype = cat_tag.get_text(strip=True) if cat_tag else "Game"

        def parse_number(val):
            try: return float(val) if '.' in val else int(val)
            except: return None

        rating_val = parse_number(tds[5].get("data-sort", ""))
        if rating_val is not None and rating_val < 0:
            rating_val = None

        release_val = tds[6].get("data-sort", "")
        followers = tds[7].get("data-sort", "")
        online = tds[8].get("data-sort", "")
        peak = tds[9].get("data-sort", "")

        records.append({
            "appid": appid, "name": name, "type": etype,
            "rating": rating_val, "release": release_val,
            "followers": followers, "online": online, "peak": peak,
        })

    return records, total_label

def summarise(records: list) -> dict:
    games =[r for r in records if r["type"] == "Game"]
    rated = [r["rating"] for r in games if r["rating"] is not None]
    return {
        "games_on_page": len(games),
        "rated_games":   len(rated),
        "avg_rating":    round(sum(rated) / len(rated), 2) if rated else None,
        "max_rating":    max(rated) if rated else None,
        "min_rating":    min(rated) if rated else None,
    }

# ── Main Logic ────────────────────────────────────────────────────────────────

def init_driver():
    print("Khởi động Trình duyệt Undetected Chromedriver (Chống Cloudflare)...")
    options = uc.ChromeOptions()
    # Chặn load hình ảnh để chạy siêu tốc
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    #[QUAN TRỌNG] FIX LỖI MISMATCH VERSION: 
    # Báo cho thư viện biết Chrome trên máy bạn đang là bản 146
    driver = uc.Chrome(options=options, headless=False, version_main=146)
    
    # Thu nhỏ cửa sổ xuống Taskbar để không làm phiền
    driver.minimize_window() 
    return driver

def main():
    driver = init_driver()
    
    try:
        # ── Bước 1: Lấy danh sách tổng quan ─────────────────────────────────
        list_data = {}
        print(f"\nFetching {BASE_URL}/developers/ ...")
        driver.get(f"{BASE_URL}/developers/")
        
        try:
            # Chờ Cloudflare tự động xác thực (tối đa 25 giây) cho đến khi thấy bảng
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-products"))
            )
            
            # Chọn "-1" (Tất cả) để load full list trên trang chủ
            try:
                select_elem = driver.find_element(By.CSS_SELECTOR, "select.dt-input")
                Select(select_elem).select_by_value("-1")
                time.sleep(2)
            except:
                pass

            html = driver.page_source
            list_data = parse_developers_list(html)
            print(f"  → Đã crawl được {len(list_data)} developers từ trang chủ\n")
        except Exception as e:
            print("  ✗ Bị chặn ở trang chủ hoặc timeout. Đang tiếp tục...\n")

        found_in_list =[d for d in DEVELOPERS if d in list_data]
        not_in_list   =[d for d in DEVELOPERS if d not in list_data]
        print(f"Targets tìm thấy trong Top List ({len(found_in_list)}): {found_in_list}")
        print(f"Targets KHÔNG có trong Top List ({len(not_in_list)}): {not_in_list}\n")

        # ── Bước 2: Crawl từng Developer cụ thể ─────────────────────────────
        all_rows = []
        summaries =[]

        print(f"Bắt đầu crawl chi tiết {len(DEVELOPERS)} developer...\n")

        for dev in DEVELOPERS:
            url = f"{BASE_URL}/developer/{quote(dev, safe='')}/"
            print(f"→ {dev}")

            list_info = list_data.get(dev, {})
            if list_info:
                print(f"  [TopList Data] Hạng #{list_info['global_rank']:>4} | Rating: {list_info['rating_pct']} | Game: {list_info['products']}")

            try:
                driver.get(url)
                # Đợi cho tới khi bảng game xuất hiện HOẶC hiện thông báo lỗi (không tìm thấy)
                WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-sales, .panel-error"))
                )
                
                # Cố gắng bấm Show "All" (-1)
                try:
                    select_elem = driver.find_element(By.CSS_SELECTOR, "select.dt-input")
                    Select(select_elem).select_by_value("-1")
                    time.sleep(2)
                except:
                    pass 

                html = driver.page_source
                records, label = parse_dev_page(html)
                print(f"  Trạng thái: {label} | Lấy được {len(records)} rows")

                if not records:
                    summaries.append({"developer": dev, "error": "no_data"})
                    time.sleep(DELAY)
                    continue

                for r in records:
                    r["developer"] = dev
                all_rows.extend(records)

                stats = summarise(records)
                print(f"  ✓ Trung bình={stats['avg_rating']}% | Cao nhất={stats['max_rating']}%\n")

                summaries.append({
                    "developer":        dev,
                    "global_rank":      list_info.get("global_rank", ""),
                    "aggregate_rating": list_info.get("rating_pct", ""),
                    "total_products":   list_info.get("products", ""),
                    "total_positive":   list_info.get("positive", ""),
                    "total_negative":   list_info.get("negative", ""),
                    **stats,
                })

            except Exception as e:
                print(f"  ✗ Lỗi khi tải trang {dev}. Có thể dính Cloudflare chặn cứng.\n")
                row = {"developer": dev, "error": "timeout_or_blocked"}
                summaries.append(row)

            time.sleep(DELAY)

    finally:
        driver.quit()

    # ── Bước 3: Lưu CSV ────────────────────────────────────────────────────────
    if all_rows:
        col_order =["developer", "appid", "name", "type", "rating", "release", "followers", "online", "peak"]
        df_games = pd.DataFrame(all_rows)
        df_games = df_games[[c for c in col_order if c in df_games.columns]]
        df_games.to_csv("steamdb_games.csv", index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu steamdb_games.csv ({len(df_games)} rows)")

    if summaries:
        df_summary = pd.DataFrame(summaries)
        df_summary.to_csv("steamdb_developer_summary.csv", index=False, encoding="utf-8-sig")
        print(f"Đã lưu steamdb_developer_summary.csv ({len(df_summary)} rows)")

if __name__ == "__main__":
    main()