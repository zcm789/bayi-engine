import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from bayi_engine import BaYiEngine

# ============================================================
# 🔐 密码保护模块
# ============================================================

PASSWORD = "bayi2026"  # ⬅️ 你可以把这里的 "bayi2026" 改成你想要的任何密码

def check_password():
    """返回 True 表示密码验证通过"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # 显示密码输入框
    st.markdown("# 🔐 八易·私享版")
    st.markdown("请输入访问密码以进入测算面板")
    password_input = st.text_input("密码", type="password")
    if st.button("进入"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ 密码错误，请重试")
    return False


# ============================================================
# 主程序（只有通过密码验证才会执行）
# ============================================================

if not check_password():
    st.stop()  # 密码不对，直接停止，不显示下面的任何内容

# 以下是正常的仪表盘代码
st.set_page_config(
    page_title="八易全息引擎 · 智能变爻",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌌 八易全息引擎 · 智能变爻仪表盘")
st.markdown("基于 `BaYiEngine` 构建，支持循环推演、数据映射与可视化分析。")


@st.cache_resource
def get_engine(seed, steps):
    return BaYiEngine(seed=seed, internal_steps=steps)


with st.sidebar:
    st.header("⚙️ 引擎配置")
    seed = st.number_input("随机种子 (seed)", value=42, step=1)
    internal_steps = st.slider("内部推演步数 (internal_steps)", min_value=1, max_value=10, value=3)

    st.divider()
    st.header("🗺️ 循环参数")
    start_idx = st.selectbox(
        "起始宫位 (start_index)",
        options=list(range(8)),
        format_func=lambda x: f"{x}: {BaYiEngine.BA_YI_NAMES[x]}"
    )
    direction = st.radio("方向 (direction)", options=["forward", "backward"], index=0)

    st.divider()
    run_btn = st.button("🚀 运行八易循环", type="primary", use_container_width=True)

    st.divider()
    st.caption("💡 提示：调整参数后点击上方按钮重新推演")


if run_btn:
    engine = get_engine(seed, internal_steps)
    with st.spinner("正在推演八易循环 ..."):
        path, transition_log = engine.run_cycle(
            start_index=start_idx,
            direction=direction,
            internal_steps=internal_steps
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总步数", len(path))
    col2.metric("起点卦值", path[0] if path else "N/A")
    col3.metric("终点卦值", path[-1] if path else "N/A")
    col4.metric("循环闭合", "✅ 是" if path[0] == path[-1] else "❌ 否")

    with st.expander("📊 路径详细统计", expanded=False):
        st.write(f"**起始宫位**: {BaYiEngine.BA_YI_NAMES[start_idx]}")
        st.write(f"**方向**: {direction}")
        st.write(f"**路径前 20 步**: {path[:20]}")
        st.write(f"**宫间衔接段数量**: {len(transition_log)}")
        if transition_log:
            st.write("**宫间衔接示例**:")
            for k, v in list(transition_log.items())[:3]:
                st.write(f"- {k}: {v}")

    st.subheader("📈 可视化分析")
    tab1, tab2, tab3 = st.tabs(["时序轨迹", "热度图", "综合视图"])
    with tab1:
        fig, ax = engine.plot_path(path, title=f"八易循环 · {direction} · 起始={BaYiEngine.BA_YI_NAMES[start_idx]}")
        st.pyplot(fig)
        plt.close(fig)
    with tab2:
        fig, ax = engine.plot_hexagram_map(path, title="六十四卦访问频率 (8x8宫位矩阵)")
        st.pyplot(fig)
        plt.close(fig)
    with tab3:
        fig, axes = engine.plot_cycle_summary(path, transition_log)
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("💾 导出与保存")
    col_export1, col_export2 = st.columns(2)
    with col_export1:
        import json
        json_data = {
            "path": path,
            "metadata": {
                "seed": seed,
                "internal_steps": internal_steps,
                "start_index": start_idx,
                "direction": direction,
                "start_name": BaYiEngine.BA_YI_NAMES[start_idx]
            }
        }
        st.download_button(
            label="📥 下载路径 JSON",
            data=json.dumps(json_data, indent=2, ensure_ascii=False),
            file_name="bayi_path.json",
            mime="application/json"
        )
    with col_export2:
        df_path = pd.DataFrame({
            "step": list(range(len(path))),
            "hexagram": path,
            "hex_bin": [engine._to_bin6(h) for h in path],
            "hex_name": [engine.get_hexagram_name(h) for h in path]
        })
        csv = df_path.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 下载路径 CSV",
            data=csv,
            file_name="bayi_path.csv",
            mime="text/csv"
        )

st.divider()
st.header("🧮 数据映射工具 (数值 → 卦象)")
col_map1, col_map2 = st.columns([2, 1])
with col_map1:
    input_text = st.text_area(
        "输入数值序列 (逗号或空格分隔)",
        value="12.3, 14.5, 18.7, 21.2, 20.1, 16.8, 13.4, 10.9, 9.8, 15.6",
        height=100
    )
with col_map2:
    st.write("**映射范围** (可选)")
    map_min = st.number_input("最小值 (min)", value=0.0, step=0.5)
    map_max = st.number_input("最大值 (max)", value=30.0, step=0.5)
    map_btn = st.button("🔄 映射为卦象", use_container_width=True)

if map_btn and input_text:
    try:
        raw_values = []
        for token in input_text.replace(",", " ").split():
            try:
                raw_values.append(float(token))
            except ValueError:
                pass
        if raw_values:
            engine = get_engine(seed, internal_steps)
            # 手动映射
            min_val = map_min
            max_val = map_max
            if max_val == min_val:
                hex_values = [0] * len(raw_values)
            else:
                hex_values = []
                for v in raw_values:
                    v_clamped = max(min_val, min(max_val, v))
                    normalized = (v_clamped - min_val) / (max_val - min_val)
                    hex_values.append(int(round(normalized * 63)))
            results = []
            for raw, h in zip(raw_values, hex_values):
                results.append({
                    "raw": raw,
                    "hexagram": h,
                    "hex_bin": engine._to_bin6(h),
                    "hex_name": engine.get_hexagram_name(h)
                })
            df_map = pd.DataFrame(results)
            st.dataframe(df_map, use_container_width=True)
            csv_map = df_map.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 下载映射结果 CSV",
                data=csv_map,
                file_name="mapped_hexagrams.csv",
                mime="text/csv"
            )
        else:
            st.error("未能解析有效数值，请检查输入格式。")
    except Exception as e:
        st.error(f"映射失败: {e}")

st.divider()
st.caption("🌌 八易全息引擎 · 基于智能变爻与汉明距离的易学推演系统")
