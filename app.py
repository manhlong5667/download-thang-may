import streamlit as st
import os
import re
import time
import zipfile
import requests
import shutil
from concurrent.futures import ThreadPoolExecutor

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="TikTok Photo Downloader", layout="wide")

# --- LỚP BẢO MẬT ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Hệ thống tải ảnh TikTok")
    pwd = st.text_input("Nhập mật khẩu truy cập:", type="password")
    if st.button("Đăng nhập"):
        if pwd == "55555":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ Mật khẩu không đúng!")
    return False

if check_auth():
    # --- GIAO DIỆN CHÍNH ---
    st.title("📸 TikTok Photo Downloader HD")
    st.markdown("Hỗ trợ tải toàn bộ ảnh từ nhiều link TikTok cùng lúc với chất lượng cao nhất.")

    def clean_hd_link(url):
        return re.sub(r'~tplv-tiktok-shrink:[0-9]+:[0-9]+', '', url)

    def download_image(args):
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

    # Khu vực nhập liệu
    input_text = st.text_area("Dán các link TikTok vào đây (Mỗi dòng một link):", height=150, placeholder="https://www.tiktok.com/...")

    if st.button("🚀 Bắt đầu tải ảnh HD"):
        # Làm sạch danh sách link
        links = [l.strip() for l in input_text.split('\n') if "tiktok.com" in l]
        
        if not links:
            st.warning("Vui lòng nhập ít nhất một đường dẫn TikTok hợp lệ!")
        else:
            save_dir = "tiktok_download_temp"
            zip_file = "tiktok_photos_collection.zip"
            
            if os.path.exists(save_dir): shutil.rmtree(save_dir)
            os.makedirs(save_dir)

            with st.status("🔄 Đang quét dữ liệu từ TikTok...", expanded=True) as status:
                all_images = []
                
                for i, url in enumerate(links):
                    st.write(f"🔍 Đang phân tích link {i+1}...")
                    # Thử lại 3 lần để tránh bị chặn
                    for _ in range(3):
                        try:
                            api_url = f"https://www.tikwm.com/api/?url={url}"
                            res = requests.get(api_url, timeout=20).json()
                            imgs = res.get('data', {}).get('images', [])
                            if imgs:
                                for img in imgs:
                                    all_images.append(clean_hd_link(img))
                                st.write(f"✅ Link {i+1}: Tìm thấy {len(imgs)} ảnh.")
                                break
                            time.sleep(1)
                        except:
                            time.sleep(1)

                if all_images:
                    all_images = list(dict.fromkeys(all_images)) # Xóa ảnh trùng
                    st.write(f"📥 Đang tải {len(all_images)} ảnh về server...")
                    
                    # Tải đa luồng để tăng tốc độ
                    tasks = [(l, f"photo_{idx+1}", save_dir) for idx, l in enumerate(all_images)]
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        executor.map(download_image, tasks)
                    
                    time.sleep(2) # Đợi ghi file hoàn tất
                    
                    # Đóng gói Zip
                    valid_files = [f for f in os.listdir(save_dir) if os.path.getsize(os.path.join(save_dir, f)) > 0]
                    if valid_files:
                        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as z:
                            for f in valid_files:
                                z.write(os.path.join(save_dir, f), arcname=f)
                        
                        status.update(label="✅ Đã xử lý xong!", state="complete")
                        
                        # Nút tải file Zip
                        with open(zip_file, "rb") as f:
                            st.download_button(
                                label="📥 TẢI TOÀN BỘ ẢNH (FILE ZIP)",
                                data=f.read(),
                                file_name="tiktok_collection_hd.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                        
                        # Hiển thị lưới ảnh xem trước
                        st.divider()
                        st.subheader("🖼️ Xem trước ảnh đã bóc tách:")
                        cols = st.columns(4)
                        for k, img_f in enumerate(valid_files):
                            with cols[k % 4]:
                                st.image(os.path.join(save_dir, img_f), use_container_width=True)
                                st.markdown(f'<a href="{all_images[k]}" target="_blank" style="text-decoration:none;"><button style="width:100%; border-radius:5px; background-color:#f0f2f6; border:1px solid #d1d5db; padding:5px; cursor:pointer; font-size:12px;">Mở ảnh HD</button></a>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Đã lấy được link nhưng không thể tải ảnh về server.")
                else:
                    st.error("❌ Không tìm thấy ảnh nào. Vui lòng kiểm tra lại link.")
