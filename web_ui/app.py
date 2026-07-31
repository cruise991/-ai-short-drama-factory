import streamlit as st
import os
import json
import time

# --- Setup Paths ---
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(WORKSPACE_DIR, "projects", "paperai-series")
os.makedirs(PROJECTS_DIR, exist_ok=True)

# --- Configuration ---
st.set_page_config(page_title="AutoMedia CEO Dashboard", layout="wide")

st.title("👔 AutoMedia Virtual Company")
st.markdown("### 首席执行官控制台 (CEO Dashboard)")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 目标下达区 (Goal Input)", "📊 执行看板 (Kanban)", "⚖️ 审批中心 (Approval Hub)", "⚙️ LibLib 引擎设置 (Engine Settings)"])

with tab1:
    st.header("创建新工单 (New Task Ticket)")
    with st.form("task_form"):
        st.text_input("短剧系列名称 (Series Name)", value="PaperAI-Series")
        episode = st.text_input("集数 (Episode)", value="episode-02")
        goal = st.text_area("核心目标与痛点 (Core Goal)", value="展示PaperAI能够自动生成文献综述，解决研究员面对海量论文无从下手的焦虑。")
        submitted = st.form_submit_button("下发任务 (Dispatch)")
        if submitted:
            episode_dir = os.path.join(PROJECTS_DIR, episode)
            os.makedirs(episode_dir, exist_ok=True)
            ticket_path = os.path.join(episode_dir, "00_task_ticket.json")
            with open(ticket_path, "w", encoding="utf-8") as f:
                json.dump({"goal": goal, "status": "Pending", "timestamp": time.time()}, f, ensure_ascii=False, indent=2)
            st.success(f"✅ 工单已下发至 {episode}！目标拆解部已接收。")

with tab2:
    st.header("全链路流转状态 (Global Status Kanban)")
    st.info("读取 `projects/` 目录结构，展示各集状态。")
    if os.path.exists(PROJECTS_DIR):
        episodes = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]
        if not episodes:
            st.write("暂无执行中的工单。")
        for ep in episodes:
            with st.expander(f"📁 {ep} 运行进度", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                ep_dir = os.path.join(PROJECTS_DIR, ep)
                
                # mock statuses based on file existence
                col1.metric("目标拆解部", "✅ 完成" if os.path.exists(os.path.join(ep_dir, "00_task_ticket.json")) else "⏸️ 等待")
                col2.metric("策划部 (剧本)", "🔄 进行中" if os.path.exists(os.path.join(ep_dir, "01_storyboards_scripts")) else "⏸️ 等待")
                col3.metric("生产部 (生图/视频)", "⏸️ 等待")
                col4.metric("后期质检部", "⏸️ 等待")
                
                st.progress(25) # Mock progress bar
    else:
        st.write("项目文件夹不存在。")

with tab3:
    st.header("需要您干预的节点 (Human-in-the-Loop)")
    st.warning("以下工单卡在【人工审核节点】，请查阅并给出决断。")
    
    st.markdown("### 待审：`episode-01` 剧本定稿")
    st.text_area("剧本预览 (Script Preview)", value="小雅：“太快了，别人还在啃文献，我的AI已经跑完了！”\n唐导：“没有经历过思考的结论，只是点外卖。”", disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 批准 (Approve) 并下发生产部"):
            st.success("已批准！生产部开始运作。")
    with col2:
        feedback = st.text_input("退回修改意见 (Reject Feedback)", placeholder="例如：前三秒冲突不够激烈")
        if st.button("❌ 退回重写 (Reject)"):
            st.error(f"已退回策划部。修改要求：{feedback}")

with tab4:
    st.header("⚙️ LibLib.tv 开放平台引擎配置")
    st.markdown("配置后可开启 **【方案一：API 自动化直连渲染】**；若未配置，系统将默认以 **【方案二：免 Key 标准化协同模式】** 稳定运作。")
    
    config_file = os.path.join(WORKSPACE_DIR, "liblib_config.json")
    saved_key = os.environ.get("LIBLIB_ACCESS_KEY", "")
    saved_secret = os.environ.get("LIBLIB_SECRET_KEY", "")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                saved_key = saved_key or cdata.get("LIBLIB_ACCESS_KEY", "")
                saved_secret = saved_secret or cdata.get("LIBLIB_SECRET_KEY", "")
        except:
            pass
            
    with st.form("liblib_form"):
        access_key = st.text_input("LIBLIB Access Key", value=saved_key, type="password")
        secret_key = st.text_input("LIBLIB Secret Key", value=saved_secret, type="password")
        save_btn = st.form_submit_button("保存设置 (Save Configuration)")
        
        if save_btn:
            os.environ["LIBLIB_ACCESS_KEY"] = access_key
            os.environ["LIBLIB_SECRET_KEY"] = secret_key
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({"LIBLIB_ACCESS_KEY": access_key, "LIBLIB_SECRET_KEY": secret_key}, f, indent=2)
            st.success("✅ LibLib API 配置已保存！激活【方案一：API 自动化直连渲染模式】。")

st.sidebar.markdown("### 系统状态")
st.sidebar.success("🟢 核心调度引擎：在线")

current_key = os.environ.get("LIBLIB_ACCESS_KEY", "")
if not current_key and os.path.exists(os.path.join(WORKSPACE_DIR, "liblib_config.json")):
    try:
        with open(os.path.join(WORKSPACE_DIR, "liblib_config.json")) as f:
            current_key = json.load(f).get("LIBLIB_ACCESS_KEY", "")
    except:
        pass

if current_key:
    st.sidebar.info("🟢 引擎模式：方案一 (API 自动化直连渲染)")
else:
    st.sidebar.warning("🔵 引擎模式：方案二 (免 Key 标准化协同模式 / 默认)")

st.sidebar.info("下一轮热点寻源触发时间：08:00 AM")
