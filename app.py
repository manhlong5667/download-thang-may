import streamlit as st
import os
import re
import time
import zipfile
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Tư liệu Thang máy", layout="wide")
st.title("🏗️ Công cụ Quản lý Ảnh Thang máy HD")
st.markdown("Dán link TikTok vào ô dưới đây để xem và tải trọn bộ ảnh mẫu chất lượng cao.")

def clean_url_to_hd(url):
    # Xóa lệnh nén nhưng giữ lại chìa khóa bảo mật để không bị lỗi 403
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

# --- PHẦN NHẬP LIỆU ---
links_input = st.text_area("Danh sách link TikTok (mỗi dòng một link):", height=150)

if st.button("🚀 Bắt đầu xử lý"):
    if not links_input:
        st.warning("Vui lòng dán ít nhất một đường dẫn!")
    else:
        links = [l.strip() for l in links_input.split('\n') if l.strip()]
        base_folder = "kho_anh_tam"
        zip_name = "bo_suu_tap_thang_may.zip"
        
        # Làm sạch dữ liệu cũ
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)
        if os.path.exists(zip_name): os.remove(zip_name)

        with st.status("🔄 Hệ thống đang truy quét dữ liệu...", expanded=True) as status:
            all_hd_links = []
            for url in links:
                try:
                    res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=15).json()
                    imgs = res.get('data', {}).get('images', [])
                    if imgs:
                        all_hd_links.extend([clean_url_to_hd(img) for img in imgs])
                except: pass

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links)) # Lọc trùng
                
                # Bước 1: Tải về server để nén Zip
                st.write(f"📥 Đang tải {len(all_hd_links)} ảnh về hệ thống...")
                tasks = [(link, f"thang_may_hd_{i+1}", base_folder) for i, link in enumerate(all_hd_links)]
                with ThreadPoolExecutor(max_workers=8) as executor:
                    executor.map(download_image_task, tasks)
                
                time.sleep(2) # Chờ ghi đĩa
                
                # Bước 2: Đóng gói Zip
                valid_files = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                if valid_files:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in valid_files:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label="✅ Đã xử lý xong!", state="complete")
                    
                    # --- NÚT TẢI FILE ZIP (HIỆN TRÊN CÙNG CHO TIỆN) ---
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label="📥 TẢI TOÀN BỘ FILE ZIP (MỌI ẢNH)",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may_HD.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    st.divider()
                    
                    # --- HIỂN THỊ XEM TRƯỚC TỪNG ẢNH ---
                    st.subheader("🖼️ Xem chi tiết từng ảnh:")
                    cols = st.columns(3)
                    for i, img_file in enumerate(valid_files):
                        img_path = os.path.join(base_folder, img_file)
                        with cols[i % 3]:
                            st.image(img_path, use_container_width=True)
                            # Nút xem ảnh gốc nếu muốn lưu lẻ
                            st.markdown(f'<a href="{all_hd_links[i]}" target="_blank" style="text-decoration:none;"><button style="width:100%; border-radius:5px; background-color:#f0f2f6; color:#31333F; border:1px solid #d1d5db; padding:5px; margin-bottom:20px; cursor:pointer;">Mở ảnh gốc</button></a>', unsafe_allow_html=True)
                else:
                    st.error("❌ Không thể tải ảnh về máy chủ do TikTok chặn IP. Hãy thử lại sau ít phút.")
            else:
                st.error("❌ Không tìm thấy dữ liệu ảnh. Vui lòng kiểm tra lại link.")
