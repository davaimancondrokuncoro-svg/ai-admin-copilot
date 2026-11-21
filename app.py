import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import json
import io

st.set_page_config(page_title="AI Admin Copilot", page_icon="🗂️", layout="wide")

st.title("🗂️ AI Admin Copilot")
st.write("Asisten cerdas untuk merapikan data struk belanja, invoice, dan surat masuk secara otomatis.")

# Mengambil API Key dan memasang batas waktu maksimal 15 detik agar tidak loading lama
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key, http_options={"timeout": 15000})
except Exception:
    st.error("⚠️ API Key Gemini belum dipasang. Silakan masukkan di pengaturan Secrets Streamlit.")
    st.stop()

def proses_dengan_ai(file_bytes, mime_type, prompt, status_box):
    # Mencari otomatis daftar model yang aktif & mendukung pembacaan gambar/dokumen di akun Anda
    model_aktif = ["gemini-3.8-flash"]
    try:
        for m in client.models.list():
            if "gemini" in m.name and "flash" in m.name and "lite" not in m.name:
                nama_bersih = m.name.replace("models/", "")
                if nama_bersih not in model_aktif:
                    model_aktif.append(nama_bersih)
    except Exception:
        pass

    error_terakhir = ""
    for model_name in model_aktif[:3]:
        status_box.write(f"🔄 Mencoba membaca dokumen dengan otak AI: **{model_name}**...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            error_terakhir = str(e)
            status_box.write(f"⚠️ {model_name} sedang sibuk/tidak tersedia, beralih...")
            continue

    raise Exception(error_terakhir)

tab1, tab2 = st.tabs(["🧾 Laporan Keuangan (Struk & Invoice)", "📩 Buku Agenda Surat Masuk"])

# --- TAB 1: STRUK & INVOICE ---
with tab1:
    st.subheader("Ekstrak Data Struk Belanja & Faktur")
    uploaded_files = st.file_uploader(
        "Unggah foto struk atau invoice (bisa pilih lebih dari 1 file sekaligus)", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True,
        key="keuangan"
    )
    
    if uploaded_files and st.button("Proses Dokumen Keuangan", type="primary"):
        hasil_keuangan = []
        with st.status("Memulai proses AI...", expanded=True) as status_box:
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
                Pastikan Total_Nominal hanya berupa angka tanpa titik, koma, atau Rp. Hanya kembalikan JSON murni tanpa teks tambahan.
                """
                
                try:
                    data = proses_dengan_ai(file_bytes, mime_type, prompt, status_box)
                    data["Nama_File"] = file.name
                    hasil_keuangan.append(data)
                except Exception as e:
                    st.warning(f"Gagal memproses {file.name}: {e}")
            status_box.update(label="Proses selesai!", state="complete", expanded=False)
                    
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
        "Unggah scan atau PDF surat masuk", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True,
        key="surat"
    )
    
    if uploaded_letters and st.button("Proses Surat Masuk", type="primary"):
        hasil_surat = []
        with st.status("Memulai proses AI...", expanded=True) as status_box:
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
                Hanya kembalikan JSON murni tanpa teks tambahan.
                """
                
                try:
                    data = proses_dengan_ai(file_bytes, mime_type, prompt, status_box)
                    data["Nama_File"] = file.name
                    hasil_surat.append(data)
                except Exception as e:
                    st.warning(f"Gagal memproses {file.name}: {e}")
            status_box.update(label="Proses selesai!", state="complete", expanded=False)
                    
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
