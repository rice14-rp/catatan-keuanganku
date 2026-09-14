import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from supabase import create_client, Client
import json
import os
import time  # Ditambahkan untuk memberi jeda notifikasi

# --- KONEKSI KE SUPABASE ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Gagal terhubung ke Supabase! Pastikan Anda sudah mengatur SUPABASE_URL dan SUPABASE_KEY di Streamlit Secrets tanpa akhiran /rest/v1/.")
    st.stop()

# --- FUNGSI DATABASE SUPABASE ---
def muat_data():
    try:
        response = supabase.table("transaksi").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return []

def tambah_data_db(data_baru):
    try:
        supabase.table("transaksi").insert(data_baru).execute()
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

def hapus_semua_data():
    try:
        supabase.table("transaksi").delete().neq("id", 0).execute()
    except Exception as e:
        st.error(f"Gagal menghapus data: {e}")

# --- FUNGSI PENGATURAN (LOKAL) ---
FILE_PENGATURAN = "pengaturan.json"
def muat_pengaturan():
    if not os.path.exists(FILE_PENGATURAN):
        return {"bank": ["Cash", "NEO Bank", "BRI", "JAGO", "Gopay", "M-Banking"]}
    with open(FILE_PENGATURAN, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {"bank": ["Cash", "NEO Bank", "BRI", "JAGO", "Gopay", "M-Banking"]}

def simpan_pengaturan(data):
    with open(FILE_PENGATURAN, "w") as file:
        json.dump(data, file, indent=4)

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Finance Dashboard", page_icon="💳", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; }
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        .saas-card {
            background-color: #ffffff; padding: 20px 24px; border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
            border: 1px solid #E2E8F0; display: flex; flex-direction: column; gap: 8px; height: 100%;
        }
        .card-header { display: flex; align-items: center; gap: 12px; }
        .card-title { color: #64748B; font-size: 14px; font-weight: 500; margin: 0; }
        .card-value { color: #0F172A; font-size: 28px; font-weight: 700; margin: 0; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

data_keuangan = muat_data()
pengaturan = muat_pengaturan()
daftar_bank = pengaturan["bank"]
sekarang = datetime.now()

# --- MENU SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color: #0F172A; font-weight: 700;'>💳 Finance App</h3>", unsafe_allow_html=True)
    st.markdown("---")
    # Menu Edit Records sudah dikembalikan ke dalam daftar!
    pilihan_menu = st.radio(
        "Menu Navigasi:",
        ["📊 Dashboard Overview", "💰 Total Saldo (Dompet)", "💸 Add Transaction", "🔍 Filter & History", "✏️ Edit Records", "📥 Export Data", "⚙️ Pengaturan"]
    )

df = pd.DataFrame(data_keuangan)
if not df.empty:
    df['tanggal_asli'] = pd.to_datetime(df['tanggal'])
    df = df.sort_values(by='tanggal_asli') 

# ==========================================
# HALAMAN 1: DASHBOARD
# ==========================================
if pilihan_menu == "📊 Dashboard Overview":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700; margin-bottom: 0px;'>Welcome back!</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 30px;'>Here's your cloud cash flow and financial summary.</p>", unsafe_allow_html=True)

    if df.empty:
        st.info("Belum ada data transaksi di database. Silakan gunakan fitur Migrasi di menu Pengaturan!")
    else:
        df_pemasukan = df[df['tipe'] == 'Pemasukan']
        df_pengeluaran = df[df['tipe'] == 'Pengeluaran']

        df_bulan_ini = df[(df['tanggal_asli'].dt.month == sekarang.month) & (df['tanggal_asli'].dt.year == sekarang.year)]
        pemasukan_bulan_ini = df_bulan_ini[df_bulan_ini['tipe'] == 'Pemasukan']['jumlah'].sum()
        pengeluaran_bulan_ini = df_bulan_ini[df_bulan_ini['tipe'] == 'Pengeluaran']['jumlah'].sum()
        arus_kas_bulan_ini = pemasukan_bulan_ini - pengeluaran_bulan_ini

        total_pemasukan = df_pemasukan['jumlah'].sum()
        total_pengeluaran = df_pengeluaran['jumlah'].sum()
        saldo_saat_ini = total_pemasukan - total_pengeluaran
        warna_arus_kas = "#10B981" if arus_kas_bulan_ini >= 0 else "#EF4444"

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""<div class="saas-card"><div class="card-header"><div class="card-title">Income (Bulan Ini)</div></div><div class="card-value" style="color: #10B981;">Rp {pemasukan_bulan_ini:,.0f}</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="saas-card"><div class="card-header"><div class="card-title">Expenses (Bulan Ini)</div></div><div class="card-value" style="color: #EF4444;">Rp {pengeluaran_bulan_ini:,.0f}</div></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="saas-card"><div class="card-header"><div class="card-title">Arus Kas (Net)</div></div><div class="card-value" style="color: {warna_arus_kas};">Rp {arus_kas_bulan_ini:,.0f}</div></div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""<div class="saas-card"><div class="card-header"><div class="card-title">Total Saldo (Cloud)</div></div><div class="card-value" style="color: #3B82F6;">Rp {saldo_saat_ini:,.0f}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        kolom_grafik1, kolom_grafik2 = st.columns([2, 1])
        with kolom_grafik1:
            st.markdown("<h4 style='color: #0F172A; font-weight: 600;'>Spending Overview (Expenses Only)</h4>", unsafe_allow_html=True)
            if not df_pengeluaran.empty:
                df_pengeluaran['tanggal_saja'] = df_pengeluaran['tanggal_asli'].dt.strftime('%d %b')
                df_line = df_pengeluaran.groupby('tanggal_saja', sort=False)['jumlah'].sum().reset_index()
                df_line['teks_angka'] = df_line['jumlah'].apply(lambda x: f"{x:,.0f}")
                fig_line = px.line(df_line, x='tanggal_saja', y='jumlah', markers=True, text='teks_angka')
                fig_line.update_traces(line_color='#3B82F6', line_width=3, marker=dict(size=8, color='white', line=dict(width=2, color='#3B82F6')), textposition="top center", textfont=dict(color='#64748B', size=11))
                fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, title=""), yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title=""))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Belum ada data pengeluaran.")
        with kolom_grafik2:
            st.markdown("<h4 style='color: #0F172A; font-weight: 600;'>By Category</h4>", unsafe_allow_html=True)
            if not df_pengeluaran.empty:
                df_pie = df_pengeluaran.groupby('jenis_pembayaran')['jumlah'].sum().reset_index()
                fig_pie = px.pie(df_pie, values='jumlah', names='jenis_pembayaran', hole=0.6)
                fig_pie.update_traces(textposition='none')
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1))
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("<br><h4 style='color: #0F172A; font-weight: 600;'>Recent Transactions</h4>", unsafe_allow_html=True)
        df_terakhir = df.tail(10).iloc[::-1].copy()
        df_terakhir['jumlah'] = df_terakhir['jumlah'].apply(lambda x: f"Rp {x:,.0f}")
        df_terakhir['tanggal'] = df_terakhir['tanggal_asli'].dt.strftime('%b %d, %Y')
        df_terakhir = df_terakhir.rename(columns={'tanggal': 'Date', 'keterangan': 'Description', 'tipe': 'Type', 'jenis_pembayaran': 'Account', 'jumlah': 'Amount'})
        st.dataframe(df_terakhir[['Date', 'Description', 'Type', 'Account', 'Amount']], use_container_width=True, hide_index=True)

