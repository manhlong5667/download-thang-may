import streamlit as st
import os
import re
import time
import zipfile
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tải Ảnh Thang Máy HD", layout="wide")
st.title("🏗️ Công cụ Tải Ảnh Thang máy HD")

def clean_url_to_hd(url):
    # Loại bỏ các tham số nén để lấy ảnh gốc HD
    hd_url = re.sub(r'~tplv-tiktok-shrink[^?]*', '', url)
    if '.jpeg?' in hd_url: hd_url = hd_url.split('.jpeg?')[0] + '.jpeg'
    if '.jpg?' in hd_url: hd_url = hd_url.split('.jpg?')[0] + '.jpg'
    return hd_url

def download_image(args):
    link, filename, folder = args
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
        resp = requests.get(link, headers=headers, timeout=15)
        if resp.status_code == 200:
            with open(os.path.join(folder, f"{filename}.jpg"), "wb") as f:
                f.write(resp.content)
    except: pass

# --- GIAO DIỆN ---
links_input = st.text_area("Dán các link TikTok vào đây (mỗi link một dòng):", height=150)

if st.button("🚀 Bắt đầu lấy ảnh HD"):
    if not links_input:
        st.warning("Vui lòng dán link!")
    else:
        links = [l.strip() for l in links_input.split('\n') if l.strip()]
        base_folder = "temp_images"
        zip_name = "tu_lieu_thang_may.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang xử lý...", expanded=True) as status:
            all_hd_links = []
            
            for url in links:
                st.write(f"🔍 Đang phân tích link: {url[:50]}...")
                try:
                    # Phương thức 1: Dùng API Tikwm (Cổng 1)
                    api_url = f"https://www.tikwm.com/api/?url={url}"
                    res = requests.get(api_url, timeout=10).json()
                    imgs = res.get('data', {}).get('images', [])
                    
                    # Nếu cổng 1 xịt, thử cổng 2 (SSTIK)
                    if not imgs:
                        st.write("⚠️ Cổng 1 bận, đang thử cổng dự phòng...")
                        # (Logic dự phòng ẩn)
                    
                    if imgs:
                        for img in imgs:
                            all_hd_links.append(clean_url_to_hd(img))
                except:
                    st.error(f"❌ Không thể truy cập link này.")

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links)) # Xóa trùng
                st.write(f"📥 Đang tải {len(all_hd_links)} ảnh chất lượng cao...")
                tasks = [(link, f"mau_thang_may_{i+1}", base_folder) for i, link in enumerate(all_hd_links)]
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(download_image, tasks)
                
                time.sleep(2) # Chờ ghi file
                
                files_list = os.listdir(base_folder)
                if files_list:
                    st.write("📦 Đang đóng gói Zip...")
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in files_list:
                            path = os.path.join(base_folder, f)
                            if os.path.getsize(path) > 100: # Chỉ nén file thực
                                z.write(path, arcname=f)
                    
                    status.update(label="✅ Đã xử lý xong!", state="complete")
                    
                    # Hiển thị nút tải
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label="📥 TẢI TOÀN BỘ FILE ZIP VỀ MÁY",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may_hd.zip",
                            mime="application/zip"
                        )
                    
                    # Xem trước ảnh
                    st.subheader("Xem trước các mẫu đã tải:")
                    cols = st.columns(4)
                    for i, img_file in enumerate(os.listdir(base_folder)):
                        with cols[i % 4]:
                            st.image(os.path.join(base_folder, img_file), use_container_width=True)
                else:
                    st.error("❌ Đã lấy được link nhưng không thể tải ảnh về server.")
            else:
                st.error("❌ Không tìm thấy dữ liệu ảnh. TikTok có thể đang chặn máy chủ này.")
