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
            st.write("🔍 Đang quét link...")
            all_hd_links = []
            
            for url in links:
                try:
                    api_res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
                    imgs = api_res.get('data', {}).get('images', [])
                    if imgs:
                        for img in imgs:
                            all_hd_links.append(clean_url_to_hd(img))
                except:
                    st.error(f"Lỗi link: {url}")

            if all_hd_links:
                st.write(f"📥 Đang tải {len(all_hd_links)} ảnh...")
                tasks = [(link, f"anh_{i+1}", base_folder) for i, link in enumerate(all_hd_links)]
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(download_image, tasks)
                
                # Chờ hệ thống ghi file xong
                time.sleep(2)
                
                st.write("📦 Đang đóng gói Zip...")
                with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                    for f in os.listdir(base_folder):
                        path = os.path.join(base_folder, f)
                        if os.path.getsize(path) > 0:
                            z.write(path, arcname=f)
                
                status.update(label="✅ Xong!", state="complete")
                
                # Nút tải về
                with open(zip_name, "rb") as f:
                    st.download_button(
                        label="📥 TẢI FILE ZIP (ẢNH HD)",
                        data=f.read(),
                        file_name="thang_may_hd.zip",
                        mime="application/zip"
                    )
                
                # Xem trước
                st.subheader("Xem trước:")
                cols = st.columns(4)
                for i, img_file in enumerate(os.listdir(base_folder)):
                    with cols[i % 4]:
                        st.image(os.path.join(base_folder, img_file))
            else:
                st.error("Không tìm thấy ảnh!")
