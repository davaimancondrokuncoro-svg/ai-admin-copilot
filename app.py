import streamlit as st
from groq import Groq
import pandas as pd
import json
import io
import base64
import time
from datetime import datetime

st.set_page_config(page_title="AI Admin Copilot", page_icon="🗂️", layout="centered")

# CSS untuk layout tengah + Watermark Tepat di Tengah Layar
st.markdown(
    """
    <style>
    .block-container {
        max-width: 820px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }
    h1, .subtitle {
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
    }

    /* Watermark Tepat di Tengah Layar */
    .watermark-center {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-20deg);
        font-size: 2.8rem;
        font-weight: 800;
        color: rgba(150, 150, 150, 0.14);
        text-align: center;
        white-space: nowrap;
        pointer-events: none;
        user-select: none;
        z-index: 9999;
    }
    </style>

    <div class="watermark-center">Dava Iman C. K. • AI Admin Copilot</div>
    """,
    unsafe_allow_html=True,
)

st.title("🗂️ AI Admin Copilot")
st.markdown(
    "<p class='subtitle' style='color: gray; margin-bottom: 1.5rem;'>Asisten cerdas untuk merapikan data struk belanja, invoice, dan buku agenda surat masuk secara otomatis.</p>",
    unsafe_allow_html=True,
)

try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("⚠️ API Key Groq belum dipasang. Silakan masukkan di pengaturan Secrets Streamlit.")
    st.stop()

def proses_gambar_dengan_ai(file_bytes, mime_type, prompt):
    base64_image = base64.b64encode(file_bytes).decode("utf-8")
    
    for percobaan in range(2):
        try:
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
                max_tokens=850,
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if "429" in str(e) and percobaan == 0:
                time.sleep(20)
                continue
            raise e

tab1, tab2 = st.tabs(["🧾 Laporan Keuangan (Struk & Invoice)", "📩 Buku Agenda Surat Masuk"])

# --- TAB 1: STRUK & INVOICE ---
with tab1:
    st.subheader("Ekstrak Rincian Barang Struk & Faktur")
    uploaded_files = st.file_uploader(
        "Unggah foto struk atau invoice (bisa pilih lebih dari 1 file sekaligus)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="keuangan"
    )
    
    if uploaded_files and st.button("Proses Dokumen Keuangan", type="primary", use_container_width=True):
        hasil_keuangan = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"⏳ Memproses file {idx + 1} dari {len(uploaded_files)}: {file.name}...")
            file_bytes = file.read()
            mime_type = file.type
            
            prompt = """
            Baca rincian barang pada struk/invoice ini. Kembalikan JSON ringkas tanpa spasi berlebih dengan kunci "items":
            {"items":[{"Tanggal":"YYYY-MM-DD","Nama_Vendor":"Nama toko","Nomor_Dokumen":"No struk/-","Nama_Barang":"Nama item","Qty":0,"Satuan":"Pcs/Kg/dll","Harga_Satuan":0,"Subtotal_Barang":0,"Kategori":"Konsumsi/ATK/Transportasi/Operasional/Lainnya"}]}
            Angka tanpa titik/koma/Rp.
            """
            
            try:
                respon_json = proses_gambar_dengan_ai(file_bytes, mime_type, prompt)
                daftar_barang = respon_json.get("items", [])
                for item in daftar_barang:
                    item["Nama_File"] = file.name
                    hasil_keuangan.append(item)
            except Exception as e:
                st.warning(f"Gagal memproses {file.name}: {e}")
                
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        status_text.empty()
        if hasil_keuangan:
            df = pd.DataFrame(hasil_keuangan)
            st.success(f"✅ Berhasil mengekstrak {len(df)} baris item belanja dari {len(uploaded_files)} file!")
            st.dataframe(df, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Rincian_Belanja')
            
            st.download_button(
                label="📥 Download Laporan Rincian Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Laporan_Rincian_Belanja_Admin.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# --- TAB 2: BUKU AGENDA SURAT MASUK ---
with tab2:
    st.subheader("Rekapitulasi Buku Agenda Surat Masuk")
    uploaded_letters = st.file_uploader(
        "Unggah foto atau hasil scan surat masuk (bisa pilih lebih dari 1 surat)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="surat"
    )
    
    if uploaded_letters and st.button("Proses Buku Agenda Surat Masuk", type="primary", use_container_width=True):
        hasil_surat = []
        progress_bar_surat = st.progress(0)
        status_text_surat = st.empty()
        tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
        
        for idx, file in enumerate(uploaded_letters):
            status_text_surat.text(f"⏳ Menganalisis surat {idx + 1} dari {len(uploaded_letters)}: {file.name}...")
            file_bytes = file.read()
            mime_type = file.type
            
            prompt = """
            Baca surat resmi/surat masuk ini dan ekstrak ke dalam format JSON standar buku agenda administrasi:
            {
                "Tanggal_Surat": "YYYY-MM-DD (jika tidak ada isi '-')",
                "Nomor_Surat": "Nomor surat resmi (jika tidak ada isi '-')",
                "Pengirim": "Nama instansi/perusahaan/pengirim",
                "Perihal": "Subjek atau perihal surat",
                "Sifat_Surat": "Pilih satu: Biasa, Penting, Segera, atau Rahasia",
                "Ringkasan_Isi": "Ringkasan padat isi surat dalam 1-2 kalimat untuk disposisi pimpinan"
            }
            """
            
            try:
                data = proses_gambar_dengan_ai(file_bytes, mime_type, prompt)
                baris_agenda = {
                    "No_Agenda": idx + 1,
                    "Tanggal_Terima": tanggal_hari_ini,
                    "Tanggal_Surat": data.get("Tanggal_Surat", "-"),
                    "Nomor_Surat": data.get("Nomor_Surat", "-"),
                    "Pengirim": data.get("Pengirim", "-"),
                    "Perihal": data.get("Perihal", "-"),
                    "Sifat_Surat": data.get("Sifat_Surat", "Biasa"),
                    "Ringkasan_Isi": data.get("Ringkasan_Isi", "-"),
                    "Nama_File": file.name
                }
                hasil_surat.append(baris_agenda)
            except Exception as e:
                st.warning(f"Gagal memproses {file.name}: {e}")
                
            progress_bar_surat.progress((idx + 1) / len(uploaded_letters))
            
        status_text_surat.empty()
        if hasil_surat:
            df_surat = pd.DataFrame(hasil_surat)
            st.success(f"✅ Berhasil merekap {len(df_surat)} surat ke Buku Agenda!")
            st.dataframe(df_surat, use_container_width=True)
            
            buffer_surat = io.BytesIO()
            with pd.ExcelWriter(buffer_surat, engine='openpyxl') as writer:
                df_surat.to_excel(writer, index=False, sheet_name='Agenda_Surat_Masuk')
            
            st.download_button(
                label="📥 Download Buku Agenda (.xlsx)",
                data=buffer_surat.getvalue(),
                file_name="Buku_Agenda_Surat_Masuk.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
# --- FOOTER ---
st.markdown(
    """
    <hr style="margin-top: 3rem; margin-bottom: 1rem; border: none; border-top: 1px solid rgba(150, 150, 150, 0.2);">
    <div style="text-align: center; color: gray; font-size: 0.85rem; padding-bottom: 1rem;">
        <strong>AI Admin Copilot v1.0 (Public Beta)</strong> • Dikembangkan oleh Dava Iman C. K.<br>
        <span style="font-size: 0.78rem;">Fitur dan akurasi ekstraksi dokumen terus ditingkatkan secara berkala.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
