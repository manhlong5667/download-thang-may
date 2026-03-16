import streamlit as st
import os
import re
import requests

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tải Ảnh Thang Máy HD", layout="wide")
st.title("🏗️ Công cụ Tải Ảnh Thang máy HD")

def clean_url_to_hd(url):
    hd_url = re.sub(r'~tplv-tiktok-shrink[^?]*', '', url)
    if '.jpeg?' in hd_url: hd_url = hd_url.split('.jpeg?')[0] + '.jpeg'
    if '.jpg?' in hd_url: hd_url = hd_url.split('.jpg?')[0] + '.jpg'
    return hd_url

# --- GIAO DIỆN ---
links_input = st.text_area("Dán các link TikTok vào đây (mỗi link một dòng):", height=150)

if st.button("🚀 Bắt đầu lấy ảnh HD"):
    if not links_input:
        st.warning("Vui lòng dán link!")
    else:
        links = [l.strip() for l in links_input.split('\n') if l.strip()]
        
        with st.status("🔄 Đang xử lý...", expanded=True) as status:
            all_hd_links = []
            for url in links:
                st.write(f"🔍 Đang phân tích: {url[:40]}...")
                try:
                    res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
                    imgs = res.get('data', {}).get('images', [])
                    if imgs:
                        for img in imgs:
                            all_hd_links.append(clean_url_to_hd(img))
                except:
                    st.error("❌ Không thể kết nối cổng dữ liệu.")

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links)) # Lọc trùng
                status.update(label="✅ Đã tìm thấy ảnh!", state="complete")
                
                st.success(f"Tìm thấy {len(all_hd_links)} ảnh chất lượng cao.")
                st.info("💡 Mẹo: Chuột phải vào ảnh chọn 'Lưu ảnh thành...' hoặc dùng công cụ chụp màn hình để lấy tư liệu nhanh nhất.")
                
                # Hiển thị ảnh kèm nút tải riêng lẻ cho từng ảnh (Tránh lỗi file Zip rỗng)
                cols = st.columns(3)
                for i, img_url in enumerate(all_hd_links):
                    with cols[i % 3]:
                        st.image(img_url, use_container_width=True, caption=f"Ảnh mẫu {i+1}")
                        # Tạo nút tải trực tiếp cho từng ảnh
                        st.markdown(f'<a href="{img_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; border-radius:5px; background-color:#008CBA; color:white; border:none; padding:10px;">Mở ảnh gốc HD</button></a>', unsafe_allow_config=True, unsafe_allow_html=True)
            else:
                st.error("❌ TikTok đã chặn yêu cầu này. Hãy thử lại sau vài phút hoặc dùng link khác.")
