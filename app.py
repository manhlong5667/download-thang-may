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
    lines = links_input.split('\n')
    valid_links = [l.strip() for l in lines if "tiktok.com" in l]
    
    if not valid_links:
        st.warning("Vui lòng dán link TikTok hợp lệ!")
    else:
        base_folder = "tong_hop_anh"
        zip_name = "bo_suu_tap_thang_may_hd.zip"
        
        if os.path.exists(base_folder): shutil.rmtree(base_folder)
        os.makedirs(base_folder)

        with st.status("🔄 Đang xử lý dữ liệu...", expanded=True) as status:
            final_photo_links = []
            
            for i, link in enumerate(valid_links):
                st.write(f"🔍 Đang bóc tách link {i+1}...")
                success = False
                # Thử lại 3 lần nếu bị chặn
                for attempt in range(3):
                    try:
                        response = requests.get(f"https://www.tikwm.com/api/?url={link}", timeout=20).json()
                        imgs = response.get('data', {}).get('images', [])
                        if imgs:
                            for img_url in imgs:
                                final_photo_links.append(clean_url_to_hd(img_url))
                            st.write(f"✅ Link {i+1}: Tìm thấy {len(imgs)} ảnh.")
                            success = True
                            break
                        else:
                            time.sleep(1) # Đợi 1 giây trước khi thử lại
                    except:
                        time.sleep(1)
                
                if not success:
                    st.error(f"❌ Link {i+1} vẫn bị chặn sau 3 lần thử. Hãy kiểm tra lại link này.")

            if final_photo_links:
                final_photo_links = list(dict.fromkeys(final_photo_links))
                st.write(f"📥 Đang tải {len(final_photo_links)} ảnh về...")
                
                tasks = [(l, f"thang_may_{idx+1}", base_folder) for idx, l in enumerate(final_photo_links)]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    executor.map(download_image_task, tasks)
                
                time.sleep(2)
                
                files_to_zip = [f for f in os.listdir(base_folder) if os.path.getsize(os.path.join(base_folder, f)) > 0]
                if files_to_zip:
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in files_to_zip:
                            z.write(os.path.join(base_folder, f), arcname=f)
                    
                    status.update(label="✅ Đã hoàn thành!", state="complete")
                    
                    with open(zip_name, "rb") as f:
                        st.download_button(
                            label=f"📂 TẢI VỀ TẤT CẢ {len(files_to_zip)} ẢNH (ZIP)",
                            data=f.read(),
                            file_name="bo_suu_tap_thang_may.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    st.divider()
                    st.subheader("🖼️ Xem trước ảnh:")
                    cols = st.columns(4)
                    for k, img_file in enumerate(files_to_zip):
                        with cols[k % 4]:
                            st.image(os.path.join(base_folder, img_file), use_container_width=True)
