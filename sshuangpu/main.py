import requests
import pandas as pd
import os
import re
import time
from openpyxl import load_workbook
import json

# --- CẤU HÌNH ---
SEARCH_KEYWORDS = ["加装电梯"] 

api_url = r'https://ss.shanghai.gov.cn/manda-app/api/app/search/v1/1ywaiqo/search'

request_delay = 0.5
retry_attempts = 3
retry_delay = 5

checkpoint_file = 'checkpoint_api.log'
txt_filename = 'crawled_titles_api.txt'
excel_filename = '模版.xlsx'
sheet_name_to_update = 'shanghai'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://www.shhuangpu.gov.cn',
    'Referer': 'https://www.shhuangpu.gov.cn/',
}

CLEANUP_KEYWORDS = [
    "街道", "项目", "地块", "工程", "方案", "规划", "设计", "建设", "新建", "改建",
    "修缮", "扩建", "改造", "用房", "公示", "公告", "预公告", "关于", "（已结束）",
    "的意见征询", "旧住房", "成套", "公众反馈意见的处理情况"
]

# --- CÁC HÀM HỖ TRỢ ---
def find_last_row_with_data(sheet):
    for row in range(sheet.max_row, 0, -1):
        for cell in sheet[row]:
            if cell.value is not None: return row
    return 0

def parse_title_hybrid(title_text):
    address = title_text.strip()
    if address.startswith("关于"): address = address[2:].strip()
    hao_pos = -1
    if '号楼' in address: hao_pos = address.rfind('号楼') + 2
    elif '号' in address: hao_pos = address.rfind('号') + 1
    if hao_pos != -1:
        address = address[:hao_pos].strip()
        return "黄浦区", address
    min_pos = -1
    for keyword in CLEANUP_KEYWORDS:
        pos = address.find(keyword)
        if pos > 0 and (min_pos == -1 or pos < min_pos): min_pos = pos
    if min_pos != -1: address = address[:min_pos].strip()
    return "黄浦区", address

def read_checkpoint():
    if os.path.exists(checkpoint_file):
        # Chỉ định encoding='utf-8' khi đọc để đảm bảo an toàn
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            try:
                content = f.read().strip().split(',')
                if len(content) == 2: return content[0], int(content[1])
            except (ValueError, IndexError): return None, 0
    return None, 0

def write_checkpoint(keyword, page_num):
    # <<< SỬA LỖI: THÊM encoding='utf-8' VÀO ĐÂY >>>
    # Đây là nguyên nhân gây ra lỗi nếu keyword là tiếng Trung
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        f.write(f"{keyword},{page_num}")

