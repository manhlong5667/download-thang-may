import streamlit as st
import os
import re
import time
import zipfile
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Tư liệu Thang máy", layout="wide")
st.title("🏗️ Công cụ Quản lý Ảnh Thang máy HD")

def clean_url_to_hd(url):
    # Xóa lệnh nén, giữ lại token bảo mật
    hd_url = re.sub(r'~tplv-tiktok-shrink:[0-9]+:[0-9]+', '', url)
    return hd_url

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

# --- GIAO DIỆN ---
links_input = st.text_area("Dán các link TikTok vào đây (mỗi link một dòng):", height=150, placeholder="Dán link 1...\nDán link 2...")

if st.button("🚀 Bắt đầu lấy tất cả ảnh"):
    # Tách link và loại bỏ khoảng trắng thừa
    raw_links = links_input.split('\n')
    links = [l.strip() for l in raw_links if "tiktok.com" in l]
    
    if not links:
        st.warning("Vui lòng dán link TikTok hợp lệ!")
    else:
        base_folder = "tong_hop_anh"
        zip_name = "bo_suu_tap_thang_may.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang quét từng link một...", expanded=True) as status:
            all_hd_links = []
            
            # VÒNG LẶP XỬ LÝ TỪNG LINK
            for index, url in enumerate(links):
                st.write(f"正在 quét link thứ {index+1}...")
                try:
                    res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=15).json()
                    imgs = res.get('data', {}).get('images', [])
                    if imgs:
                        # Gom hết link ảnh HD vào danh sách chung
                        for img in imgs:
                            all_hd_links.append(clean_url_to_hd(img))
                except:
                    st.error(f"Lỗi khi đọc link {index+1}")

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links)) # Lọc trùng
                st.write(f"📥 Đang tải tổng cộng {len(all_hd_links)} ảnh từ tất cả các link...")
                
                # Tải ảnh song song
                tasks = [(link, f"anh_mau_{i+1}", base_folder) for i, link in enumerate(all_hd_links)]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(download_image_task, tasks)
                
                time.sleep(2)
                
                # Nén Zip
                valid_files = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                if valid_files:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in valid_files:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label=f"✅ Xong! Đã gom ảnh từ {len(links)} link.", state="complete")
                    
                    # Nút tải Zip
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label=f"📂 TẢI VỀ TẤT CẢ {len(valid_files)} ẢNH (ZIP)",
                            data=f.read(),
                            file_name="tong_hop_thang_may_hd.zip",
                            mime="application/zip",