# ==========================================
# HALAMAN 1.5: TOTAL SALDO
# ==========================================
elif pilihan_menu == "💰 Total Saldo (Dompet)":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Total Saldo & Rekap Rekening</h2>", unsafe_allow_html=True)
    if df.empty:
        st.warning("Belum ada data untuk dihitung.")
    else:
        semua_bank = set(df['jenis_pembayaran'].unique()).union(set(daftar_bank))
        saldo_per_bank = {}
        total_semua_uang = 0
        for bank in semua_bank:
            pemasukan = df[(df['tipe'] == 'Pemasukan') & (df['jenis_pembayaran'] == bank)]['jumlah'].sum()
            pengeluaran = df[(df['tipe'] == 'Pengeluaran') & (df['jenis_pembayaran'] == bank)]['jumlah'].sum()
            saldo = pemasukan - pengeluaran
            saldo_per_bank[bank] = saldo
            total_semua_uang += saldo
            
        st.markdown(f"### 💵 Total Seluruh Uang: <span style='color:#3B82F6;'>Rp {total_semua_uang:,.0f}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)
        
        kolom = st.columns(3)
        indeks = 0
        for bank, saldo in saldo_per_bank.items():
            warna_saldo = "#EF4444" if saldo < 0 else "#10B981"
            with kolom[indeks % 3]:
                st.markdown(f"""<div class="saas-card" style="margin-bottom: 15px;"><div class="card-header"><div class="card-title">Akun: {bank}</div></div><div class="card-value" style="color: {warna_saldo}; font-size: 24px;">Rp {saldo:,.0f}</div></div>""", unsafe_allow_html=True)
            indeks += 1

# ==========================================
# HALAMAN 2: TAMBAH DATA
# ==========================================
elif pilihan_menu == "💸 Add Transaction":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Add New Transaction</h2>", unsafe_allow_html=True)
    with st.form(key="form_tambah"):
        tipe_transaksi = st.radio("Jenis Transaksi", ["Pengeluaran", "Pemasukan"], horizontal=True)
        keterangan = st.text_input("Keterangan (misal: Beli Makan / Saldo Awal)")
        jumlah = st.number_input("Masukkan jumlah (Rp)", min_value=0, step=1000)
        jenis_bayar = st.selectbox("Akun / Bank", daftar_bank)
        
        if st.form_submit_button("Simpan Transaksi"):
            if keterangan and jumlah > 0:
                data_baru = {
                    "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "keterangan": keterangan,
                    "jumlah": jumlah,
                    "tipe": tipe_transaksi,
                    "jenis_pembayaran": jenis_bayar
                }
                tambah_data_db(data_baru)
                # Menambahkan pop-up modern (toast)
                st.toast(f"Hore! {tipe_transaksi} berhasil dicatat!", icon="🎉")
                st.success("✅ Data berhasil tersimpan ke Database Cloud.")
                # Memberi waktu 1.5 detik agar pengguna bisa melihat pesan sukses
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("⚠️ Isi keterangan dan pastikan jumlah lebih dari 0!")

# ==========================================
# HALAMAN 3: FILTER & HISTORY
# ==========================================
elif pilihan_menu == "🔍 Filter & History":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Transaction History</h2>", unsafe_allow_html=True)
    if df.empty:
        st.warning("Belum ada data.")
    else:
        k1, k2 = st.columns(2)
        with k1: opsi_waktu = st.selectbox("Rentang Waktu:", ["Bulan Ini", "7 Hari Terakhir", "Hari Ini", "Semua Data"])
        with k2: opsi_tipe = st.selectbox("Jenis Transaksi:", ["Semua", "Pemasukan", "Pengeluaran"])
        
        if opsi_waktu == "Hari Ini": df_saring = df[df['tanggal_asli'].dt.date == sekarang.date()]
        elif opsi_waktu == "7 Hari Terakhir": df_saring = df[df['tanggal_asli'] >= (sekarang - timedelta(days=7))]
        elif opsi_waktu == "Bulan Ini": df_saring = df[(df['tanggal_asli'].dt.month == sekarang.month) & (df['tanggal_asli'].dt.year == sekarang.year)]
        else: df_saring = df
        if opsi_tipe != "Semua": df_saring = df_saring[df_saring['tipe'] == opsi_tipe]
            
        st.markdown(f"**Total ({opsi_tipe} - {opsi_waktu}):** Rp {df_saring['jumlah'].sum():,.0f}")
        if not df_saring.empty:
            df_tampil = df_saring.copy()
            df_tampil['jumlah'] = df_tampil['jumlah'].apply(lambda x: f"Rp {x:,.0f}")
            df_tampil = df_tampil.sort_values(by='tanggal_asli', ascending=False)
            st.dataframe(df_tampil[['tanggal', 'keterangan', 'tipe', 'jenis_pembayaran', 'jumlah']], use_container_width=True, hide_index=True)

# ==========================================
# HALAMAN 4: EDIT RECORDS (DIKEMBALIKAN)
# ==========================================
elif pilihan_menu == "✏️ Edit Records":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Edit Records</h2>", unsafe_allow_html=True)
    st.write("Ubah data langsung di dalam tabel. Untuk menghapus baris, klik kotak di ujung kiri lalu tekan 'Delete' pada keyboard.")
    
    if df.empty:
        st.warning("Belum ada data untuk diedit.")
    else:
        semua_opsi = list(set(df['jenis_pembayaran'].unique()).union(set(daftar_bank)))
        
        # Membuat tabel yang bisa diedit (Sembunyikan kolom ID dan tanggal_asli agar rapi)
        df_edit = st.data_editor(
            df.drop(columns=['tanggal_asli'], errors='ignore'), 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "id": None, # ID disembunyikan dari layar
                "tanggal": st.column_config.TextColumn("Waktu (YYYY-MM-DD HH:MM)"),
                "tipe": st.column_config.SelectboxColumn("Tipe", options=["Pemasukan", "Pengeluaran"]),
                "jumlah": st.column_config.NumberColumn("Jumlah (Rp)"),
                "jenis_pembayaran": st.column_config.SelectboxColumn("Akun", options=semua_opsi)
            }
        )
        
        if st.button("💾 Simpan Perubahan Permanen"):
            with st.spinner("Menyinkronkan data dengan Cloud Supabase..."):
                # Cara aman & sederhana: Hapus semua data di Cloud, lalu masukkan ulang data hasil editan
                hapus_semua_data()
                data_baru = df_edit.drop(columns=['id'], errors='ignore').to_dict(orient="records")
                if len(data_baru) > 0:
                    try:
                        supabase.table("transaksi").insert(data_baru).execute()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menyimpan: {e}")
            
            st.toast("Perubahan berhasil disimpan!", icon="💾")
            st.success("✅ Seluruh perubahan berhasil disinkronkan ke Database Cloud!")
            time.sleep(1.5)
            st.rerun()

