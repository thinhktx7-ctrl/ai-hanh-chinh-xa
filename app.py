import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import qrcode
from io import BytesIO
import datetime
import pandas as pd

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI HÀNH CHÍNH XÃ - GEMINI FREE", layout="wide", page_icon="🏛️")

# --- DỮ LIỆU ĐỊA PHƯƠNG (Có thể mở rộng thêm 11.162 xã) ---
DATA_HANH_CHINH = {
    "Tuyên Quang": ["Lâm Bình", "Thác Bà", "Sơn Dương", "Chiêm Hóa", "Na Hang"],
    "Hà Nội": ["Huyện Đông Anh", "Quận Ba Đình", "Quận Hoàn Kiếm", "Xã Tiên Dương", "Phường Dịch Vọng"],
    "TP.HCM": ["Huyện Cần Giờ", "Xã Bình Chánh", "Quận 1", "TP. Thủ Đức"],
    "Đà Nẵng": ["Huyện Hòa Vang", "Quận Hải Châu", "Quận Liên Chiểu"],
    "Cần Thơ": ["Huyện Phong Điền", "Quận Ninh Kiều", "Quận Cái Răng"]
}

LOAI_VB = [
    "Công văn (CV)", "Biên bản (BB)", "Quyết định (QĐ)", "Thông báo (TB)", 
    "Chứng nhận (CN)", "Đơn đề nghị", "Giấy xác nhận", "Kế hoạch (KH)", 
    "Báo cáo (BC)", "Phê duyệt", "Triệu tập", "Thông tin"
]

PROMPT_MAU = [
    "Báo cáo công tác tháng 2/2026 xã Lâm Bình, 125 hộ nghèo",
    "Thông báo họp dân ấp Thác Rã, 8h ngày 10/3 về làm đường",
    "Quyết định khen thưởng học sinh giỏi ấp Nà Mức",
    "Kế hoạch phòng chống dịch sốt xuất huyết mùa mưa",
    "Giấy xác nhận tạm trú cho công dân Lê Thị D"
]

# --- HÀM TẠO FILE WORD CHUẨN NGHỊ ĐỊNH 30 ---
def create_docx(data):
    doc = Document()
    # Thiết lập font mặc định
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(14)

    # Header: Quốc hiệu & Tên đơn vị (Dùng bảng để căn lề chuẩn)
    table = doc.add_table(rows=1, cols=2)
    table.columns[0].width = Inches(3)
    table.columns[1].width = Inches(3.5)
    
    # Cột trái: Tên UBND
    left_cell = table.cell(0, 0).paragraphs[0]
    left_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
    left_cell.add_run(f"UBND {data['xa'].upper()}\n").bold = True
    left_cell.add_run(f"Số: {data['so_hieu']}\n")
    
    # Cột phải: Quốc hiệu
    right_cell = table.cell(0, 1).paragraphs[0]
    right_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_qh = right_cell.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    run_qh.bold = True
    run_tn = right_cell.add_run("Độc lập - Tự do - Hạnh phúc\n")
    run_tn.bold = True
    right_cell.add_run(f"{data['xa']}, ngày {data['ngay'].strftime('%d')} tháng {data['ngay'].strftime('%m')} năm {data['ngay'].strftime('%Y')}")

    doc.add_paragraph("\n")
    
    # Trích yếu
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = p_title.add_run(f"V/v: {data['trich_yeu']}")
    title_run.bold = True

    # Nội dung
    doc.add_paragraph(f"Kính gửi: {data['kinh_gui']}")
    doc.add_paragraph(data['noi_dung'])

    # Chữ ký
    doc.add_paragraph("\n")
    sign_table = doc.add_table(rows=1, cols=2)
    sign_right = sign_table.cell(0, 1).paragraphs[0]
    sign_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sign_right.add_run("CHỦ TỊCH\n").bold = True
    sign_right.add_run("(Ký, ghi rõ họ tên)\n\n\n\n")
    sign_right.add_run(data['chu_tich']).bold = True

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- GIAO DIỆN SIDEBAR ---
with st.sidebar:
    st.header("🔑 CẤU HÌNH HỆ THỐNG")
    gemini_key = st.text_input("Gemini API Key", type="password", help="Lấy miễn phí tại aistudio.google.com")
    st.info("Bản này dùng Gemini API Miễn phí (Free Tier)")
    
    tinh = st.selectbox("Chọn Tỉnh/Thành", list(DATA_HANH_CHINH.keys()))
    xa = st.selectbox("Chọn Xã/Phường", DATA_HANH_CHINH[tinh])
    st.divider()
    chu_tich = st.text_input("Chủ tịch UBND", "Nguyễn Văn A")
    van_thu = st.text_input("Văn thư", "Lê Văn C")

