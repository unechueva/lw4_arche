import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="VM & Container Hosting", layout="wide", page_icon="🖥️")
st.title("🖥️ VM & Container Manager")
st.markdown("**Хостинг-провайдер** — аренда виртуалок и контейнеров с SSH-доступом")

with st.sidebar:
    st.header("📌 Инструкции")
    st.info("1. Запусти backend: `uvicorn api:app --reload`\n2. Создай ресурс\n3. Подключайся по SSH")
    
    st.markdown("**Логин/пароль внутри:** `user` / (из образа)")
    
    if "api_status" not in st.session_state:
        try:
            requests.get(f"{API_URL}/list", timeout=2)
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
                r = requests.post(f"{API_URL}/create", json=payload, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ **Успешно создано!**\n**ID:** `{data.get('id')}`\n**Порт:** `{data.get('port')}`")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ API вернул ошибку {r.status_code}\n{r.text}")
            except Exception as e:
                st.error(f"❌ Не удалось подключиться к backend\n{e}")

with tab2:
    st.header("Запущенные ресурсы")
    
    col_refresh, col_stats = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Обновить список", type="secondary"):
            st.rerun()
    
    try:
        r = requests.get(f"{API_URL}/list", timeout=5)
        if r.status_code == 200:
            items = r.json() or []
            
            total = len(items)
            docker_count = sum(1 for i in items if i.get("type") == "docker")
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
                    row_cols = st.columns([1, 1, 1, 1, 2, 3, 1])
                    
                    row_cols[0].write(item.get("id", ""))
                    row_cols[1].write(item.get("type", "").upper())
                    row_cols[2].write(str(item.get("cpu", "")))
                    row_cols[3].write(str(item.get("ram", "")))
                    
                    status = item.get("status", "unknown")
                    if status == "running":
                        row_cols[4].markdown("🟢 **running**")
                    elif status == "stopped":
                        row_cols[4].markdown("🔴 **stopped**")
                    else:
                        row_cols[4].write(status)
                    
                    port = item.get("port")
                    if port:
                        ssh_cmd = f"ssh user@localhost -p {port}"
                        row_cols[5].code(ssh_cmd, language="bash")
                        
                        if row_cols[5].button("📋", key=f"copy_{item['id']}"):
                            st.session_state.copied_ssh = ssh_cmd
                            st.toast("✅ SSH-команда скопирована в буфер!", icon="📋")
                    else:
                        row_cols[5].write("—")
                    
                    if row_cols[6].button("❌", key=f"del_{item['id']}", help="Удалить ресурс"):
                        with st.spinner(f"Удаляем {item['id']}..."):
                            try:
                                d = requests.delete(f"{API_URL}/delete/{item['id']}", timeout=5)
                                if d.status_code == 200:
                                    st.success(f"✅ {item['id']} удалён")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Ошибка удаления: {d.status_code}")
                            except Exception as e:
                                st.error(f"❌ {e}")
            else:
                st.info("ℹ️ Пока нет запущенных ресурсов. Создайте первый!")
        else:
            st.error(f"❌ Ошибка получения списка: {r.status_code}")
    except Exception as e:
        st.error(f"❌ Backend недоступен. Запусти `uvicorn api:app --reload`\n{e}")

if "copied_ssh" in st.session_state:
    st.session_state.pop("copied_ssh")
