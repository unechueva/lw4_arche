import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="VM/Container Manager", layout="wide")
st.title("🖥️VM & Container Manager")

tab1, tab2, tab3 = st.tabs(["➕ Create", "📋 List", "📊 Monitor"])


with tab1:
    st.header("Create new resource")
    col1, col2 = st.columns(2)
    with col1:
        rtype = st.selectbox("Type", ["docker", "vm"])
        os = st.selectbox("OS", ["ubuntu", "debian"])
    with col2:
        cpu = st.selectbox("CPU cores", [1, 2])
        ram = st.selectbox("RAM (MB)", [512, 1024])

    if st.button(" Create"):
        payload = {
            "type": rtype,
            "os": os,
            "cpu": cpu,
            "ram": ram
        }
        try:
            r = requests.post(f"{API_URL}/create", json=payload, timeout=5)
            if r.status_code == 200:
                data = r.json()
                st.success(f"Created! ID: {data.get('id')}, port: {data.get('port')}")
            else:
                st.error(f"API error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Connection failed: {e}")


with tab2:
    st.header("Running resources")
    if st.button("🔄 Refresh list"):
        st.session_state.list_refresh = not st.session_state.get("list_refresh", False)

    try:
        r = requests.get(f"{API_URL}/list", timeout=5)
        if r.status_code == 200:
            items = r.json()
            if items:
                for item in items:
                    ssh = f"ssh user@localhost -p {item['port']}" if item.get("port") else ""
                    cols = st.columns([1, 1, 1, 1, 1, 3, 1])
                    cols[0].write(item.get("id", ""))
                    cols[1].write(item.get("type", ""))
                    cols[2].write(item.get("os", ""))
                    cols[3].write(str(item.get("cpu", "")))
                    cols[4].write(str(item.get("ram", "")))
                    cols[5].write(ssh)
                    if cols[6].button("❌", key=f"del_{item['id']}"):
                        try:
                            d = requests.delete(f"{API_URL}/delete/{item['id']}", timeout=5)
                            if d.status_code == 200:
                                st.success(f"Deleted {item['id']}")
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {d.status_code}")
                        except Exception as e:
                            st.error(f"Delete error: {e}")
            else:
                st.info("No resources running.")
        else:
            st.error(f"List error: {r.status_code}")
    except Exception as e:
        st.error(f"List unavailable: {e}")


with tab3:
    st.header("Monitor")
    if st.button(" Refresh status"):
        st.session_state.mon_refresh = not st.session_state.get("mon_refresh", False)

    try:
        r = requests.get(f"{API_URL}/monitor", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data:
                for d in data:
                    st.write(f"**{d.get('id')}** – status: {d.get('status')}, uptime: {d.get('uptime', 'N/A')} s")
            else:
                st.info("No active resources.")
        else:
            st.error(f"Monitor error: {r.status_code}")
    except Exception as e:
        st.error(f"Monitor unavailable: {e}")