# --- GIAO DIỆN CHÍNH ---
st.title("🏛️ AI HÀNH CHÍNH CẤP XÃ - TRỢ LÝ ĐA NĂNG")
st.caption(f"Đang phục vụ: UBND {xa.upper()} - {tinh.upper()}")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Thông tin văn bản")
    loai_vb = st.selectbox("Loại văn bản", LOAI_VB)
    so_hieu = st.text_input("Số hiệu", f"01/{loai_vb.split('(')[-1].replace(')', '')}-UBND")
    ngay = st.date_input("Ngày ban hành", datetime.date.today())
    kinh_gui = st.text_input("Kính gửi", "UBND Huyện / Nhân dân xã")
    
    prompt_chon = st.selectbox("🎯 Mẫu gợi ý nhanh", ["--- Chọn mẫu ---"] + PROMPT_MAU)
    user_input = st.text_area("Nội dung chi tiết/Yêu cầu", 
                             value=prompt_chon if prompt_chon != "--- Chọn mẫu ---" else "",
                             height=150)

with col2:
    st.subheader("✨ Kết quả AI Gemini")
    if st.button("🚀 SOẠN THẢO VĂN BẢN (GEMINI FREE)", type="primary"):
        if not gemini_key:
            st.error("Vui lòng nhập Gemini API Key ở thanh bên trái!")
        else:
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                system_prompt = f"""
                SOẠN {loai_vb} UBND XÃ theo NGHỊ ĐỊNH 30/2020/NĐ-CP
                XÃ: {xa} | TỈNH: {tinh} | CHỦ TỊCH: {chu_tich}
                CẤU TRÚC 5 PHẦN:
                1. CĂN CỨ: Luật/Quyết định Huyện/Tỉnh (tự gợi ý các luật phổ biến)
                2. TÌNH HÌNH: Nêu thực trạng địa phương liên quan yêu cầu
                3. NỘI DUNG: 3-5 điểm đánh số rõ ràng
                4. ĐỀ NGHỊ/TỔ CHỨC: Giao nhiệm vụ cho các ban ngành xã
                5. KẾT LUẬN: Trân trọng
                Ngôn ngữ: Trang trọng, đúng phong cách hành chính Việt Nam.
                """
                
                with st.spinner("Đang kết nối trí tuệ nhân tạo Google..."):
                    response = model.generate_content(f"{system_prompt}\n\nYêu cầu cụ thể: {user_input}")
                    st.session_state['ai_content'] = response.text
                    st.session_state['trich_yeu'] = user_input[:100]
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")

    if 'ai_content' in st.session_state:
        st.markdown("---")
        st.write(st.session_state['ai_content'])
        
        # Tạo file DOCX để tải về
        docx_bytes = create_docx({
            'xa': xa,
            'so_hieu': so_hieu,
            'ngay': ngay,
            'trich_yeu': st.session_state['trich_yeu'],
            'kinh_gui': kinh_gui,
            'noi_dung': st.session_state['ai_content'],
            'chu_tich': chu_tich
        })
        
        st.download_button(
            label="📥 TẢI FILE WORD (.DOCX) CHUẨN",
            data=docx_bytes,
            file_name=f"{so_hieu.replace('/', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- PHẦN PHỤ: QR CODE ---
if 'ai_content' in st.session_state:
    st.divider()
    qr_data = f"VB-XÃ-{xa}-{so_hieu}-{ngay}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf)
    st.image(buf.getvalue(), width=120, caption="Mã QR định danh")