# --- PHẦN CHÍNH: THU THẬP VÀ XỬ LÝ DỮ LIỆU ---
try:
    all_extracted_data = []
    all_raw_titles = []

    saved_keyword, last_completed_page = read_checkpoint()

    for keyword in SEARCH_KEYWORDS:
        if saved_keyword and SEARCH_KEYWORDS.index(keyword) < SEARCH_KEYWORDS.index(saved_keyword):
            print(f"Bỏ qua từ khóa đã hoàn thành: '{keyword}'")
            continue

        print(f"\n{'='*20} BẮT ĐẦU THU THẬP CHO TỪ KHÓA: '{keyword}' {'='*20}")

        print("Đang kiểm tra tổng số trang...")
        initial_payload = {
            "cid": "vcXSblaG6SxswWniwgOsNTFg1qcaNlvo", "uid": "vcXSblaG6SxswWniwgOsNTFg1qcaNlvo", "query": keyword,
            "current": 1, "size": 20, "disable_correction": False,
            "facets": {"view": [{"type": "value", "name": "view", "sort": {"count": "desc"}, "size": 10}]},
            "input_type": "Input"
        }

        try:
            initial_response = requests.post(api_url, headers=headers, json=initial_payload, timeout=30)
            initial_response.raise_for_status()
            initial_data = initial_response.json()
            total_pages = initial_data.get('result', {}).get('_meta', {}).get('page', {}).get('total_pages', 0)
            if total_pages == 0:
                print(f"Không tìm thấy kết quả cho từ khóa '{keyword}'. Bỏ qua.")
                continue
            print(f"Phát hiện thấy có tổng cộng {total_pages} trang kết quả.")
        except requests.exceptions.RequestException as e:
            print(f"Lỗi nghiêm trọng khi lấy tổng số trang cho từ khóa '{keyword}'. Lỗi: {e}")
            continue
        
        start_page = 1
        if keyword == saved_keyword: start_page = last_completed_page + 1
        
        if start_page > total_pages:
            print(f"Checkpoint cho thấy đã thu thập xong từ khóa '{keyword}'. Bỏ qua.")
            continue

        for page_num in range(start_page, total_pages + 1):
            payload = initial_payload.copy()
            payload['current'] = page_num
            print(f"--- Đang thu thập trang {page_num}/{total_pages} (Từ khóa: '{keyword}') ---")

            response = None
            for attempt in range(retry_attempts):
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                    response.raise_for_status(); break
                except requests.exceptions.RequestException as req_err:
                    print(f"  Lỗi kết nối (lần {attempt + 1}/{retry_attempts}): {req_err}"); time.sleep(retry_delay)
            if response is None: continue
            
            try: data = response.json(); results = data.get('result', {}).get('items', [])
            except json.JSONDecodeError: print(f"  Không thể phân tích JSON. Bỏ qua."); continue

            if not results: print(f"Trang {page_num} không có dữ liệu."); break

            for item in results:
                full_title = item.get('title', {}).get('raw', '').strip()
                date_string = item.get('date', {}).get('raw', '').strip()
                
                if full_title and date_string:
                    all_raw_titles.append(full_title)
                    district, address = parse_title_hybrid(full_title)
                    parts = date_string.split('-')
                    year, month, day = (parts[0], parts[1], parts[2]) if len(parts) == 3 else ("", "", "")
                    all_extracted_data.append({'区': district, '地址': address, '年': year, '月': month, '日': day})

            write_checkpoint(keyword, page_num)
            print(f"  Đã xử lý xong trang {page_num}. Đã lưu checkpoint.")
            time.sleep(request_delay)
    
    # (Phần ghi dữ liệu ra file không thay đổi)
    print(f"\n>>> TOÀN BỘ QUÁ TRÌNH THU THẬP HOÀN TẤT. {len(all_extracted_data)} tiêu đề hợp lệ đã được xử lý. <<<\n")
    if all_raw_titles:
        with open(txt_filename, 'a', encoding='utf-8') as f:
            f.write('\n'.join(all_raw_titles) + '\n')
        print(f"Đã thêm {len(all_raw_titles)} tiêu đề thô vào file '{txt_filename}'")

    if all_extracted_data:
        columns_order = ['区', '地址', '年', '月', '日']
        new_df = pd.DataFrame(all_extracted_data)[columns_order]
        try:
            book = load_workbook(excel_filename)
            sheet = book[sheet_name_to_update] if sheet_name_to_update in book.sheetnames else book.create_sheet(sheet_name_to_update)
            last_data_row = find_last_row_with_data(sheet)
            start_row = last_data_row + 1
            if start_row <= 1:
                headers_list = list(new_df.columns)
                for col_idx, header_value in enumerate(headers_list, start=2): sheet.cell(row=1, column=col_idx, value=header_value)
                start_row = 2
            print(f"Đang ghi {len(new_df)} dòng dữ liệu mới vào sheet '{sheet_name_to_update}' bắt đầu từ hàng {start_row}...")
            for i, row_data in new_df.iterrows():
                current_row = start_row + i
                for col_idx, col_name in enumerate(columns_order, start=2):
                    sheet.cell(row=current_row, column=col_idx, value=row_data[col_name])
            book.save(excel_filename)
            print("Hoàn tất! File Excel đã được cập nhật thành công.")
        except FileNotFoundError: print(f"Lỗi: Không tìm thấy file Excel '{excel_filename}'.")
        except Exception as ex: print(f"Lỗi khi ghi file Excel: {ex}")
    else:
        print("Không có dữ liệu mới hợp lệ để ghi vào file Excel.")
except Exception as e:
    print(f"Đã xảy ra một lỗi không mong muốn: {e}")