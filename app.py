import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import qrcode
from io import BytesIO
import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI HÀNH CHÍNH XÃ (FREE GEMINI)", layout="wide", page_icon="🇻🇳")

# (Phần DATA_HANH_CHINH và LOAI_VAN_BAN giữ nguyên như bản trước)
DATA_HANH_CHINH = {"Tuyên Quang": ["Lâm Bình", "Thác Bà"], "Hà Nội": ["Đông Anh", "Ba Đình"], "TP.HCM": ["Cần Giờ", "Bình Chánh"]}
LOAI_VB = ["Công văn (CV)", "Biên bản (BB)", "Quyết định (QĐ)", "Thông báo (TB)", "Báo cáo (BC)"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 CẤU HÌNH")
    gemini_key = st.text_input("Gemini API Key (Miễn phí)", type="password", help="Lấy tại aistudio.google.com")
    tinh = st.selectbox("Chọn Tỉnh/Thành", list(DATA_HANH_CHINH.keys()))
    xa = st.selectbox("Chọn Xã/Phường", DATA_HANH_CHINH[tinh])
    chu_tich = st.text_input("Chủ tịch UBND", "Nguyễn Văn A")

# --- GIAO DIỆN CHÍNH ---
st.title("🏛️ AI HÀNH CHÍNH CẤP XÃ - BẢN MIỄN PHÍ")

col1, col2 = st.columns([1, 1])

with col1:
    loai = st.selectbox("Loại văn bản", LOAI_VB)
    so_hieu = st.text_input("Số hiệu", f"01/{loai.split('(')[-1][:2]}-UBND")
    noi_dung_yc = st.text_area("Yêu cầu nội dung", placeholder="Ví dụ: Báo cáo tình hình lũ lụt tháng 3 tại ấp Thác Rã...", height=200)

with col2:
    if st.button("🚀 SOẠN THẢO VỚI GEMINI (FREE)", type="primary"):
        if not gemini_key:
            st.error("Vui lòng nhập Gemini API Key!")
        else:
            try:
                # Cấu hình Gemini
                genai.configure(api_key=gemini_key)
                # Sử dụng model gemini-1.5-flash hoặc 2.5-flash tùy thời điểm
                model = genai.GenerativeModel('gemini-1.5-flash') 
                
                system_prompt = f"Bạn là chuyên viên văn thư UBND {xa}, {tinh}. Hãy soạn thảo {loai} theo đúng Nghị định 30/2020/NĐ-CP. Chủ tịch là {chu_tich}. Nội dung phải chuyên nghiệp, có căn cứ luật pháp."
                
                with st.spinner("AI Gemini đang xử lý..."):
                    response = model.generate_content(f"{system_prompt}\n\nYêu cầu cụ thể: {noi_dung_yc}")
                    st.session_state['ai_content'] = response.text
            except Exception as e:
                st.error(f"Lỗi: {e}. Có thể do API Key sai hoặc hết hạn.")

    if 'ai_content' in st.session_state:
        st.subheader("📄 Kết quả bản thảo")
        st.write(st.session_state['ai_content'])
        st.info("💡 Lưu ý: Bản miễn phí của Gemini có thể dùng dữ liệu để huấn luyện. Không nhập thông tin tuyệt mật quốc gia.")

# (Hàm create_docx giữ nguyên như bản trước để xuất file chuẩn Word)
