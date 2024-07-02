import streamlit as st
import pandas as pd
import random
import json
import os
import urllib.parse
import re
import io

# 파일에서 데이터 로드
def load_data():
    try:
        if os.path.exists('restaurants.json'):
            with open('restaurants.json', 'r', encoding='utf-8') as f:
                return pd.DataFrame(json.load(f))
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
    return pd.DataFrame(columns=['상호명', '주소', '대표메뉴', '연락처', '음식 종류', '가격대'])

# 데이터를 파일에 저장
def save_data(df):
    try:
        with open('restaurants.json', 'w', encoding='utf-8') as f:
            json.dump(df.to_dict('records'), f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {e}")

# 주소를 네이버 지도 URL로 변환하는 함수
def get_naver_map_url(address):
    base_url = "https://map.naver.com/v5/search/"
    encoded_address = urllib.parse.quote(address)
    return f"{base_url}{encoded_address}"

# 상호명과 주소를 이용해 네이버 검색 URL로 변환하는 함수
def get_naver_search_url(name, address):
    dong_match = re.search(r'(\w+사하구)', address)
    dong = dong_match.group(1) if dong_match else ""
    search_term = f"{dong} {name}".strip() if dong else name
    base_url = "https://search.naver.com/search.naver?query="
    encoded_term = urllib.parse.quote(search_term)
    return f"{base_url}{encoded_term}"

# 랜덤 식당 추천 페이지
def random_recommendation_page():
    st.header('🎲 랜덤 식당 추천')
    
    # 필터링 옵션
    food_type_filter = st.multiselect('음식 종류 필터', ['한식', '중식', '일식', '양식', '기타'], key='random_food_type')
    price_range_filter = st.multiselect('가격대 필터', ['저렴', '보통', '고급'], key='random_price_range')
    
    if st.button('랜덤 식당 추천받기', key='random_recommend_button'):
        filtered_df = st.session_state.restaurants
        if food_type_filter:
            filtered_df = filtered_df[filtered_df['음식 종류'].isin(food_type_filter)]
        if price_range_filter:
            filtered_df = filtered_df[filtered_df['가격대'].isin(price_range_filter)]
        
        if not filtered_df.empty:
            recommendation = filtered_df.sample(1).iloc[0]
            st.success('오늘의 추천 식당은...')
            naver_map_url = get_naver_map_url(recommendation['주소'])
            naver_search_url = get_naver_search_url(recommendation['상호명'], recommendation['주소'])
            st.markdown(f"""
            ### 🏠 [{recommendation['상호명']}]({naver_search_url})
            - 📍 주소: [{recommendation['주소']}]({naver_map_url})
            - 🍴 대표메뉴: {recommendation['대표메뉴']}
            - 📞 연락처: {recommendation['연락처']}
            - 🍲 음식 종류: {recommendation['음식 종류']}
            - 💰 가격대: {recommendation['가격대']}
            """)
        else:
            st.warning('추천할 식당이 없습니다. 필터를 조정하거나 새로운 식당을 등록해주세요.')

# 식당 관리 페이지
def restaurant_management_page():
    st.header('식당 목록 및 관리')
    
    # 사이드바: 식당 정보 등록 및 수정
    with st.sidebar:
        st.header('식당 정보 등록/수정')
        operation = st.radio('작업 선택', ['새 식당 등록', '기존 식당 수정'], key='operation_radio')
        
        if operation == '기존 식당 수정' and not st.session_state.restaurants.empty:
            restaurant_to_edit = st.selectbox('수정할 식당 선택', st.session_state.restaurants['상호명'].tolist(), key='edit_restaurant_select')
            if restaurant_to_edit:
                restaurant_data = st.session_state.restaurants[st.session_state.restaurants['상호명'] == restaurant_to_edit].iloc[0]
        else:
            restaurant_data = pd.Series()

        name = st.text_input('상호명', value=restaurant_data.get('상호명', ''), key='restaurant_name_input')
        address = st.text_input('주소', value=restaurant_data.get('주소', ''), key='restaurant_address_input')
        menu = st.text_input('대표메뉴', value=restaurant_data.get('대표메뉴', ''), key='restaurant_menu_input')
        contact = st.text_input('연락처', value=restaurant_data.get('연락처', ''), key='restaurant_contact_input')
        food_type = st.selectbox('음식 종류', ['한식', '중식', '일식', '양식', '기타'], 
                                 index=['한식', '중식', '일식', '양식', '기타'].index(restaurant_data.get('음식 종류', '한식')),
                                 key='restaurant_food_type_select')
        price_range = st.selectbox('가격대', ['저렴', '보통', '고급'], 
                                   index=['저렴', '보통', '고급'].index(restaurant_data.get('가격대', '보통')),
                                   key='restaurant_price_range_select')
        
        if st.button('저장', key='save_restaurant_button'):
            new_data = {
                '상호명': name, '주소': address, '대표메뉴': menu, '연락처': contact,
                '음식 종류': food_type, '가격대': price_range
            }
            if operation == '새 식당 등록':
                st.session_state.restaurants = pd.concat([st.session_state.restaurants, pd.DataFrame([new_data])], ignore_index=True)
                st.success('새 식당이 등록되었습니다!')
            else:
                st.session_state.restaurants.loc[st.session_state.restaurants['상호명'] == restaurant_to_edit] = new_data
                st.success('식당 정보가 수정되었습니다!')
            save_data(st.session_state.restaurants)

    # 메인 화면: 검색, 필터링, 식당 목록 표시
    search_query = st.text_input('식당 검색 (상호명 또는 대표메뉴)', key='search_query_input')

    # 필터링
    col1, col2 = st.columns(2)
    with col1:
        food_type_filter = st.multiselect('음식 종류 필터', ['한식', '중식', '일식', '양식', '기타'], key='manage_food_type')
    with col2:
        price_range_filter = st.multiselect('가격대 필터', ['저렴', '보통', '고급'], key='manage_price_range')

    # 데이터 필터링 적용
    filtered_df = st.session_state.restaurants
    if search_query:
        filtered_df = filtered_df[filtered_df['상호명'].str.contains(search_query) | filtered_df['대표메뉴'].str.contains(search_query)]
    if food_type_filter:
        filtered_df = filtered_df[filtered_df['음식 종류'].isin(food_type_filter)]
    if price_range_filter:
        filtered_df = filtered_df[filtered_df['가격대'].isin(price_range_filter)]

    # 필터링된 데이터 표시
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info('조건에 맞는 식당이 없습니다.')

    # 식당 삭제 기능
    if not st.session_state.restaurants.empty:
        st.header('식당 삭제')
        restaurant_to_delete = st.selectbox('삭제할 식당 선택', st.session_state.restaurants['상호명'].tolist(), key='delete_restaurant_select')
        if st.button('선택한 식당 삭제', key='delete_restaurant_button'):
            st.session_state.restaurants = st.session_state.restaurants[st.session_state.restaurants['상호명'] != restaurant_to_delete]
            save_data(st.session_state.restaurants)
            st.success(f'{restaurant_to_delete} 식당이 삭제되었습니다.')

# 새로운 함수: 파일 업로드 페이지
def file_upload_page():
    st.header('📤 restaurants.json 파일 업로드')
    
    uploaded_file = st.file_uploader("restaurants.json 파일을 선택하세요", type=['json'])
    
    if uploaded_file is not None:
        try:
            # 파일 내용을 읽어 데이터프레임으로 변환
            content = uploaded_file.getvalue().decode('utf-8')
            data = json.loads(content)
            new_df = pd.DataFrame(data)
            
            # 필수 컬럼 확인
            required_columns = ['상호명', '주소', '대표메뉴', '연락처', '음식 종류', '가격대']
            if all(col in new_df.columns for col in required_columns):
                # 기존 데이터와 병합
                st.session_state.restaurants = pd.concat([st.session_state.restaurants, new_df]).drop_duplicates(subset=['상호명'], keep='last')
                st.session_state.restaurants = st.session_state.restaurants[st.session_state.restaurants['상호명'].notnull()]
                save_data(st.session_state.restaurants)
                st.success('파일이 성공적으로 업로드되고 기존 데이터와 병합되었습니다!')
                
                # 업로드된 데이터 미리보기
                st.subheader('업로드된 데이터 미리보기')
                st.dataframe(new_df, use_container_width=True)
            else:
                st.error('업로드된 파일에 필요한 모든 컬럼이 포함되어 있지 않습니다. 필요한 컬럼: ' + ', '.join(required_columns))
        except Exception as e:
            st.error(f'파일 처리 중 오류가 발생했습니다: {e}')

# 메인 앱
def main():
    st.set_page_config(page_title="맛집 추천 앱", page_icon="🍽️", layout="wide")
    st.title('🍽️ 머 물낀데(v1.0)')

    # 세션 상태 초기화
    if 'restaurants' not in st.session_state:
        st.session_state.restaurants = load_data()

    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🎲 랜덤 추천", "📋 식당 관리", "📤 파일 업로드"])

    with tab1:
        random_recommendation_page()
    
    with tab2:
        restaurant_management_page()
    
    with tab3:
        file_upload_page()

if __name__ == "__main__":
    main()

# 스타일링
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)