import streamlit as st
import os
import re
import time
import zipfile
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Quản lý Tư liệu Thang máy", layout="wide")
st.title("🏗️ Công cụ Tải Ảnh Thang máy HD")
st.markdown("Nhập link TikTok vào bên dưới để lấy ảnh chất lượng cao phục vụ tư vấn kỹ thuật.")

# --- CÁC HÀM XỬ LÝ (GIỮ NGUYÊN LOGIC HD CỦA BẠN) ---
def clean_url_to_hd(url):
    hd_url = re.sub(r'~tplv-tiktok-shrink[^?]*', '', url)
    if '.jpeg?' in hd_url: hd_url = hd_url.split('.jpeg?')[0] + '.jpeg'
    if '.jpg?' in hd_url: hd_url = hd_url.split('.jpg?')[0] + '.jpg'
    return hd_url

def download_image(args):
    link, filename, folder = args
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(link, headers=headers, timeout=15)
        if resp.status_code == 200:
            with open(os.path.join(folder, f"{filename}.jpg"), "wb") as f:
                f.write(resp.content)
    except: pass

# --- GIAO DIỆN NGƯỜI DÙNG ---
with st.sidebar:
    st.header("Cài đặt")
    st.info("Tool này chuyên dụng để lấy ảnh mẫu thang máy từ TikTok.")
    clear_cache = st.button("Dọn dẹp bộ nhớ tạm")

links_input = st.text_area("Dán các link TikTok (mỗi link một dòng):", height=150)

if st.button("🚀 Bắt đầu lấy ảnh HD"):
    if not links_input:
        st.warning("Vui lòng dán ít nhất một link!")
    else:
        links = [l.strip() for l in links_input.split('\n') if l.strip()]
        base_folder = "temp_images"
        zip_name = "tu_lieu_thang_may.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang xử lý dữ liệu...", expanded=True) as status:
            st.write("🔍 Đang truy quét link ảnh gốc...")
            all_hd_links = []
            
            for url in links:
                try:
                    # Sử dụng API trung gian để ổn định trên môi trường Web
                    api_res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
                    imgs = api_res.get('data', {}).get('images', [])
                    if imgs:
                        all_hd_links.extend([clean_url_to_hd(img) for img in imgs])
                except:
                    st.error(f"Lỗi khi truy cập link: {url}")

            if all_hd_links:
                st.write(f"📥 Tìm thấy {len(all_hd_links)} ảnh. Đang tải về...")
                tasks = [(link, f"thang_may_hd_{i+1}", base_folder) for i, link in enumerate(all_hd_links)]
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(download_image, tasks)
                
                st.write("📦 Đang nén file...")
                with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                    for f in os.listdir(base_folder):
                        z.write(os.path.join(base_folder, f), arcname=f)
                
                status.update(label="✅ Đã xử lý xong!", state="complete", expanded=False)
                
                # --- NÚT TẢI FILE ZIP ---
                with open(zip_name, "rb") as f:
                    st.download_button(
                        label="📥 TẢI TOÀN BỘ FILE ZIP VỀ MÁY",
                        data=f,
                        file_name="bo_suu_tap_thang_may_hd.zip",
                        mime="application/zip"
                    )
                
                # Hiển thị ảnh xem trước
                st.subheader("Xem trước ảnh đã tải:")
                cols = st.columns(3)
                for i, img_file in enumerate(os.listdir(base_folder)):
                    with cols[i % 3]:
                        st.image(os.path.join(base_folder, img_file))
            else:
                st.error("Không tìm thấy ảnh nào. Vui lòng kiểm tra lại link!")
