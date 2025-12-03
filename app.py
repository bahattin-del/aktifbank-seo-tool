import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px

# Sayfa Ayarları
st.set_page_config(page_title="Aktif Bank - SEO Basit Rapor", layout="wide")

st.title("📊 Aktif Bank - SEO Performans Özeti")
st.markdown("Bu rapor, sayfaların **Trafik** ve **Teknik Güç** dengesini basitçe analiz eder.")

# ---------------------------------------------------------
# DOSYA YÜKLEME
# ---------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    sf_file = st.file_uploader("1. Screaming Frog Dosyası (CSV)", type=['csv', 'xlsx'], key="sf")
with col2:
    gsc_file = st.file_uploader("2. Trafik Dosyası (CSV/Excel)", type=['csv', 'xlsx'], key="gsc")

# ---------------------------------------------------------
# İŞLEM MOTORU
# ---------------------------------------------------------
@st.cache_data
def process_data(sf_file, gsc_file):
    try:
        # 1. SCREAMING FROG OKUMA
        if sf_file.name.endswith('.csv'):
            df_links = pd.read_csv(sf_file, low_memory=False)
        else:
            df_links = pd.read_excel(sf_file)
        
        df_links.columns = df_links.columns.str.strip()
        if 'Type' in df_links.columns: df_links = df_links[df_links['Type'] == 'Hyperlink']
        df_links = df_links[df_links['Source'] != df_links['Destination']]

        # GRAVITY HESAPLA
        G = nx.from_pandas_edgelist(df_links, source='Source', target='Destination', create_using=nx.DiGraph())
        pagerank = nx.pagerank(G, alpha=0.85)
        df_gravity = pd.DataFrame(list(pagerank.items()), columns=['URL', 'Raw_Gravity'])

        # 2. TRAFİK OKUMA
        if gsc_file.name.endswith('.csv'):
            df_traffic = pd.read_csv(gsc_file)
        else:
            df_traffic = pd.read_excel(gsc_file)
            
        # Sütunları Bul
        string_cols = df_traffic.select_dtypes(include=['object']).columns
        num_cols = df_traffic.select_dtypes(include=['number']).columns
        df_traffic = df_traffic[[string_cols[0], num_cols[0]]].copy()
        df_traffic.columns = ['URL', 'Clicks']

        # 3. BİRLEŞTİRME
        df_gravity['URL_Clean'] = df_gravity['URL'].astype(str).str.strip().str.rstrip('/')
        df_traffic['URL_Clean'] = df_traffic['URL'].astype(str).str.strip().str.rstrip('/')
        
        final_df = pd.merge(df_traffic, df_gravity, on='URL_Clean', how='inner')
        final_df = final_df.rename(columns={'URL_x': 'URL'})
        final_df = final_df[['URL', 'Clicks', 'Raw_Gravity']]

        # 4. BASİTLEŞTİRME VE ETİKETLEME (Logik Burada!)
        avg_click = final_df['Clicks'].mean()
        avg_grav = final_df['Raw_Gravity'].mean()

        def get_status(row):
            if row['Clicks'] > avg_click and row['Raw_Gravity'] > avg_grav:
                return "🌟 YILDIZ (Süper)"
            elif row['Clicks'] > avg_click and row['Raw_Gravity'] < avg_grav:
                return "🚨 ACİL (Fırsat)"
            elif row['Clicks'] < avg_click and row['Raw_Gravity'] > avg_grav:
                return "🗑️ İSRAF (Gereksiz)"
            else:
                return "💤 NORMAL"

        final_df['Durum'] = final_df.apply(get_status, axis=1)
        
        # 0-100 Puanlama Sistemi (Basitleştirme)
        max_grav = final_df['Raw_Gravity'].max()
        final_df['Teknik Puan'] = (final_df['Raw_Gravity'] / max_grav * 100).round(1)
        
        return final_df.sort_values(by='Clicks', ascending=False), avg_click, avg_grav, None

    except Exception as e:
        return None, 0, 0, f"Hata oluştu: {str(e)}"

# ---------------------------------------------------------
# GÖRÜNÜM (BASİT ARAYÜZ)
# ---------------------------------------------------------
if sf_file and gsc_file:
    df, avg_c, avg_g, error = process_data(sf_file, gsc_file)
    
    if error:
        st.error(error)
    else:
        # ÖZET KARTLARI
        st.success("Analiz Tamamlandı. İşte Sitenin Durumu:")
        
        stars = len(df[df['Durum'].str.contains("YILDIZ")])
        opportunities = len(df[df['Durum'].str.contains("ACİL")])
        waste = len(df[df['Durum'].str.contains("İSRAF")])
        
        k1, k2, k3 = st.columns(3)
        k1.metric("🌟 Mükemmel Sayfalar", stars, "Bunlara Dokunma")
        k2.metric("🚨 Acil Düzeltilecekler", opportunities, "Trafik Var, Link Yok!")
        k3.metric("🗑️ Gücü Boşa Harcayanlar", waste, "Footer'dan Çıkar")

        st.divider()

        # TABLO SEKMELERİ
        tab1, tab2, tab3 = st.tabs(["🏆 BAŞARI TABLOSU", "🛠️ YAPILACAK İŞLER", "🔍 TÜM LİSTE"])

        with tab1:
            st.subheader("En İyi Performans Gösteren Sayfalar")
            st.info("Bu sayfalar hem çok trafik alıyor hem de teknik olarak güçlü. (Kredi sayfanız burada olmalı)")
            # Sadece Yıldızları Göster
            star_df = df[df['Durum'].str.contains("YILDIZ")][['URL', 'Durum', 'Clicks', 'Teknik Puan']]
            st.dataframe(star_df, use_container_width=True)

        with tab2:
            st.subheader("Aksiyon Planı")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.error("🚨 Bu Sayfalara HEMEN İç Link Verin")
                st.caption("İnsanlar bunları arıyor ama site içinde sayfalar gizli kalmış.")
                opp_df = df[df['Durum'].str.contains("ACİL")][['URL', 'Clicks', 'Teknik Puan']]
                st.dataframe(opp_df, use_container_width=True)
                
            with col_b:
                st.warning("🗑️ Bu Sayfaların Linkini Azaltın")
                st.caption("Kimse tıklamıyor ama anasayfa kadar güçlüler.")
                waste_df = df[df['Durum'].str.contains("İSRAF")][['URL', 'Clicks', 'Teknik Puan']]
                st.dataframe(waste_df, use_container_width=True)

        with tab3:
            st.subheader("Tüm Sayfaların Analizi")
            # Arama kutusu
            search = st.text_input("Sayfa Ara (Örn: kredi)", "")
            if search:
                display_df = df[df['URL'].str.contains(search, case=False)]
            else:
                display_df = df
            
            st.dataframe(display_df[['URL', 'Durum', 'Clicks', 'Teknik Puan']], use_container_width=True)

else:
    st.info("👆 Lütfen dosyaları yükleyin, analizi yapayım.")