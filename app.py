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
    # Xóa lệnh nén, giữ lại chìa khóa bảo mật
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

# --- GIAO DIỆN ---
links_input = st.text_area("Dán các link TikTok vào đây (Mỗi dòng 1 link):", height=150, placeholder="https://www.tiktok.com/...\nhttps://www.tiktok.com/...")

if st.button("🚀 Bắt đầu lấy tất cả ảnh"):
    # Tách link và làm sạch
    raw_list = links_input.split('\n')
    links = [l.strip() for l in raw_list if "tiktok.com" in l]
    
    if not links:
        st.warning("Vui lòng dán link TikTok hợp lệ!")
    else:
        base_folder = "tong_hop_anh"
        zip_name = "tu_lieu_thang_may_hd.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang gom dữ liệu từ các link...", expanded=True) as status:
            all_hd_links = []
            
            for i, url in enumerate(links):
                st.write(f"🔍 Đang quét link {i+1}...")
                try:
                    res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=15).json()
                    imgs = res.get('data', {}).get('images', [])
                    if imgs:
                        for img in imgs:
                            all_hd_links.append(clean_url_to_hd(img))
                except:
                    st.error(f"Lỗi tại link thứ {i+1}")

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links)) # Lọc trùng
                st.write(f"📥 Đang tải {len(all_hd_links)} ảnh về hệ thống...")
                
                tasks = [(link, f"mau_thang_may_{j+1}", base_folder) for j, link in enumerate(all_hd_links)]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(download_image_task, tasks)
                
                time.sleep(2) # Chờ ghi file
                
                # Đóng gói Zip
                valid_files = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                if valid_files:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in valid_files:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label=f"✅ Hoàn tất! Đã gom ảnh từ {len(links)} link.", state="complete")
                    
                    # Nút tải Zip
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label=f"📂 TẢI VỀ TẤT CẢ {len(valid_files)} ẢNH (ZIP)",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    # Hiển thị ảnh xem trước
                    st.divider()
                    st.subheader("🖼️ Danh sách ảnh đã tìm thấy:")
                    cols = st.columns(4)
                    for k, img_file in enumerate(valid_files):
                        with cols[k % 4]:
                            st.image(os.path.join(base_folder, img_file), use_container_width=True)
                else:
                    st.error("❌ Không tải được ảnh về máy chủ.")
            else:
                st.error("❌ Không tìm thấy ảnh trong các link đã cung cấp.")
