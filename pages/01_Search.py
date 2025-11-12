import streamlit as st
import time
import json
import os
from collections import deque

CONFIG_FILE = "config.json"

# --- Configuration Management ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        st.error(f"설정 파일({CONFIG_FILE})을 찾을 수 없습니다.")
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"설정 파일({CONFIG_FILE})의 형식이 잘못되었습니다. 파일을 확인해주세요.")
        return []

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def auto_migrate_config(config):
    """Automatically migrates the config to the new structure with groups."""
    config_updated = False
    for category in config:
        if 'groups' not in category:
            category['groups'] = {}
            config_updated = True
        
        if category['key'] == 'used_market_search' and "당근마켓" not in category['groups']:
            daangn_sites = [s['nickname'] for s in category['sites'] if s['nickname'].startswith('당근_')]
            if daangn_sites:
                category['groups']["당근마켓"] = daangn_sites
                config_updated = True
    return config, config_updated

# --- Helper Function ---
def open_urls_in_browser(keyword, sites):
    if not keyword:
        st.warning("검색어를 입력해주세요.")
        return
    js_code = ""
    unique_sites = {site['url']: site for site in sites}.values()
    for site in unique_sites:
        if site.get("url"):
            url = site["url"].replace("{query}", keyword)
            js_code += f"window.open('{url}', '_blank');"
    if js_code:
        unique_id = int(time.time() * 1000)
        st.components.v1.html(f"<script id='search-script-{unique_id}'>{js_code}</script>", height=0, width=0)
        st.success(f"'{keyword}'에 대한 검색을 시작합니다.")

