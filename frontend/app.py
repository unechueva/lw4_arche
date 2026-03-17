import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="VM/Container Manager", layout="wide")
st.title("🖥️ VM & Container Manager")

tab1, tab2 = st.tabs(["➕ Create", "📋 List"])

with tab1:
    st.header("Create new resource")
    col1, col2 = st.columns(2)
    with col1:
        rtype = st.selectbox("Type", ["docker", "vm"], help="Virtual machine or container")
        cpu = st.selectbox("CPU cores", [1, 2], help="Number of CPU cores")
    with col2:
        ram = st.selectbox("RAM (MB)", [512, 1024], help="Memory in megabytes")

    if st.button("🚀 Create", type="primary"):
        payload = {"type": rtype, "cpu": cpu, "ram": ram}
        with st.spinner("Creating resource..."):
            try:
                r = requests.post(f"{API_URL}/create", json=payload, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ Created! ID: `{data.get('id')}`, port: `{data.get('port')}`")
                else:
                    st.error(f"❌ API error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")

with tab2:
    st.header("Running resources")
    if st.button("🔄 Refresh list"):
        st.rerun()

    try:
        r = requests.get(f"{API_URL}/list", timeout=5)
        if r.status_code == 200:
            items = r.json()
            if items:
                cols = st.columns([1, 1, 1, 1, 2, 3, 1])
                cols[0].markdown("**ID**")
                cols[1].markdown("**Type**")
                cols[2].markdown("**CPU**")
                cols[3].markdown("**RAM**")
                cols[4].markdown("**Status**")
                cols[5].markdown("**SSH Access**")
                cols[6].markdown("**Actions**")

                for item in items:
                    cols = st.columns([1, 1, 1, 1, 2, 3, 1])
                    cols[0].write(item.get("id", ""))
                    cols[1].write(item.get("type", ""))
                    cols[2].write(str(item.get("cpu", "")))
                    cols[3].write(str(item.get("ram", "")))

                    status = item.get("status", "unknown")
                    if status == "running":
                        cols[4].markdown("🟢 running")
                    elif status == "stopped":
                        cols[4].markdown("🔴 stopped")
                    else:
                        cols[4].write(status)

                    port = item.get("port")
                    if port:
                        ssh_cmd = f"ssh user@localhost -p {port}"
                        cols[5].code(ssh_cmd, language="bash")
                    else:
                        cols[5].write("—")

                    if cols[6].button("❌", key=f"del_{item['id']}", help="Delete this resource"):
                        with st.spinner(f"Deleting {item['id']}..."):
                            try:
                                d = requests.delete(f"{API_URL}/delete/{item['id']}", timeout=5)
                                if d.status_code == 200:
                                    st.success(f"✅ Deleted {item['id']}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Delete failed: {d.status_code}")
                            except Exception as e:
                                st.error(f"❌ Delete error: {e}")
            else:
                st.info("ℹ️ No resources running.")
        else:
            st.error(f"❌ List error: {r.status_code}")
    except Exception as e:
        st.error(f"❌ List unavailable: {e}")
