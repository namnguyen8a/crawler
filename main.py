import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from openpyxl import load_workbook

# --- CẤU HÌNH ---
url = 'https://www.shyp.gov.cn/shypq/yqyw-wb-gtjzl-gsgg-fags/index.html'
txt_filename = 'crawled_titles.txt'
excel_filename = '模版.xlsx'
sheet_name_to_update = 'shanghai'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- PHẦN 1: THU THẬP VÀ XỬ LÝ DỮ LIỆU (KHÔNG THAY ĐỔI) ---
try:
    print(f"Đang kết nối đến {url}...")
    # ... (Toàn bộ phần code crawl và trích xuất dữ liệu vẫn giữ nguyên như trước)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')
    list_items = soup.select('ul.uli16.nowrapli.padding-top-10.list-date.border li')
    
    extracted_data = []
    raw_titles = []
    common_suffix = "既有多层住宅加装电梯工程规划设计方案公示"

    print("Bắt đầu thu thập và trích xuất dữ liệu...")
    for item in list_items:
        date_tag = item.find('span', class_='time')
        title_tag = item.find('a')
        if date_tag and title_tag:
            full_title = title_tag.get_text(strip=True)
            raw_titles.append(full_title)
            
            district, address = "Không xác định", "Không xác định"
            if '区' in full_title:
                district_end_index = full_title.find('区') + 1
                district = full_title[:district_end_index]
                address_part = full_title[district_end_index:]
                address = address_part.replace(common_suffix, "").strip()

            extracted_data.append({
                '区': district, '地址': address, '公告日期': date_tag.get_text(strip=True)
            })

    if raw_titles:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(raw_titles))
        print(f"Hoàn tất! Đã lưu {len(raw_titles)} tiêu đề thô vào file '{txt_filename}'")


    # --- PHẦN 2: GHI FILE EXCEL CHÍNH XÁC VÀO TỪNG Ô ---
    if extracted_data:
        new_df = pd.DataFrame(extracted_data)[['区', '地址', '公告日期']]

        # Tải workbook hiện có
        book = load_workbook(excel_filename)
        
        # Lấy sheet cần cập nhật
        if sheet_name_to_update in book.sheetnames:
            sheet = book[sheet_name_to_update]
        else:
            sheet = book.create_sheet(sheet_name_to_update)
            # Nếu là sheet mới, ghi header bắt đầu từ cột B
            headers_list = list(new_df.columns)
            sheet.cell(row=1, column=2, value=headers_list[0]) # Cột B
            sheet.cell(row=1, column=3, value=headers_list[1]) # Cột C
            sheet.cell(row=1, column=4, value=headers_list[2]) # Cột D

        # Tìm hàng trống tiếp theo để bắt đầu ghi dữ liệu
        start_row = sheet.max_row + 1

        # Lặp qua từng dòng dữ liệu mới và ghi vào các ô cụ thể
        print(f"Đang ghi dữ liệu mới vào sheet '{sheet_name_to_update}' bắt đầu từ cột B...")
        for i, row_data in new_df.iterrows():
            current_row = start_row + i
            # Ghi dữ liệu vào cột B, C, D
            sheet.cell(row=current_row, column=2, value=row_data['区'])      # Cột B (index 2)
            sheet.cell(row=current_row, column=3, value=row_data['地址'])    # Cột C (index 3)
            sheet.cell(row=current_row, column=4, value=row_data['公告日期']) # Cột D (index 4)
        
        # Lưu lại toàn bộ workbook
        book.save(excel_filename)
        
        print("Hoàn tất! File đã được cập nhật thành công.")
    else:
        print("Không tìm thấy dữ liệu đã trích xuất để lưu vào file Excel.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")