import streamlit as st
import os
import re
import time
import zipfile
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Kho Ảnh Thang Máy HD", layout="wide")
st.title("🏗️ Hệ thống Quản lý & Tải Ảnh Thang máy HD")

def clean_url_to_hd(url):
    # Loại bỏ lệnh nén để lấy ảnh gốc HD
    return re.sub(r'~tplv-tiktok-shrink:[0-9]+:[0-9]+', '', url)

def download_image_task(args):
    link, filename, folder = args
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
        resp = requests.get(link, headers=headers, timeout=20)
        if resp.status_code == 200:
            with open(os.path.join(folder, f"{filename}.jpg"), "wb") as f:
                f.write(resp.content)
            return True
    except:
        return False

# --- GIAO DIỆN NHẬP LIỆU ---
links_input = st.text_area("Dán các link TikTok vào đây (Mỗi dòng một link):", height=150)

if st.button("🚀 Bắt đầu xử lý tất cả link"):
    valid_links = [l.strip() for l in links_input.split('\n') if "tiktok.com" in l]
    
    if not valid_links:
        st.warning("Vui lòng dán link TikTok hợp lệ!")
    else:
        base_folder = "kho_anh_thang_may"
        zip_name = "bo_suu_tap_thang_may_hd.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang xử lý dữ liệu...", expanded=True) as status:
            final_photo_links = []
            
            # Quét từng link một để lấy dữ liệu
            for i, link in enumerate(valid_links):
                st.write(f"🔍 Đang kiểm tra link {i+1}...")
                for attempt in range(3): # Thử lại 3 lần nếu bị chặn
                    try:
                        response = requests.get(f"https://www.tikwm.com/api/?url={link}", timeout=20).json()
                        imgs = response.get('data', {}).get('images', [])
                        if imgs:
                            for img_url in imgs:
                                final_photo_links.append(clean_url_to_hd(img_url))
                            st.write(f"✅ Link {i+1}: Đã lấy được ảnh.")
                            break
                        time.sleep(1)
                    except:
                        time.sleep(1)

            if final_photo_links:
                final_photo_links = list(dict.fromkeys(final_photo_links)) # Lọc trùng
                
                # Tải ảnh về máy chủ để nén và hiển thị
                tasks = [(l, f"anh_thang_may_{idx+1}", base_folder) for idx, l in enumerate(final_photo_links)]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(download_image_task, tasks)
                
                time.sleep(2)
                
                # Nén file Zip
                files_to_zip = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                if files_to_zip:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in files_to_zip:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label="✅ Hoàn tất!", state="complete")
                    
                    # 1. NÚT TẢI TOÀN BỘ FILE ZIP
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label=f"📂 TẢI TOÀN BỘ {len(files_to_zip)} ẢNH (FILE ZIP)",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    # 2. CHỨC NĂNG XEM ẢNH TRỰC TIẾP
                    st.
