import streamlit as st
from groq import Groq
import pandas as pd
import json
import io
import base64

st.set_page_config(page_title="AI Admin Copilot", page_icon="🗂️", layout="wide")

st.title("🗂️ AI Admin Copilot")
st.write("Asisten cerdas untuk merapikan data struk belanja, invoice, dan surat masuk secara otomatis.")

try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("⚠️ API Key Groq belum dipasang. Silakan masukkan di pengaturan Secrets Streamlit.")
    st.stop()

def proses_gambar_dengan_ai(file_bytes, mime_type, prompt):
    base64_image = base64.b64encode(file_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)

tab1, tab2 = st.tabs(["🧾 Laporan Keuangan (Struk & Invoice)", "📩 Buku Agenda Surat Masuk"])

# --- TAB 1: STRUK & INVOICE ---
with tab1:
    st.subheader("Ekstrak Data Struk Belanja & Faktur")
    uploaded_files = st.file_uploader(
        "Unggah foto struk atau invoice (bisa pilih lebih dari 1 file sekaligus)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="keuangan"
    )
    
    if uploaded_files and st.button("Proses Dokumen Keuangan", type="primary"):
        hasil_keuangan = []
        with st.spinner("AI sedang membaca dan merapikan data..."):
            for file in uploaded_files:
                file_bytes = file.read()
                mime_type = file.type
                
                prompt = """
                Baca dokumen struk belanja atau invoice ini. Ekstrak informasinya ke dalam format JSON dengan kunci persis seperti berikut:
                {
                    "Tanggal": "YYYY-MM-DD (jika tidak ada isi '-')",
                    "Nama_Vendor": "Nama toko/perusahaan",
                    "Nomor_Dokumen": "Nomor struk/invoice (jika tidak ada isi '-')",
                    "Kategori": "Pilih satu: Konsumsi, ATK, Transportasi, Operasional, atau Lainnya",
                    "Total_Nominal": 0
                }
                Pastikan Total_Nominal hanya berupa angka tanpa titik, koma, atau Rp.
                """
                
                try:
                    data = proses_gambar_dengan_ai(file_bytes, mime_type, prompt)
                    data["Nama_File"] = file.name
                    hasil_keuangan.append(data)
                except Exception as e:
                    st.warning(f"Gagal memproses {file.name}: {e}")
                    
        if hasil_keuangan:
            df = pd.DataFrame(hasil_keuangan)
            st.success("✅ Data berhasil dirapikan!")
            st.dataframe(df, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Laporan_Keuangan')
            
            st.download_button(
                label="📥 Download Laporan Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Laporan_Keuangan_Admin.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --- TAB 2: SURAT MASUK ---
with tab2:
    st.subheader("Rekapitulasi Buku Agenda Surat Masuk")
    uploaded_letters = st.file_uploader(
        "Unggah foto/scan surat masuk", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="surat"
    )
    
    if uploaded_letters and st.button("Proses Surat Masuk", type="primary"):
        hasil_surat = []
        with st.spinner("AI sedang menganalisis isi surat..."):
            for file in uploaded_letters:
                file_bytes = file.read()
                mime_type = file.type
                
                prompt = """
                Baca surat masuk ini dan ekstrak ke dalam format JSON dengan kunci persis seperti berikut:
                {
                    "Tanggal_Surat": "YYYY-MM-DD (jika tidak ada isi '-')",
                    "Nomor_Surat": "Nomor surat resmi",
                    "Pengirim": "Instansi/perusahaan pengirim",
                    "Perihal": "Subjek atau perihal surat",
                    "Ringkasan_Isi": "Ringkasan singkat isi surat dalam 1-2 kalimat"
                }
                """
                
                try:
                    data = proses_gambar_dengan_ai(file_bytes, mime_type, prompt)
                    data["Nama_File"] = file.name
                    hasil_surat.append(data)
                except Exception as e:
                    st.warning(f"Gagal memproses {file.name}: {e}")
                    
        if hasil_surat:
            df_surat = pd.DataFrame(hasil_surat)
            st.success("✅ Data surat berhasil direkap!")
            st.dataframe(df_surat, use_container_width=True)
            
            buffer_surat = io.BytesIO()
            with pd.ExcelWriter(buffer_surat, engine='openpyxl') as writer:
                df_surat.to_excel(writer, index=False, sheet_name='Agenda_Surat_Masuk')
            
            st.download_button(
                label="📥 Download Buku Agenda (.xlsx)",
                data=buffer_surat.getvalue(),
                file_name="Buku_Agenda_Surat_Masuk.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
