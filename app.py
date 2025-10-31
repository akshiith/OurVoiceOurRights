import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from gtts import gTTS
import base64

from utils import (
    init_database, get_cache_timestamp, is_cache_valid, 
    save_to_cache, get_from_cache, fetch_from_api, 
    load_offline_data, get_state_average, format_indian_number,
    get_month_name, get_translations, generate_summary,
    get_all_states_from_cache, get_districts_from_cache,
    get_districts_from_offline, generate_pdf_report
)

st.set_page_config(
    page_title="MGNREGA Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_database()

st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .hindi-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.2rem;
    }
    .warning-banner {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .glossary-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

trans = get_translations()

with st.sidebar:
    st.header("🔧 Settings / सेटिंग्स")
    
    language = st.selectbox(
        "Language / भाषा",
        options=["English", "हिंदी"],
        index=0
    )
    lang_code = 'en' if language == "English" else 'hi'
    
    st.markdown("---")
    st.markdown("### 📚 Glossary / शब्दावली")
    
    glossary_label = "📖 Detailed Metric Guide" if lang_code == 'en' else "📖 विस्तृत मैट्रिक गाइड"
    with st.expander(glossary_label, expanded=False):
        if lang_code == 'en':
            st.markdown("""
            ### 👨‍🌾 Households Worked
            **Definition:** Number of individual households that received employment under MGNREGA during the reporting period.
            
            **Significance:** This metric shows how many families benefited from the scheme. Higher numbers indicate better reach and inclusivity.
            
            **Example:** If 23,450 households worked, it means 23,450 families received wage employment that month.
            
            ---
            
            ### 💰 Total Expenditure
            **Definition:** The total amount of money spent on MGNREGA projects in the district, including wages and material costs.
            
            **Significance:** Indicates the scale of economic activity and government investment in rural employment. Higher expenditure typically correlates with more development work.
            
            **Measured In:** Indian Rupees (₹), often displayed in Lakhs (1L = 100,000) or Crores (1Cr = 10,000,000).
            
            **Example:** ₹5.8 Crore means the district spent ₹58,000,000 on MGNREGA projects.
            
            ---
            
            ### 🧱 Person-Days Generated
            **Definition:** Total days of employment created. One person working for one day equals one person-day.
            
            **Calculation:** If 100 people work for 10 days each, that's 1,000 person-days.
            
            **Significance:** This is a key indicator of employment generation. The MGNREGA guarantees 100 days of work per household per year, so this metric shows progress toward that goal.
            
            **Example:** 4.2 Lakh person-days = 420,000 days of employment provided to workers.
            
            ---
            
            ### 💵 Average Wage
            **Definition:** The average daily wage paid to MGNREGA workers in the district.
            
            **Significance:** MGNREGA wages must meet or exceed the state's minimum wage. This metric helps track fair compensation.
            
            **Measured In:** Rupees per day (₹/day).
            
            **Example:** ₹235.50 per day means on average, each worker earned ₹235.50 for a day's work.
            
            ---
            
            ### 📊 Understanding the Dashboard
            - **Green Arrows ↗:** Metric increased from last month (positive trend)
            - **Red Arrows ↘:** Metric decreased from last month (needs attention)
            - **District vs State Average:** Shows how your district compares to the state average
            - **6-Month Trend:** Visualizes performance over time to identify patterns
            """)
        else:
            st.markdown("""
            ### 👨‍🌾 कुल परिवार (Households Worked)
            **परिभाषा:** रिपोर्टिंग अवधि के दौरान मनरेगा के तहत रोजगार प्राप्त करने वाले व्यक्तिगत परिवारों की संख्या।
            
            **महत्व:** यह मैट्रिक दिखाता है कि कितने परिवारों को योजना से लाभ हुआ। उच्च संख्या बेहतर पहुंच और समावेशिता को दर्शाती है।
            
            **उदाहरण:** यदि 23,450 परिवारों ने काम किया, इसका मतलब है कि उस महीने 23,450 परिवारों को मजदूरी रोजगार मिला।
            
            ---
            
            ### 💰 कुल व्यय (Total Expenditure)
            **परिभाषा:** जिले में मनरेगा परियोजनाओं पर खर्च की गई कुल राशि, जिसमें मजदूरी और सामग्री की लागत शामिल है।
            
            **महत्व:** ग्रामीण रोजगार में आर्थिक गतिविधि और सरकारी निवेश के पैमाने को दर्शाता है। अधिक व्यय आमतौर पर अधिक विकास कार्य से संबंधित होता है।
            
            **माप:** भारतीय रुपये (₹), अक्सर लाख (1L = 1,00,000) या करोड़ (1Cr = 1,00,00,000) में प्रदर्शित।
            
            **उदाहरण:** ₹5.8 करोड़ का मतलब है कि जिले ने मनरेगा परियोजनाओं पर ₹5,80,00,000 खर्च किए।
            
            ---
            
            ### 🧱 कार्य दिवस (Person-Days Generated)
            **परिभाषा:** सृजित रोजगार के कुल दिन। एक व्यक्ति एक दिन काम करता है = एक कार्य दिवस।
            
            **गणना:** यदि 100 लोग प्रत्येक 10 दिन काम करते हैं, तो यह 1,000 कार्य दिवस है।
            
            **महत्व:** यह रोजगार सृजन का एक प्रमुख संकेतक है। मनरेगा प्रति परिवार प्रति वर्ष 100 दिनों के काम की गारंटी देता है, इसलिए यह मैट्रिक उस लक्ष्य की ओर प्रगति दिखाता है।
            
            **उदाहरण:** 4.2 लाख कार्य दिवस = श्रमिकों को 4,20,000 दिनों का रोजगार प्रदान किया गया।
            
            ---
            
            ### 💵 औसत वेतन (Average Wage)
            **परिभाषा:** जिले में मनरेगा श्रमिकों को दी जाने वाली औसत दैनिक मजदूरी।
            
            **महत्व:** मनरेगा मजदूरी राज्य की न्यूनतम मजदूरी को पूरा या उससे अधिक होनी चाहिए। यह मैट्रिक उचित मुआवजे को ट्रैक करने में मदद करता है।
            
            **माप:** प्रति दिन रुपये (₹/दिन)।
            
            **उदाहरण:** ₹235.50 प्रति दिन का मतलब है कि औसतन, प्रत्येक श्रमिक ने एक दिन के काम के लिए ₹235.50 कमाए।
            
            ---
            
            ### 📊 डैशबोर्ड को समझना
            - **हरे तीर ↗:** पिछले महीने से मैट्रिक में वृद्धि (सकारात्मक रुझान)
            - **लाल तीर ↘:** पिछले महीने से मैट्रिक में कमी (ध्यान देने की जरूरत)
            - **जिला बनाम राज्य औसत:** दिखाता है कि आपका जिला राज्य औसत की तुलना में कैसा प्रदर्शन कर रहा है
            - **6 महीने का रुझान:** समय के साथ प्रदर्शन को दृश्यमान करता है ताकि पैटर्न की पहचान हो सके
            """)
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size: 0.8rem; color: #666;'>
    <b>About MGNREGA</b><br>
    The Mahatma Gandhi National Rural Employment Guarantee Act provides at least 100 days of wage employment per year to rural households.
    <br><br>
    <b>मनरेगा के बारे में</b><br>
    महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम ग्रामीण परिवारों को प्रति वर्ष कम से कम 100 दिनों का वेतन रोजगार प्रदान करता है।
    </div>
    """, unsafe_allow_html=True)

st.markdown(f'<div class="main-title">{trans["title"][lang_code]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">{trans["subtitle"][lang_code]}</div>', unsafe_allow_html=True)

default_states = ["Uttar Pradesh", "Maharashtra", "Karnataka", "Tamil Nadu", "Bihar", "Rajasthan"]
cached_states = get_all_states_from_cache()
available_states = cached_states if cached_states else default_states

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    selected_state = st.selectbox(
        f"🗺️ {trans['select_state'][lang_code]}",
        options=available_states,
        index=0 if "Uttar Pradesh" in available_states else 0
    )

cached_districts = get_districts_from_cache(selected_state)
if not cached_districts:
    cached_districts = get_districts_from_offline(selected_state)
    if not cached_districts:
        cached_districts = ["Lucknow"]

with col2:
    selected_district = st.selectbox(
        f"🏘️ {trans['select_district'][lang_code]}",
        options=cached_districts,
        index=0
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_button = st.button(f"🔍 {trans['fetch_data'][lang_code]}", type="primary", width='stretch')

location_help_label = "📍 Can't find your district? Enter your city/town name:" if lang_code == 'en' else "📍 अपना जिला नहीं मिल रहा? अपने शहर/कस्बे का नाम दर्ज करें:"
with st.expander(location_help_label, expanded=False):
    user_location = st.text_input(
        "City/Town/Village" if lang_code == 'en' else "शहर/कस्बा/गांव",
        placeholder="e.g., Gomti Nagar, Varanasi Cantt, etc." if lang_code == 'en' else "उदाहरण: गोमती नगर, वाराणसी छावनी, आदि"
    )
    
    if user_location:
        location_lower = user_location.lower()
        suggested_districts = []
        
        for district in cached_districts:
            if location_lower in district.lower() or district.lower() in location_lower:
                suggested_districts.append(district)
        
        common_mappings = {
            'gomti': 'Lucknow',
            'hazratganj': 'Lucknow',
            'alambagh': 'Lucknow',
            'assi': 'Varanasi',
            'godowlia': 'Varanasi',
            'bhu': 'Varanasi',
            'iit kanpur': 'Kanpur',
            'kanpur central': 'Kanpur',
            'taj mahal': 'Agra',
            'agra fort': 'Agra'
        }
        
        for key, district in common_mappings.items():
            if key in location_lower and district in cached_districts and district not in suggested_districts:
                suggested_districts.append(district)
        
        if suggested_districts:
            st.success(f"{'Suggested district(s):' if lang_code == 'en' else 'सुझाया गया जिला:'} {', '.join(suggested_districts)}")
            st.info(f"{'Please select from the dropdown above' if lang_code == 'en' else 'कृपया ऊपर ड्रॉपडाउन से चुनें'}")
        else:
            st.warning(f"{'No matching district found. Please try a different location or select manually.' if lang_code == 'en' else 'कोई मेल खाता जिला नहीं मिला। कृपया एक अलग स्थान आज़माएं या मैन्युअल रूप से चुनें।'}")

@st.cache_data(ttl=86400)
def get_district_data(state, district):
    """Fetch district data with caching and fallback"""
    data_source = "cache"
    timestamp = None
    
    if is_cache_valid(state, district):
        df = get_from_cache(state, district)
        timestamp = get_cache_timestamp(state, district)
        data_source = "cache"
    else:
        api_data = fetch_from_api(state, district)
        
        if api_data:
            df = pd.DataFrame(api_data)
            save_to_cache(state, district, api_data)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_source = "api"
        else:
            df = get_from_cache(state, district)
            
            if df.empty:
                df = load_offline_data(state, district)
                if not df.empty:
                    records = df.to_dict('records')
                    save_to_cache(state, district, records)
                data_source = "offline"
            
            timestamp = get_cache_timestamp(state, district)
    
    return df, data_source, timestamp

if fetch_button or selected_state or selected_district:
    with st.spinner('Loading data... / डेटा लोड हो रहा है...'):
        df, data_source, last_updated = get_district_data(selected_state, selected_district)
        
        if df.empty:
            st.error("⚠️ No data available for this district / इस जिले के लिए कोई डेटा उपलब्ध नहीं है")
            st.stop()
        
        if data_source in ["cache", "offline"]:
            update_date = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if last_updated else "Unknown"
            st.markdown(f"""
            <div class="warning-banner">
                ⚠️ <b>Showing cached data</b> (last updated on {update_date})<br>
                <i>कैश किया गया डेटा दिखाया जा रहा है (अंतिम अपडेट: {update_date})</i>
            </div>
            """, unsafe_allow_html=True)
        
        df = df.sort_values(by=['year', 'month'], ascending=False)
        
        latest = df.iloc[0]
        
        st.markdown("---")
        st.subheader(f"📊 Key Metrics for {selected_district}, {selected_state}")
        st.markdown(f"<i>प्रमुख मैट्रिक्स: {selected_district}, {selected_state}</i>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        delta_households = None
        delta_expenditure = None
        delta_person_days = None
        delta_wage = None
        
        if len(df) > 1:
            previous = df.iloc[1]
            delta_households = int(latest['households'] - previous['households'])
            delta_expenditure = float(latest['expenditure'] - previous['expenditure'])
            delta_person_days = int(latest['person_days'] - previous['person_days'])
            delta_wage = float(latest['avg_wage'] - previous['avg_wage'])
        
        with col1:
            st.metric(
                label=f"👨‍🌾 {trans['households'][lang_code]}",
                value=f"{int(latest['households']):,}",
                delta=delta_households
            )
        
        with col2:
            st.metric(
                label=f"💰 {trans['expenditure'][lang_code]}",
                value=format_indian_number(latest['expenditure']),
                delta=delta_expenditure
            )
        
        with col3:
            st.metric(
                label=f"🧱 {trans['person_days'][lang_code]}",
                value=format_indian_number(latest['person_days']),
                delta=delta_person_days
            )
        
        with col4:
            st.metric(
                label=f"💵 {trans['avg_wage'][lang_code]}",
                value=f"₹{latest['avg_wage']:.2f}",
                delta=delta_wage
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 6-Month Trend / 6 महीने का रुझान")
            
            trend_df = df.head(6).sort_values(by=['year', 'month'])
            trend_df['month_year'] = trend_df.apply(
                lambda x: f"{get_month_name(x['month'])} {x['year']}", axis=1
            )
            
            fig_line = go.Figure()
            
            fig_line.add_trace(go.Scatter(
                x=trend_df['month_year'],
                y=trend_df['person_days'],
                mode='lines+markers',
                name='Person-Days',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig_line.update_layout(
                title="Person-Days Generated Over Time",
                xaxis_title="Month",
                yaxis_title="Person-Days",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_line, width='stretch')
        
        with col2:
            st.subheader("📊 District vs State Average / जिला बनाम राज्य औसत")
            
            state_avg = get_state_average(selected_state, latest['year'], latest['month'])
            
            if state_avg:
                comparison_df = pd.DataFrame({
                    'Category': ['District', 'State Avg'],
                    'Person-Days': [latest['person_days'], state_avg['person_days']],
                    'Expenditure': [latest['expenditure'], state_avg['expenditure']]
                })
                
                fig_bar = go.Figure(data=[
                    go.Bar(name='Person-Days', x=comparison_df['Category'], y=comparison_df['Person-Days'], marker_color='#2ca02c'),
                    go.Bar(name='Expenditure (₹)', x=comparison_df['Category'], y=comparison_df['Expenditure'], marker_color='#ff7f0e')
                ])
                
                fig_bar.update_layout(
                    title=f"Comparison for {get_month_name(latest['month'])} {latest['year']}",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig_bar, width='stretch')
            else:
                st.info("State average data not available / राज्य औसत डेटा उपलब्ध नहीं है")
        
        st.markdown("---")
        st.subheader(f"📈 {trans['performance_summary'][lang_code]}")
        
        summary_text_en = generate_summary(selected_district, selected_state, df, language='en')
        summary_text_hi = generate_summary(selected_district, selected_state, df, language='hi')
        
        if lang_code == 'en':
            st.markdown(f"{summary_text_en}")
        else:
            st.markdown(f"{summary_text_hi}")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button(f"🔊 {trans['read_summary'][lang_code]}", type="secondary"):
                with st.spinner("Generating audio... / ऑडियो बना रहा है..."):
                    try:
                        audio_file = "summary_audio.mp3"
                        text_to_speak = summary_text_en if lang_code == 'en' else summary_text_hi
                        
                        tts = gTTS(text=text_to_speak, lang=lang_code, slow=False)
                        tts.save(audio_file)
                        
                        with open(audio_file, "rb") as f:
                            audio_bytes = f.read()
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
                        
                        st.success("✅ Audio ready! / ऑडियो तैयार है!")
                    except Exception as e:
                        st.error(f"Error generating audio: {str(e)}")
        
        with col2:
            pdf_buffer = generate_pdf_report(selected_district, selected_state, df, language=lang_code)
            if pdf_buffer:
                download_label = "📄 Download PDF Report" if lang_code == 'en' else "📄 PDF रिपोर्ट डाउनलोड करें"
                filename = f"MGNREGA_{selected_district}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label=download_label,
                    data=pdf_buffer,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
        
        st.markdown("---")
        
        with st.expander("📅 View All Monthly Data / सभी मासिक डेटा देखें"):
            display_df = df.copy()
            display_df['Month'] = display_df['month'].apply(get_month_name)
            display_df = display_df[['Month', 'year', 'households', 'person_days', 'expenditure', 'avg_wage']]
            display_df.columns = ['Month', 'Year', 'Households', 'Person-Days', 'Expenditure (₹)', 'Avg Wage (₹)']
            st.dataframe(display_df, width='stretch', hide_index=True)
        
        historical_label = "📊 Historical Trends & Year-over-Year Analysis" if lang_code == 'en' else "📊 ऐतिहासिक रुझान और वर्ष-दर-वर्ष विश्लेषण"
        with st.expander(historical_label, expanded=False):
            all_years = sorted(df['year'].unique(), reverse=True)
            
            if len(all_years) >= 2:
                st.subheader("📈 " + ("Year-over-Year Comparison" if lang_code == 'en' else "वर्ष-दर-वर्ष तुलना"))
                
                yoy_data = []
                for month_num in range(5, 11):
                    month_name = get_month_name(month_num)
                    for year in all_years:
                        year_month_data = df[(df['year'] == year) & (df['month'] == month_num)]
                        if not year_month_data.empty:
                            record = year_month_data.iloc[0]
                            yoy_data.append({
                                'Month': month_name,
                                'Year': year,
                                'Person-Days': record['person_days'],
                                'Households': record['households'],
                                'Expenditure': record['expenditure'],
                                'Avg Wage': record['avg_wage']
                            })
                
                if yoy_data:
                    yoy_df = pd.DataFrame(yoy_data)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_yoy_person_days = go.Figure()
                        for year in all_years:
                            year_data = yoy_df[yoy_df['Year'] == year]
                            fig_yoy_person_days.add_trace(go.Scatter(
                                x=year_data['Month'],
                                y=year_data['Person-Days'],
                                mode='lines+markers',
                                name=str(year),
                                line=dict(width=3),
                                marker=dict(size=8)
                            ))
                        
                        fig_yoy_person_days.update_layout(
                            title="Person-Days: Year-over-Year" if lang_code == 'en' else "कार्य दिवस: वर्ष-दर-वर्ष",
                            xaxis_title="Month" if lang_code == 'en' else "महीना",
                            yaxis_title="Person-Days" if lang_code == 'en' else "कार्य दिवस",
                            hovermode='x unified',
                            height=400
                        )
                        st.plotly_chart(fig_yoy_person_days, width='stretch')
                    
                    with col2:
                        fig_yoy_households = go.Figure()
                        for year in all_years:
                            year_data = yoy_df[yoy_df['Year'] == year]
                            fig_yoy_households.add_trace(go.Scatter(
                                x=year_data['Month'],
                                y=year_data['Households'],
                                mode='lines+markers',
                                name=str(year),
                                line=dict(width=3),
                                marker=dict(size=8)
                            ))
                        
                        fig_yoy_households.update_layout(
                            title="Households: Year-over-Year" if lang_code == 'en' else "परिवार: वर्ष-दर-वर्ष",
                            xaxis_title="Month" if lang_code == 'en' else "महीना",
                            yaxis_title="Households" if lang_code == 'en' else "परिवार",
                            hovermode='x unified',
                            height=400
                        )
                        st.plotly_chart(fig_yoy_households, width='stretch')
                    
                    st.subheader("📅 " + ("Seasonal Patterns" if lang_code == 'en' else "मौसमी पैटर्न"))
                    
                    avg_by_month = yoy_df.groupby('Month').agg({
                        'Person-Days': 'mean',
                        'Households': 'mean',
                        'Expenditure': 'mean',
                        'Avg Wage': 'mean'
                    }).reset_index()
                    
                    months_order = [get_month_name(m) for m in range(5, 11)]
                    avg_by_month['Month'] = pd.Categorical(avg_by_month['Month'], categories=months_order, ordered=True)
                    avg_by_month = avg_by_month.sort_values('Month')
                    
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        fig_seasonal_person_days = go.Figure(data=[
                            go.Bar(
                                x=avg_by_month['Month'],
                                y=avg_by_month['Person-Days'],
                                marker_color='#2ca02c',
                                text=avg_by_month['Person-Days'].apply(lambda x: format_indian_number(x)),
                                textposition='auto'
                            )
                        ])
                        fig_seasonal_person_days.update_layout(
                            title="Average Person-Days by Month" if lang_code == 'en' else "महीने के अनुसार औसत कार्य दिवस",
                            xaxis_title="Month" if lang_code == 'en' else "महीना",
                            yaxis_title="Avg Person-Days" if lang_code == 'en' else "औसत कार्य दिवस",
                            height=400
                        )
                        st.plotly_chart(fig_seasonal_person_days, width='stretch')
                    
                    with col4:
                        fig_seasonal_expenditure = go.Figure(data=[
                            go.Bar(
                                x=avg_by_month['Month'],
                                y=avg_by_month['Expenditure'],
                                marker_color='#ff7f0e',
                                text=avg_by_month['Expenditure'].apply(lambda x: format_indian_number(x)),
                                textposition='auto'
                            )
                        ])
                        fig_seasonal_expenditure.update_layout(
                            title="Average Expenditure by Month" if lang_code == 'en' else "महीने के अनुसार औसत व्यय",
                            xaxis_title="Month" if lang_code == 'en' else "महीना",
                            yaxis_title="Avg Expenditure (₹)" if lang_code == 'en' else "औसत व्यय (₹)",
                            height=400
                        )
                        st.plotly_chart(fig_seasonal_expenditure, width='stretch')
                    
                    latest_year = all_years[0]
                    prev_year = all_years[1]
                    
                    latest_total = yoy_df[yoy_df['Year'] == latest_year]['Person-Days'].sum()
                    prev_total = yoy_df[yoy_df['Year'] == prev_year]['Person-Days'].sum()
                    
                    if prev_total > 0:
                        yoy_change = ((latest_total - prev_total) / prev_total) * 100
                        
                        if lang_code == 'en':
                            summary = f"**Year-over-Year Growth:** In {latest_year}, total person-days were {format_indian_number(latest_total)}, "
                            summary += f"compared to {format_indian_number(prev_total)} in {prev_year}. "
                            if yoy_change > 0:
                                summary += f"This represents a **{yoy_change:.1f}% increase** 📈"
                            else:
                                summary += f"This represents a **{abs(yoy_change):.1f}% decrease** 📉"
                        else:
                            summary = f"**वर्ष-दर-वर्ष वृद्धि:** {latest_year} में, कुल कार्य दिवस {format_indian_number(latest_total)} थे, "
                            summary += f"{prev_year} में {format_indian_number(prev_total)} की तुलना में। "
                            if yoy_change > 0:
                                summary += f"यह **{yoy_change:.1f}% वृद्धि** को दर्शाता है 📈"
                            else:
                                summary += f"यह **{abs(yoy_change):.1f}% कमी** को दर्शाता है 📉"
                        
                        st.markdown(summary)
            else:
                st.info("Multiple years of data required for year-over-year analysis" if lang_code == 'en' else "वर्ष-दर-वर्ष विश्लेषण के लिए कई वर्षों का डेटा आवश्यक है")

st.markdown("---")

comparison_label = "🔄 Compare Multiple Districts" if lang_code == 'en' else "🔄 कई जिलों की तुलना करें"
with st.expander(comparison_label, expanded=False):
    st.markdown(f"**{'Select districts to compare' if lang_code == 'en' else 'तुलना के लिए जिले चुनें'}**")
    
    comparison_districts = st.multiselect(
        "Districts" if lang_code == 'en' else "जिले",
        options=cached_districts,
        default=[selected_district] if selected_district in cached_districts else []
    )
    
    if len(comparison_districts) >= 2:
        comparison_data = []
        
        for district in comparison_districts:
            district_df, _, _ = get_district_data(selected_state, district)
            if not district_df.empty:
                latest_record = district_df.iloc[0]
                comparison_data.append({
                    'District': district,
                    'Households': int(latest_record['households']),
                    'Person-Days': int(latest_record['person_days']),
                    'Expenditure (₹)': float(latest_record['expenditure']),
                    'Avg Wage (₹)': float(latest_record['avg_wage'])
                })
        
        if comparison_data:
            comp_df = pd.DataFrame(comparison_data)
            
            st.subheader(f"📊 {'District Comparison' if lang_code == 'en' else 'जिला तुलना'}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_comp_households = go.Figure(data=[
                    go.Bar(
                        x=comp_df['District'],
                        y=comp_df['Households'],
                        marker_color='#1f77b4',
                        text=comp_df['Households'],
                        textposition='auto'
                    )
                ])
                fig_comp_households.update_layout(
                    title="Households Worked" if lang_code == 'en' else "कुल परिवार",
                    xaxis_title="District" if lang_code == 'en' else "जिला",
                    yaxis_title="Count" if lang_code == 'en' else "संख्या",
                    height=350
                )
                st.plotly_chart(fig_comp_households, width='stretch')
            
            with col2:
                fig_comp_person_days = go.Figure(data=[
                    go.Bar(
                        x=comp_df['District'],
                        y=comp_df['Person-Days'],
                        marker_color='#2ca02c',
                        text=comp_df['Person-Days'],
                        textposition='auto'
                    )
                ])
                fig_comp_person_days.update_layout(
                    title="Person-Days Generated" if lang_code == 'en' else "कार्य दिवस",
                    xaxis_title="District" if lang_code == 'en' else "जिला",
                    yaxis_title="Count" if lang_code == 'en' else "संख्या",
                    height=350
                )
                st.plotly_chart(fig_comp_person_days, width='stretch')
            
            col3, col4 = st.columns(2)
            
            with col3:
                fig_comp_expenditure = go.Figure(data=[
                    go.Bar(
                        x=comp_df['District'],
                        y=comp_df['Expenditure (₹)'],
                        marker_color='#ff7f0e',
                        text=[format_indian_number(x) for x in comp_df['Expenditure (₹)']],
                        textposition='auto'
                    )
                ])
                fig_comp_expenditure.update_layout(
                    title="Total Expenditure" if lang_code == 'en' else "कुल व्यय",
                    xaxis_title="District" if lang_code == 'en' else "जिला",
                    yaxis_title="Amount (₹)" if lang_code == 'en' else "राशि (₹)",
                    height=350
                )
                st.plotly_chart(fig_comp_expenditure, width='stretch')
            
            with col4:
                fig_comp_wage = go.Figure(data=[
                    go.Bar(
                        x=comp_df['District'],
                        y=comp_df['Avg Wage (₹)'],
                        marker_color='#d62728',
                        text=[f"₹{x:.2f}" for x in comp_df['Avg Wage (₹)']],
                        textposition='auto'
                    )
                ])
                fig_comp_wage.update_layout(
                    title="Average Wage" if lang_code == 'en' else "औसत वेतन",
                    xaxis_title="District" if lang_code == 'en' else "जिला",
                    yaxis_title="Wage per Day (₹)" if lang_code == 'en' else "प्रति दिन वेतन (₹)",
                    height=350
                )
                st.plotly_chart(fig_comp_wage, width='stretch')
            
            st.markdown("### " + ("Comparison Table" if lang_code == 'en' else "तुलना तालिका"))
            st.dataframe(comp_df, width='stretch', hide_index=True)
    
    elif len(comparison_districts) == 1:
        st.info("Please select at least 2 districts to compare" if lang_code == 'en' else "तुलना के लिए कम से कम 2 जिले चुनें")
    else:
        st.info("Select districts from the dropdown above" if lang_code == 'en' else "ऊपर ड्रॉपडाउन से जिले चुनें")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>Data source: Government of India Open Data Portal (data.gov.in)</p>
    <p>डेटा स्रोत: भारत सरकार ओपन डेटा पोर्टल (data.gov.in)</p>
    <p style='margin-top: 1rem;'>Built with ❤️ for rural India | ग्रामीण भारत के लिए ❤️ के साथ बनाया गया</p>
</div>
""", unsafe_allow_html=True)
