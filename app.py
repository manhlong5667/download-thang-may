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
    if '.webp?' in hd_url: hd_url = hd_url.split('.webp?')[0] + '.webp'
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
                try:
                    res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
                    imgs = res.get('data', {}).get('images', [])
                    if imgs:
                        for img in imgs:
                            all_hd_links.append(clean_url_to_hd(img))
                except:
                    pass

            if all_hd_links:
                all_hd_links = list(dict.fromkeys(all_hd_links)) # Lọc trùng
                status.update(label="✅ Đã tìm thấy ảnh!", state="complete")
                
                st.success(f"Tìm thấy {len(all_hd_links)} ảnh. Bạn có thể xem và tải trực tiếp bên dưới.")
                
                # Hiển thị ảnh theo dạng lưới
                cols = st.columns(3)
                for i, img_url in enumerate(all_hd_links):
                    with cols[i % 3]:
                        st.image(img_url, use_container_width=True)
                        # Nút bấm đã được sửa lỗi tham số
                        st.markdown(
                            f'<a href="{img_url}" target="_blank" style="text-decoration:none;">'
                            f'<button style="width:100%; border-radius:5px; background-color:#008CBA; color:white; border:none; padding:10px; cursor:pointer;">'
                            f'Mở ảnh HD để lưu</button></a>', 
                            unsafe_allow_html=True
                        )
            else:
                st.error("❌ Không tìm thấy dữ liệu. Có thể link bị lỗi hoặc TikTok đang chặn.")
