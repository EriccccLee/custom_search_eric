import streamlit as st

st.set_page_config(
    page_title="맞춤형 최저가 검색기",
    page_icon="🚀",
    layout="wide"
)

# --- Custom CSS to widen the page ---
st.markdown("""
<style>
    .block-container {
        max-width: 98% !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 맞춤형 최저가 검색기")
st.sidebar.success("원하는 페이지를 선택하세요.")

st.markdown(
    """
    ### 안녕하세요! 👋
    
    이 앱은 여러 쇼핑몰의 최저가를 한 번에 검색할 수 있도록 도와주는 맞춤형 검색기입니다.
    
    **👈 왼쪽 사이드바에서 '🔍 검색기'를 선택하여 검색을 시작하세요.**
    
    ---
    
    #### 주요 기능
    - **통합 검색**: 여러 사이트를 동시에 검색하여 시간을 절약합니다.
    - **카테고리별 검색**: '최저가 검색', '면세점 검색' 등 목적에 맞게 검색할 수 있습니다.
    - **쉬운 확장**: 새로운 검색 카테고리나 사이트를 쉽게 추가할 수 있습니다. (`pages` 폴더에 새 파일을 추가하세요.)
    
    #### 사용 방법
    1. 왼쪽 사이드바에서 **'🔍 검색기'** 페이지로 이동합니다.
    2. 검색창에 원하는 상품명을 입력합니다.
    3. 원하는 검색 카테고리의 **'검색 실행'** 버튼을 클릭합니다.
    4. 선택된 사이트들이 새 탭으로 열리며 검색 결과가 표시됩니다.
    
    """
)