# ==========================================
# HALAMAN 5: EKSPOR DATA
# ==========================================
elif pilihan_menu == "📥 Export Data":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Export Data</h2>", unsafe_allow_html=True)
    if df.empty:
        st.warning("Tidak ada data.")
    else:
        csv_data = df.drop(columns=['tanggal_asli'], errors='ignore').to_csv(index=False, sep=";").encode('utf-8')
        st.download_button("⬇️ Download CSV", data=csv_data, file_name="laporan_keuangan_cloud.csv", mime="text/csv")

# ==========================================
# HALAMAN 6: PENGATURAN & MIGRASI DATA LAMA
# ==========================================
elif pilihan_menu == "⚙️ Pengaturan":
    st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Pengaturan Aplikasi</h2>", unsafe_allow_html=True)
    
    st.markdown("#### 🏦 Daftar Rekening / E-Wallet")
    df_bank = pd.DataFrame(daftar_bank, columns=["Nama Akun / Bank"])
    df_bank_edit = st.data_editor(df_bank, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Simpan Pengaturan Bank"):
        list_bank_baru = [str(b).strip() for b in df_bank_edit["Nama Akun / Bank"].tolist() if str(b).strip() != ""]
        pengaturan["bank"] = list_bank_baru
        simpan_pengaturan(pengaturan)
        st.toast("Pengaturan Bank Disimpan!", icon="✅")

    st.markdown("---")
    st.markdown("#### 🔄 Migrasi Data Lama (JSON ke Supabase)")
    st.write("Klik tombol di bawah ini untuk memindahkan semua catatan lama Anda dari file lokal ke database Cloud. **Cukup klik satu kali saja!**")
    if st.button("🚀 Pindahkan Data Lama ke Cloud"):
        if os.path.exists("dompet_pribadi.json"):
            with open("dompet_pribadi.json", "r") as file:
                try:
                    data_lama = json.load(file)
                    if not data_lama:
                        st.warning("File dompet_pribadi.json Anda kosong.")
                    else:
                        berhasil = 0
                        for item in data_lama:
                            tipe_trx = item.get("tipe", "Pengeluaran")
                            data_insert = {
                                "tanggal": item.get("tanggal"),
                                "keterangan": item.get("keterangan"),
                                "jumlah": item.get("jumlah"),
                                "tipe": tipe_trx,
                                "jenis_pembayaran": item.get("jenis_pembayaran")
                            }
                            try:
                                tambah_data_db(data_insert)
                                berhasil += 1
                            except:
                                pass 
                        st.success(f"✅ Berhasil memindahkan {berhasil} data ke Cloud! Silakan cek menu Dashboard.")
                except json.JSONDecodeError:
                    st.error("File rusak atau tidak terbaca.")
        else:
            st.error("File dompet_pribadi.json tidak ditemukan.")

    st.markdown("---")
    st.markdown("#### ⚠️ Danger Zone (Reset Database Cloud)")
    konfirmasi = st.checkbox("Saya yakin ingin mengosongkan seluruh database.")
    if st.button("🗑️ Hapus Semua Data Cloud"):
        if konfirmasi:
            hapus_semua_data()
            st.success("✅ Database berhasil di-reset!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("⚠️ Centang kotak konfirmasi terlebih dahulu.")
