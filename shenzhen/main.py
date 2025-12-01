import requests
import pandas as pd
import os
import re
import time
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# --- CẤU HÌNH ---
api_url = 'https://search.gd.gov.cn/api/search/all'
excel_filename = '251115_SH_SZ_Crawled_Data_Fixed.xlsx'
sheet_name = 'shenzhen'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Origin': 'https://search.gd.gov.cn',
    'Referer': 'https://search.gd.gov.cn/',
}

# 1. TỪ KHÓA TÌM KIẾM
SEARCH_KEYWORDS_LIST = ["加装电梯", "增设电梯"]

# 2. TỪ KHÓA RÁC (BLACKLIST)
IRRELEVANT_KEYWORDS = [
    "采购", "招标", "中标", "谈判", "磋商", "比选", 
    "有限公司", "公司", 
    "供电", "变电", "输变电", "电缆", "线路", 
    "地铁", "轨道", "铁路", "隧道", "大桥", "立交",
    "小学", "中学", "幼儿园", "校区", "医院", "卫生院", "派出所",
    "竣工", "验收", "会议", "检查", "整治", "调研", "座谈", 
    "代表", "群众", "业主",
    "印发", "通知", "办法", "导则", "规定", "意见", "政策", "补助", "指南", "图册"
]

# 3. DANH SÁCH QUẬN
SHENZHEN_DISTRICTS = ["南山区", "福田区", "罗湖区", "盐田区", "宝安区", "龙岗区", "龙华区", "坪山区", "光明区", "大鹏新区"]
DISTRICT_KEYWORDS = {
    "南山区": ["南山", "蛇口", "华侨城", "科技园", "后海", "前海", "西丽"],
    "福田区": ["福田", "华强北", "中心区", "皇岗", "莲花山", "香蜜湖", "梅林"],
    "罗湖区": ["罗湖", "东门", "国贸", "莲塘", "黄贝", "笋岗"],
    "盐田区": ["盐田", "梅沙", "沙头角"],
    "宝安区": ["宝安", "西乡", "福永", "沙井", "松岗", "石岩", "新安"],
    "龙岗区": ["龙岗", "布吉", "横岗", "平湖", "坂田", "南湾"],
    "龙华区": ["龙华", "观澜", "民治", "大浪"],
    "坪山区": ["坪山", "坑梓"],
    "光明区": ["光明", "公明"],
    "大鹏新区": ["大鹏", "葵涌", "南澳"]
}

# --- CÁC HÀM XỬ LÝ ---

def init_excel_file():
    """Tự động xóa file cũ"""
    if os.path.exists(excel_filename):
        try:
            os.remove(excel_filename)
            print(f"🗑️  Đã xóa file cũ: {excel_filename}")
            time.sleep(1) 
        except Exception as e:
            print(f"⚠️  Không thể xóa file cũ: {e}")
            return False
    return True

def clean_title_smart(title):
    """Làm sạch tiêu đề (Bản nâng cấp cắt Prefix)"""
    cleaned = title
    
    # 1. Cắt mốc '关于' (Về việc)
    if '关于' in cleaned:
        parts = cleaned.split('关于')
        cleaned = parts[-1] 
    else:
        cleaned = re.sub(r'^.*?(管理局|自然资源局|办事处|委员会|政府)', '', cleaned)

    # 2. CẮT PREFIX (Từ thừa ở đầu) - MỚI
    # Lặp lại việc xóa cho đến khi sạch hết các từ khóa đầu dòng
    is_dirty = True
    while is_dirty:
        is_dirty = False
        # Các từ thừa thường gặp ở đầu tên chung cư
        prefixes = [
            "公布", "举行", "拟对", "深圳市", "南山区", "福田区", "罗湖区", 
            "盐田区", "宝安区", "龙岗区", "龙华区", "坪山区", "光明区", 
            "大鹏新区", "项目", "受理", "许可", "位于", "对"
        ]
        
        cleaned = cleaned.strip()
        for p in prefixes:
            if cleaned.startswith(p):
                cleaned = cleaned[len(p):] 
                is_dirty = True 
                break

    # 3. Xóa các từ khóa hành chính ở đuôi
    suffixes = ["公示", "公告", "通告", "意见", "批前", "受理", "许可", "书", "一期", "二期"] 
    for s in suffixes:
        cleaned = cleaned.replace(s, '')
        
    # 4. Cắt hành động (Cắt từ từ khóa trở về sau)
    actions = ["加装", "增设", "电梯", "总平面图", "工程", "设计方案", "建设工程", "核发", "规划"]
    
    min_idx = len(cleaned)
    found = False
    for act in actions:
        idx = cleaned.find(act)
        # Chỉ cắt nếu từ khóa không nằm ngay đầu câu (tránh cắt nhầm hết tên)
        if idx != -1 and idx < min_idx and idx > 1:
            min_idx = idx
            found = True
            
    if found:
        cleaned = cleaned[:min_idx]

    # Làm sạch ký tự đặc biệt (Dấu ngoặc, số lẻ loi)
    return cleaned.strip(' :：,，-《》()（）0123456789')

