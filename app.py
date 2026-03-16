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

# --- CHỨC NĂNG BẢO MẬT ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔐 Truy cập nội bộ")
    password = st.text_input("Nhập mật khẩu để tiếp tục:", type="password")
    
    if st.button("Đăng nhập"):
        if password == "55555":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Mật khẩu không chính xác!")
    return False

# Kiểm tra mật khẩu trước khi chạy app
if check_password():
    st.title("🏗️ Công cụ Quản lý & Xem Ảnh Thang máy HD")

    def clean_url_to_hd(url):
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

    # --- GIAO DIỆN CHÍNH ---
    links_input = st.text_area("Dán các link TikTok vào đây (Mỗi dòng 1 link):", height=150)

    if st.button("🚀 Bắt đầu lấy tất cả ảnh"):
        valid_links = [l.strip() for l in links_input.split('\n') if "tiktok.com" in l]
        
        if not valid_links:
            st.warning("Vui lòng dán link TikTok hợp lệ!")
        else:
            base_folder = "anh_thang_may_temp"
            zip_name = "bo_suu_tap_hd.zip"
            
            if os.path.exists(base_folder): shutil.rmtree(base_folder)
            os.makedirs(base_folder)

            with st.status("🔄 Đang xử lý dữ liệu...", expanded=True) as status:
                final_photo_links = []
                
                for i, link in enumerate(valid_links):
                    st.write(f"🔍 Đang quét link {i+1}...")
                    for _ in range(3):
                        try:
                            res = requests.get(f"https://www.tikwm.com/api/?url={link}", timeout=20).json()
                            imgs = res.get('data', {}).get('images', [])
                            if imgs:
                                final_photo_links.extend([clean_url_to_hd(img) for img in imgs])
                                st.write(f"✅ Link {i+1}: Tìm thấy {len(imgs)} ảnh.")
                                break
                            time.sleep(1)
                        except:
                            time.sleep(1)

                if final_photo_links:
                    final_photo_links = list(dict.fromkeys(final_photo_links))
                    st.write(f"📥 Đang tải {len(final_photo_links)} ảnh...")
                    
                    tasks = [(l, f"thang_may_{idx+1}", base_folder) for idx, l in enumerate(final_photo_links)]
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        executor.map(download_image_task, tasks)
                    
                    time.sleep(2)
                    
                    files_to_zip = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                    if files_to_zip:
                        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                            for f in files_to_zip:
                                z.write(os.path.join(base_folder, f), arcname=f)
                        
                        status.update(label="✅ Đã xử lý xong!", state="complete")
                        
                        # Nút tải Zip
                        with open(zip_name, "rb") as f:
                            st.download_button(
                                label="📥 TẢI TOÀN BỘ FILE ZIP",
                                data=f.read(),
                                file_name="bo_suu_tap_thang_may.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                        
                        # Hiển thị ảnh mẫu trực tiếp
                        st.divider()
                        st.subheader("🖼️ Xem chi tiết các mẫu đã tìm thấy:")
                        cols = st.columns(4)
                        for k, img_file in enumerate(files_to_zip):
                            with cols[k % 4]:
                                st.image(os.path.join(base_folder, img_file), use_container_width=True)
                                st.markdown(f'<a href="{final_photo_links[k]}" target="_blank" style="text-decoration:none;"><button style="width:100%; border-radius:5px; background-color:#f0f2f6; border:1px solid #d1d5db; padding:5px; cursor:pointer; font-size:12px;">Mở ảnh HD</button></a>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Không tải được ảnh về server.")
                else:
                    st.error("❌ Không lấy được dữ liệu ảnh.")