# --- Main Application ---
def render_search_page():
    st.title("🔍 맞춤형 최저가 검색기")

    # --- Initialize State & Auto-migrate ---
    if 'search_config' not in st.session_state:
        config, updated = auto_migrate_config(load_config())
        st.session_state.search_config = config
        if updated:
            save_config(config)
            st.rerun()
    if 'global_keyword_input' not in st.session_state:
        st.session_state.global_keyword_input = ""
    if 'site_to_move' not in st.session_state:
        st.session_state.site_to_move = None

    edit_mode = st.toggle("사이트 편집 모드")
    st.markdown("---")

    # --- Normal Mode ---
    if not edit_mode:
        with st.container(border=True):
            st.subheader("통합 검색 설정")
            
            num_cat_cols = 5
            cat_cols = st.columns(num_cat_cols)
            for i, category in enumerate(st.session_state.search_config):
                with cat_cols[i % num_cat_cols]:
                    cat_key = category['key']
                    state_key = f"cat_check_{cat_key}"
                    if state_key not in st.session_state:
                        st.session_state[state_key] = False
                    
                    is_active = st.session_state[state_key]
                    button_type = "primary" if is_active else "secondary"
                    
                    if st.button(category['title'], key=f"cat_btn_{cat_key}", type=button_type, use_container_width=True):
                        st.session_state[state_key] = not is_active
                        st.rerun()
                        st.rerun()

            st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)

            keyword_col, search_btn_col = st.columns([4, 1])
            with keyword_col:
                keyword = st.text_input("검색어를 입력하세요", key="global_keyword_input", placeholder="여기에 검색어를 입력...", label_visibility="collapsed")
            with search_btn_col:
                if st.button("🚀 통합 검색 실행", type="primary", use_container_width=True):
                    if keyword:
                        integrated_sites = []
                        for category in st.session_state.search_config:
                            cat_key = category['key']
                            if st.session_state.get(f"cat_check_{cat_key}", False):
                                all_sites_in_category = {s['nickname']: s for s in category['sites']}
                                key_prefix = f"check_{category['key']}"
                                for group_name, member_nicknames in category.get('groups', {}).items():
                                    if st.session_state.get(f"{key_prefix}_group_{group_name}", True):
                                        for nickname in member_nicknames:
                                            if nickname in all_sites_in_category:
                                                integrated_sites.append(all_sites_in_category[nickname])
                                grouped_nicknames = {site for group in category.get('groups', {}).values() for site in group}
                                for site in category['sites']:
                                    if site['nickname'] not in grouped_nicknames and st.session_state.get(f"{key_prefix}_{site['nickname']}", True):
                                        integrated_sites.append(site)
                        if integrated_sites:
                            with st.spinner("통합 검색을 시작합니다..."):
                                open_urls_in_browser(keyword, integrated_sites)
                        else: st.warning("통합 검색할 카테고리를 하나 이상 선택해주세요.")
                    else: st.warning("검색어를 입력해주세요.")
        st.markdown("---")

        for i, category in enumerate(st.session_state.search_config):
            with st.expander(f"{category['title']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("검색 대상 사이트")
                    key_prefix = f"check_{category['key']}"
                    all_site_nicknames = {s['nickname'] for s in category['sites']}
                    grouped_nicknames = {nickname for group in category.get('groups', {}).values() for nickname in group}
                    ungrouped_nicknames = sorted(list(all_site_nicknames - grouped_nicknames))
                    
                    items_to_render = []
                    for group_name in sorted(category.get('groups', {}).keys()):
                        items_to_render.append({"nickname": f"{group_name} (그룹)", "is_group": True, "group_name": group_name})
                    for nickname in ungrouped_nicknames:
                        items_to_render.append({"nickname": nickname, "is_group": False})

                    num_columns = 4 
                    cols = st.columns(num_columns)
                    for idx, item in enumerate(items_to_render):
                        with cols[idx % num_columns]:
                            nickname = item['nickname']
                            is_group = item.get("is_group", False)
                            state_key = f"{key_prefix}_group_{item['group_name']}" if is_group else f"{key_prefix}_{nickname}"
                            
                            if state_key not in st.session_state: st.session_state[state_key] = True
                            is_active = st.session_state[state_key]
                            button_type = "primary" if is_active else "secondary"
                            
                            if st.button(nickname, key=f"btn_{state_key}", type=button_type, use_container_width=True):
                                st.session_state[state_key] = not is_active
                                st.rerun()
                                st.rerun()
                with col2:
                    st.write("") 
                    st.write("") 
                    if st.button(category['title'], key=f"button_{category['key']}", use_container_width=True):
                        if keyword:
                            selected_sites = []
                            all_sites_in_category = {s['nickname']: s for s in category['sites']}
                            key_prefix = f"check_{category['key']}"
                            for group_name, member_nicknames in category.get('groups', {}).items():
                                if st.session_state.get(f"{key_prefix}_group_{group_name}", True):
                                    for nickname in member_nicknames:
                                        if nickname in all_sites_in_category:
                                            selected_sites.append(all_sites_in_category[nickname])
                            grouped_nicknames = {site for group in category.get('groups', {}).values() for site in group}
                            for site in category['sites']:
                                if site['nickname'] not in grouped_nicknames and st.session_state.get(f"{key_prefix}_{site['nickname']}", True):
                                    selected_sites.append(site)
                            if selected_sites:
                                with st.spinner(f"'{category['title']}' 검색을 시작합니다..."):
                                    open_urls_in_browser(keyword, selected_sites)
                            else: st.warning("선택된 검색 사이트가 없습니다.")
                        else: st.warning("검색어를 입력해주세요.")
            if i < len(st.session_state.search_config) - 1: st.markdown("---")

    # --- Edit Mode ---
    else:
        # ... (Edit mode code remains the same as the last correct version)
        st.info("편집 모드에서는 사이트와 카테고리를 관리할 수 있습니다.")

        if st.session_state.site_to_move is not None:
            cat_idx, site_idx = st.session_state.site_to_move
            site_to_move = st.session_state.search_config[cat_idx]['sites'][site_idx]
            
            with st.container(border=True):
                st.markdown(f"**'{site_to_move['nickname']}'** 사이트를 이동합니다.")
                destination_options = {i: cat['title'] for i, cat in enumerate(st.session_state.search_config) if i != cat_idx}
                
                if not destination_options:
                    st.warning("이동할 다른 카테고리가 없습니다.")
                    st.session_state.site_to_move = None
                    time.sleep(1); st.rerun()
                else:
                    move_col1, move_col2, move_col3 = st.columns([3, 1, 1])
                    with move_col1:
                        destination_idx = st.selectbox("이동할 카테고리를 선택하세요.", options=list(destination_options.keys()), format_func=lambda x: destination_options[x], key="move_dest_select", label_visibility="collapsed")
                    with move_col2:
                        if st.button("이동 실행", type="primary", use_container_width=True):
                            moved_site = st.session_state.search_config[cat_idx]['sites'].pop(site_idx)
                            for group_name, members in st.session_state.search_config[cat_idx]['groups'].items():
                                if moved_site['nickname'] in members: members.remove(moved_site['nickname'])
                            st.session_state.search_config[destination_idx]['sites'].append(moved_site)
                            save_config(st.session_state.search_config)
                            st.session_state.site_to_move = None
                            st.success(f"'{moved_site['nickname']}' 사이트를 '{destination_options[destination_idx]}' 카테고리로 이동했습니다.")
                            time.sleep(1); st.rerun()
                    with move_col3:
                        if st.button("취소", use_container_width=True):
                            st.session_state.site_to_move = None
                            st.rerun()
            st.markdown("---")

        with st.expander("설정 내보내기/가져오기"):
            st.download_button(label="⚙️ 현재 설정 내보내기", data=json.dumps(st.session_state.search_config, ensure_ascii=False, indent=4), file_name="searcher_config.json", mime="application/json")
            uploaded_file = st.file_uploader("⚙️ 설정 파일 가져오기 (.json)", type="json")
            if uploaded_file is not None:
                try:
                    new_config = json.load(uploaded_file)
                    if isinstance(new_config, list) and all('title' in item for item in new_config):
                        st.session_state.search_config, _ = auto_migrate_config(new_config)
                        save_config(st.session_state.search_config)
                        st.success("설정을 성공적으로 가져왔습니다! 페이지를 새로고침합니다.")
                        time.sleep(1); st.rerun()
                    else: st.error("업로드한 파일의 형식이 올바르지 않습니다.")
                except Exception as e: st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

        for i, category in enumerate(st.session_state.search_config):
            category_key = category['key']
            with st.expander(f"카테고리 편집: {category['title']}", expanded=False):
                st.markdown("##### 카테고리 설정")
                cat_col1, cat_col2, cat_col3, cat_col4 = st.columns([3, 1, 1, 1])
                with cat_col1:
                    new_title = st.text_input("카테고리 이름", value=category['title'], key=f"cat_title_{category_key}", label_visibility="collapsed")
                    if new_title != category['title']:
                        st.session_state.search_config[i]['title'] = new_title
                        save_config(st.session_state.search_config); st.rerun()
                with cat_col2:
                    if st.button("⬆️", key=f"cat_up_{category_key}", use_container_width=True, help="카테고리를 위로 이동") and i > 0:
                        st.session_state.search_config.insert(i - 1, st.session_state.search_config.pop(i))
                        save_config(st.session_state.search_config); st.rerun()
                with cat_col3:
                    if st.button("⬇️", key=f"cat_down_{category_key}", use_container_width=True, help="카테고리를 아래로 이동") and i < len(st.session_state.search_config) - 1:
                        st.session_state.search_config.insert(i + 1, st.session_state.search_config.pop(i))
                        save_config(st.session_state.search_config); st.rerun()
                with cat_col4:
                    if st.button("❌", key=f"cat_del_{category_key}", use_container_width=True, help="카테고리 삭제"):
                        st.session_state.search_config.pop(i)
                        save_config(st.session_state.search_config); st.rerun()
                
                st.markdown("##### 사이트 목록 편집")
                for site_idx, site in enumerate(category['sites']):
                    site_col1, site_col2, site_col3 = st.columns([4, 1, 1])
                    with site_col1: st.text(f"{site['nickname']} ({site['url']})")
                    with site_col2:
                        if st.button("삭제", key=f"del_{category_key}_{site['nickname']}", use_container_width=True):
                            st.session_state.search_config[i]['sites'].pop(site_idx)
                            save_config(st.session_state.search_config); st.rerun()
                    with site_col3:
                        if st.button("이동", key=f"move_{category_key}_{site['nickname']}", use_container_width=True):
                            st.session_state.site_to_move = (i, site_idx)
                            st.rerun()

                with st.form(key=f"add_site_form_{category_key}"):
                    st.markdown("###### 새 사이트 추가")
                    sc1, sc2 = st.columns(2)
                    new_nickname = sc1.text_input("사이트 별명")
                    new_url = sc2.text_input("사이트 URL (검색어는 {query}로)")
                    if st.form_submit_button("추가하기"):
                        if new_nickname and new_url and "{query}" in new_url:
                            st.session_state.search_config[i]['sites'].append({"nickname": new_nickname, "url": new_url})
                            save_config(st.session_state.search_config); st.rerun()
                        else: st.warning("별명과 URL을 올바르게 입력해주세요. URL에는 {query}가 포함되어야 합니다.")
                
                st.markdown("---")
                st.markdown("##### 그룹 관리")
                all_site_nicknames = [s['nickname'] for s in category['sites']]
                with st.form(key=f"create_group_{category_key}"):
                    new_group_name = st.text_input("새 그룹 이름")
                    if st.form_submit_button("그룹 생성"):
                        if new_group_name and new_group_name not in category['groups']:
                            category['groups'][new_group_name] = []
                            save_config(st.session_state.search_config); st.rerun()
                        else: st.warning("그룹 이름이 비어있거나 이미 존재합니다.")
                for group_name in list(category['groups'].keys()):
                    with st.container(border=True):
                        grp_col1, grp_col2 = st.columns([4,1])
                        with grp_col1: st.markdown(f"**'{group_name}' 그룹 편집**")
                        with grp_col2:
                            if st.button("🗑️ 그룹 삭제", key=f"del_group_{category_key}_{group_name}", use_container_width=True):
                                del category['groups'][group_name]
                                save_config(st.session_state.search_config); st.rerun()
                        
                        current_members = category['groups'][group_name]
                        selected_members = st.multiselect("그룹에 포함할 사이트를 선택하세요.", options=all_site_nicknames, default=current_members, key=f"ms_{category_key}_{group_name}")
                        if set(selected_members) != set(current_members):
                            category['groups'][group_name] = selected_members
                            save_config(st.session_state.search_config); st.rerun()
        
        st.markdown("---")
        with st.form(key="add_category_form"):
            st.markdown("##### 새 카테고리 추가")
            new_cat_title = st.text_input("새 카테고리 이름")
            if st.form_submit_button("카테고리 추가하기"):
                if new_cat_title:
                    new_key = new_cat_title.lower().replace(" ", "_")
                    st.session_state.search_config.append({"title": new_cat_title, "key": new_key, "sites": [], "groups": {}})
                    save_config(st.session_state.search_config); st.rerun()
                else: st.warning("카테고리 이름을 입력해주세요.")

if __name__ == "__main__":
    render_search_page()