def is_valid_xiaoqu(name):
    """Kiểm tra tên chung cư hợp lệ"""
    if not name or len(name) < 2: return False
    
    # BLACKLIST TÊN CỤ THỂ
    INVALID_NAMES = [
        "既有住宅", "住宅", "现有住宅", "老旧小区", 
        "规划", "自然", "资源", "局", "委", "办", 
        "深圳", "市", "区", "街道", 
        "印发", "征求", "加强", "部分"
    ]
    
    if name in INVALID_NAMES: return False
    if "既有住宅" in name: return False
    
    if re.match(r'^[0-9\W]', name): return False
    
    return True

def extract_address(title):
    clean_text = clean_title_smart(title)
    
    xiaoqu = ""
    dongshu = ""
    danyuan = ""
    
    # Regex 1: Tên + Số tòa
    match = re.search(r'(.+?)(\d+[栋号幢楼座])(\d*单元)?', clean_text)
    
    if match:
        temp_xiaoqu = match.group(1).strip()
        if is_valid_xiaoqu(temp_xiaoqu):
            xiaoqu = temp_xiaoqu
            dongshu = match.group(2).strip()
            danyuan = match.group(3).strip() if match.group(3) else ""
    else:
        # Regex 2: Kiểm tra hậu tố nhà ở
        residential_suffixes = ["花园", "小区", "公寓", "大厦", "新村", "苑", "坊", "豪庭", "山庄", "城", "家园", "住宅", "宿舍"]
        if any(clean_text.endswith(s) for s in residential_suffixes):
            if is_valid_xiaoqu(clean_text):
                xiaoqu = clean_text

    return xiaoqu, dongshu, danyuan

def get_district(title, content):
    text = f"{title} {content}"
    for d in SHENZHEN_DISTRICTS:
        if d in text: return d
    for d, kws in DISTRICT_KEYWORDS.items():
        for kw in kws:
            if kw in text: return d
    return "未知区"

def main():
    if not init_excel_file(): return

    all_data = []
    seen_urls = set()
    
    print("🚀 Đang chạy script crawl Thâm Quyến (Final Perfect Version)...")
    
    for keyword in SEARCH_KEYWORDS_LIST:
        print(f"\n🔎 Tìm kiếm: {keyword}")
        page = 1
        
        while True:
            try:
                payload = {
                    "gdbsDivision": "440300", "gdbsOrgNum": "MB2C94128",
                    "keywords": keyword, "page": page, "position": "title",
                    "range": "site", "recommand": 1, "service_area": 755,
                    "site_id": "755016", "sort": "smart"
                }
                
                # Tăng timeout lên 30s để tránh lỗi ngắt kết nối
                resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
                data = resp.json()
                
                if 'data' not in data or 'news' not in data['data']: break
                items = data['data']['news']['list']
                total = data['data']['news']['total']
                
                if not items: break
                if page == 1: print(f"   📊 Tổng: {total} kết quả.")

                count = 0
                for item in items:
                    url = item.get('url')
                    if url in seen_urls: continue
                    seen_urls.add(url)
                    
                    full_title = item.get('title', '').replace('<em>', '').replace('</em>', '')
                    
                    if any(bad in full_title for bad in IRRELEVANT_KEYWORDS): continue
                    
                    xiaoqu, dongshu, danyuan = extract_address(full_title)
                    
                    if xiaoqu:
                        district = get_district(full_title, item.get('content', ''))
                        
                        pub_time = item.get('pub_time', '')
                        y, m, d = "", "", ""
                        if pub_time:
                            parts = pub_time.split(' ')[0].split('-')
                            if len(parts) >= 3: y, m, d = parts[0], parts[1], parts[2]
                        
                        all_data.append({
                            '区': district, '小区': xiaoqu, 
                            '栋数': dongshu, '单元': danyuan,
                            '年': y, '月': m, '日': d
                        })
                        count += 1
                        print(f"   ✅ {xiaoqu} | {dongshu} | {danyuan}")
                
                print(f"   Trang {page}: +{count} dòng.")
                page += 1
                time.sleep(1) # Tăng thời gian nghỉ để tránh quá tải server
                
            except Exception as e:
                print(f"   ❌ Lỗi trang {page}: {e}")
                # Nếu lỗi timeout, thử chờ 5s rồi chạy tiếp trang sau
                time.sleep(5)
                # break # Có thể bỏ break nếu muốn nó cố chạy tiếp
                break

    if all_data:
        print(f"\n💾 Đang ghi {len(all_data)} dòng vào Excel...")
        df = pd.DataFrame(all_data)
        cols = ['区', '小区', '栋数', '单元', '年', '月', '日']
        df = df[cols]
        
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        ws.append(cols)
        for r in dataframe_to_rows(df, index=False, header=False):
            ws.append(r)
        wb.save(excel_filename)
        print("🎉 Hoàn tất!")
    else:
        print("⚠️ Không có dữ liệu hợp lệ.")

if __name__ == "__main__":
    main()