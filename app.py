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
st.title("🏗️ Công cụ Tải Ảnh Thang máy HD")

def clean_url_to_hd(url):
    # Xóa lệnh nén nhưng giữ lại token bảo mật
    hd_url = re.sub(r'~tplv-tiktok-shrink:[0-9]+:[0-9]+', '', url)
    return hd_url

def download_image_task(args):
    link, filename, folder = args
    try:
        # Header giả lập trình duyệt Chrome thật để tránh bị chặn 403
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
links_input = st.text_area("Dán các link TikTok vào đây (mỗi link một dòng):", height=150)

if st.button("🚀 Bắt đầu lấy ảnh HD"):
    if not links_input:
        st.warning("Vui lòng dán link!")
    else:
        links = [l.strip() for l in links_input.split('\n') if l.strip()]
        base_folder = "folder_thang_may"
        zip_name = "bo_suu_tap_hd.zip"
        
        # Dọn dẹp thư mục cũ
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)
        if os.path.exists(zip_name): os.remove(zip_name)

        with st.status("🔄 Hệ thống đang làm việc...", expanded=True) as status:
            all_hd_links = []
            for url in links:
                try:
                    res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
                    imgs = res.get('data', {}).get('images', [])
                    if imgs:
                        all_hd_links.extend([clean_url_to_hd(img) for img in imgs])
                except: pass

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links))
                st.write(f"📥 Đang tải {len(all_hd_links)} ảnh về máy chủ...")
                
                # Tải ảnh song song để tăng tốc
                tasks = [(link, f"thang_may_{i+1}", base_folder) for i, link in enumerate(all_hd_links)]
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(download_image_task, tasks)
                
                # Chờ một chút để đảm bảo file đã ghi xong
                time.sleep(2)
                
                # Đóng gói Zip
                st.write("📦 Đang nén file Zip...")
                valid_files = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                
                if valid_files:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in valid_files:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label="✅ Đã chuẩn bị xong file Zip!", state="complete")
                    
                    # NÚT TẢI TOÀN BỘ
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label="📂 TẢI TOÀN BỘ ẢNH (FILE ZIP)",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may_hd.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    # Hiển thị xem trước
                    st.divider()
                    st.subheader("Xem trước tư liệu:")
                    cols = st.columns(4)
                    for i, img_file in enumerate(valid_files):
                        with cols[i % 4]:
                            st.image(os.path.join(base_folder, img_file), use_container_width=True)
                else:
                    st.error("❌ Máy chủ bị chặn không thể tải ảnh. Hãy dùng nút 'Mở ảnh' lẻ hoặc thử lại sau.")
            else:
                st.error("❌ Không tìm thấy link ảnh.")
