import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="VM & Container Hosting", layout="wide", page_icon="🖥️")

st.title("🖥️ VM & Container Manager")
st.markdown("**Хостинг-провайдер** — аренда виртуалок и контейнеров с SSH-доступом")

with st.sidebar:
    st.header("📌 Инструкции")
    st.info("1. Запусти backend: `uvicorn backend.api:app --reload`\n2. Создай ресурс\n3. Подключайся по SSH")
    
    st.markdown("**Логин/пароль внутри:** `root` / `toor` (для Docker)")
    
    if "api_status" not in st.session_state:
        try:
            requests.get(f"{API_URL}/list", timeout=3)
            st.session_state.api_status = "🟢 Online"
        except:
            st.session_state.api_status = "🔴 Backend не запущен"
    
    st.markdown(f"**API статус:** {st.session_state.api_status}")

tab1, tab2 = st.tabs(["➕ Create Resource", "📋 List & Manage"])

with tab1:
    st.header("Создать новый ресурс")
    col1, col2 = st.columns(2)
    
    with col1:
        rtype = st.selectbox("Тип", ["docker", "vm"], help="Docker контейнер или QEMU виртуалка")
        cpu = st.selectbox("CPU cores", [1, 2])
    
    with col2:
        ram = st.selectbox("RAM (MB)", [512, 1024])
    
    if st.button("🚀 Создать ресурс", type="primary", use_container_width=True):
        payload = {"type": rtype, "cpu": cpu, "ram": ram}
        
        with st.spinner("Создаём ресурс..."):
            try:
                r = requests.post(f"{API_URL}/create", json=payload, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ **Успешно создано!**\n**ID:** `{data.get('id', '—')}`\n**Порт:** `{data.get('details', {}).get('port', '—')}`")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ API вернул ошибку {r.status_code}\n{r.text}")
            except Exception as e:
                st.error(f"❌ Не удалось подключиться к backend\n{str(e)}")

with tab2:
    st.header("Запущенные ресурсы")
    
    col_refresh, col_stats = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Обновить список", type="secondary"):
            st.rerun()
    
    try:
        r = requests.get(f"{API_URL}/list", timeout=5)
        if r.status_code == 200:
            raw_data = r.json()
            if isinstance(raw_data, dict):
                items = list(raw_data.values())
            elif isinstance(raw_data, list):
                items = raw_data
            else:
                items = []
            
            total = len(items)
            docker_count = sum(1 for i in items if isinstance(i, dict) and i.get("type") == "docker")
            vm_count = total - docker_count
            st.caption(f"**Всего ресурсов: {total}** | 🐳 Docker: {docker_count} | 🖥️ VM: {vm_count}")
            
            if items:
                header_cols = st.columns([1, 1, 1, 1, 2, 3, 1])
                header_cols[0].markdown("**ID**")
                header_cols[1].markdown("**Type**")
                header_cols[2].markdown("**CPU**")
                header_cols[3].markdown("**RAM**")
                header_cols[4].markdown("**Status**")
                header_cols[5].markdown("**SSH Access**")
                header_cols[6].markdown("**Actions**")
                
                st.divider()
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    row_cols = st.columns([1, 1, 1, 1, 2, 3, 1])
                    
                    row_cols[0].write(item.get("id", "—"))
                    row_cols[1].write(item.get("type", "—").upper())
                    row_cols[2].write(str(item.get("cpu", "—")))
                    row_cols[3].write(str(item.get("ram", "—")))
                    
                    status = item.get("status", "unknown")
                    if status == "running":
                        row_cols[4].markdown("🟢 **running**")
                    elif status == "stopped":
                        row_cols[4].markdown("🔴 **stopped**")
                    else:
                        row_cols[4].write(status)
                    
                    port = item.get("port")
                    if port:
                        ssh_user = "root" if item.get("type") == "docker" else "unechueva"
                        ssh_cmd = f"ssh {ssh_user}@localhost -p {port}"
                        row_cols[5].code(ssh_cmd, language="bash")
                        
                        if row_cols[5].button("📋", key=f"copy_{item.get('id', 'no-id')}"):
                            st.session_state[f"copied_{item.get('id', 'no-id')}"] = ssh_cmd
                            st.toast("✅ SSH-команда скопирована!", icon="📋")
                    else:
                        row_cols[5].write("—")
                    
                    if row_cols[6].button("❌", key=f"del_{item.get('id', 'no-id')}", help="Удалить ресурс"):
                        with st.spinner(f"Удаляем {item.get('id', '?')}..."):
                            try:
                                d = requests.delete(f"{API_URL}/delete/{item.get('id')}", timeout=5)
                                if d.status_code in (200, 404):
                                    st.success(f"✅ Удалён")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Ошибка: {d.status_code} — {d.text}")
                            except Exception as e:
                                st.error(f"❌ {str(e)}")
            else:
                st.info("ℹ️ Пока нет запущенных ресурсов. Создайте первый!")
        else:
            st.error(f"❌ Ошибка получения списка: {r.status_code}")
    except Exception as e:
        st.error(f"❌ Backend недоступен или ошибка ответа\n{str(e)}")
