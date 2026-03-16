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
links_input = st.text_area("Dán các link TikTok vào đây (Mỗi dòng 1 link):", height=150)

if st.button("🚀 Bắt đầu lấy tất cả ảnh"):
    # Tách link và làm sạch tuyệt đối
    lines = links_input.split('\n')
    valid_links = []
    for line in lines:
        clean_line = line.strip()
        if "tiktok.com" in clean_line:
            valid_links.append(clean_line)
    
    if not valid_links:
        st.warning("Vui lòng dán link TikTok hợp lệ!")
    else:
        base_folder = "tong_hop_anh"
        zip_name = "bo_suu_tap_thang_may_hd.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang xử lý đa luồng...", expanded=True) as status:
            final_photo_links = []
            
            # QUÉT TỪNG LINK MỘT
            for i, link in enumerate(valid_links):
                st.write(f"🔍 Đang bóc tách dữ liệu link {i+1}: {link[:40]}...")
                try:
                    # Gọi API lấy ảnh
                    response = requests.get(f"https://www.tikwm.com/api/?url={link}", timeout=20).json()
                    data = response.get('data', {})
                    imgs = data.get('images', [])
                    
                    if imgs:
                        count_before = len(final_photo_links)
                        for img_url in imgs:
                            hd_url = clean_url_to_hd(img_url)
                            final_photo_links.append(hd_url)
                        st.write(f"✅ Tìm thấy {len(final_photo_links) - count_before} ảnh từ link này.")
                    else:
                        st.error(f"⚠️ Link {i+1} không chứa ảnh hoặc bị TikTok chặn.")
                except Exception as e:
                    st.error(f"❌ Lỗi tại link {i+1}: {str(e)}")

            # Sau khi gom tất cả link ảnh từ mọi nguồn
            if final_photo_links:
                final_photo_links = list(dict.fromkeys(final_photo_links)) # Xóa trùng
                st.write(f"📥 Tổng cộng có {len(final_photo_links)} ảnh cần tải. Bắt đầu tải về...")
                
                tasks = [(l, f"thang_may_{idx+1}", base_folder) for idx, l in enumerate(final_photo_links)]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(download_image_task, tasks)
                
                time.sleep(2) # Chờ ghi file vào bộ nhớ Cloud
                
                # Nén Zip
                files_to_zip = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                if files_to_zip:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in files_to_zip:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label=f"✅ Xong! Tổng hợp thành công {len(files_to_zip)} ảnh.", state="complete")
                    
                    # Hiển thị nút tải
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label=f"📂 TẢI VỀ TẤT CẢ {len(files_to_zip)} ẢNH (ZIP)",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    # Xem trước
                    st.divider()
                    cols = st.columns(4)
                    for k, img_file in enumerate(files_to_zip):
                        with cols[k % 4]:
                            st.image(os.path.join(base_folder, img_file), use_container_width=True)
                else:
                    st.error("❌ Link đã nhận nhưng không thể tải ảnh về máy chủ.")
            else:
                st.error("❌ Không lấy được bất kỳ ảnh nào từ các link trên.")
