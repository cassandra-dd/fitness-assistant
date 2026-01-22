import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime, timedelta
import io
import textwrap

# 引入美化菜单库
try:
    from streamlit_option_menu import option_menu
except ImportError:
    st.error("请先安装 streamlit-option-menu 库: `pip install streamlit-option-menu`")
    st.stop()

# ==================== 1. 配置与 CSS 样式 ====================

st.set_page_config(
    page_title="健身小助手",
    page_icon="🍑",
    layout="centered"
)

# 深度美化 CSS
st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    
    /* 按钮样式 */
    .stButton>button {
        background-color: #E6C9C9; color: white; border-radius: 20px; border: none; font-weight: bold; transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #D1B3B3; transform: scale(1.02);
    }
    
    /* 侧边栏背景 */
    [data-testid="stSidebar"] { background-color: #FFF0F5; border-right: 1px solid #FFE4E1; }
    
    /* 标题颜色 */
    h1, h2, h3, h4, h5 { color: #8B5F65 !important; font-family: "Helvetica Neue", sans-serif; }
    
    /* 卡片式表单容器 */
    div[data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.7); padding: 30px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(230, 201, 201, 0.3); border: 1px solid #FFE4E1;
    }
    
    /* 聊天气泡 */
    .chat-bubble {
        background-color: #FFFFFF; border-radius: 15px; padding: 20px; margin: 10px 0 20px 0;
        border: 1px solid #FFE4E1; color: #555; line-height: 1.6; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Bento Grid 卡片样式 */
    .bento-card {
        background-color: #FFFDF9; border-radius: 20px; padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: 2px solid #FFF5EE; margin-bottom: 15px;
    }
    .stat-badge {
        background-color: #FFF5EE; padding: 5px 10px; border-radius: 8px;
        font-weight: bold; color: #8B5F65; margin-right: 8px; font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. 基础配置与数据处理 ====================

DATA_FILE = "fitness_data.json"

def _clean_setting_value(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text.strip().strip('"').strip("'")

def get_setting(*keys: str, default: str = "") -> str:
    for key in keys:
        if not key:
            continue

        try:
            value = st.secrets[key]
        except Exception:
            value = None
        value = _clean_setting_value(value)
        if value:
            return value

        value = _clean_setting_value(os.getenv(key))
        if value:
            return value

    return default

def load_env_file(path=".env"):
    """自动读取 .env 文件"""
    if not os.path.exists(path): return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except: pass

# 初始化时直接加载环境配置
load_env_file(".env")

def normalize_record(record):
    if not isinstance(record, dict): return None
    training = record.get("training", [])
    if isinstance(training, str): training = [training]
    return {
        "id": str(record.get("id") or datetime.now().timestamp()),
        "date": str(record.get("date") or ""),
        "training": training or [],
        "diet": str(record.get("diet") or ""),
        "mood": str(record.get("mood") or ""),
    }

def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [normalize_record(r) for r in raw if normalize_record(r) and r.get("date")]
    except: return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_week_range(date_obj):
    if isinstance(date_obj, datetime): date_obj = date_obj.date()
    start = date_obj - timedelta(days=date_obj.weekday())
    return start, start + timedelta(days=6)

def render_copy_button(text, label="📋 一键复制"):
    components.html(
        f"""
        <div style="margin-top: 6px;">
          <button style="background:#E6C9C9;color:white;border:none;padding:8px 14px;border-radius:999px;cursor:pointer;font-weight:600;"
            onclick="navigator.clipboard.writeText({json.dumps(text)}).then(() => {{document.getElementById('copied').innerText='已复制！'; setTimeout(()=>document.getElementById('copied').innerText='', 1500);}})">
            {label}
          </button>
          <span id="copied" style="margin-left:10px;color:#8B5F65;font-weight:600;"></span>
        </div>
        """, height=54,
    )

# ==================== 3. 静态图片生成 (已修改：数据居中) ====================

def create_donut_chart_image_static(parts_summary, bg_color_rgb, size_px=280):
    """辅助函数：生成静态圆环图用于合成"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    if not parts_summary: parts_summary = {"休息": 1}
    values = list(parts_summary.values())
    if sum(values) <= 0: values = [1]
    palette = ["#FF9EB1", "#FFD1A9", "#E5C890", "#F4B8E4", "#A6D189", "#8CAAEE"]
    colors = [palette[i % len(palette)] for i in range(len(values))]
    bg_rgba = tuple(c / 255 for c in bg_color_rgb) + (1.0,)

    fig, ax = plt.subplots(figsize=(4, 4), dpi=200)
    fig.patch.set_facecolor(bg_rgba)
    ax.set_facecolor(bg_rgba)
    ax.pie(values, colors=colors, startangle=90, counterclock=False, wedgeprops=dict(width=0.25, edgecolor=bg_rgba, linewidth=5))
    ax.set(aspect="equal")

    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", bbox_inches="tight", pad_inches=0.0)
    plt.close(fig)
    buf.seek(0)
    
    chart = Image.open(buf).convert("RGBA")
    side = max(chart.size)
    square = Image.new("RGBA", (side, side), color=bg_color_rgb + (255,))
    square.paste(chart, ((side - chart.width) // 2, (side - chart.height) // 2), chart)
    return square.resize((size_px, size_px), Image.LANCZOS)

def create_summary_image(week_str, total_days, parts_summary, summary_sentence):
    """
    生成静态图片 - [修改点]：圆环居中，数据列表移动到圆环下方
    """
    from PIL import Image, ImageDraw, ImageFont

    width, height = 750, 1100 # 稍微加高一点以容纳垂直布局
    app_bg_color = (255, 245, 247)
    card_bg_color = (255, 251, 240)
    title_color = (106, 57, 62)
    text_color = (80, 80, 80)
    accent_color = (255, 158, 177)
    
    img = Image.new('RGB', (width, height), color=app_bg_color)
    draw = ImageDraw.Draw(img)

    # 字体加载
    try:
        font_path = "msyh.ttc" if os.name == 'nt' else "/System/Library/Fonts/PingFang.ttc"
        font_title = ImageFont.truetype(font_path, 70)
        font_subtitle = ImageFont.truetype(font_path, 32)
        font_body = ImageFont.truetype(font_path, 28)
        font_chart_label = ImageFont.truetype(font_path, 36)
        font_chart_val = ImageFont.truetype(font_path, 50)
        font_quote = ImageFont.truetype(font_path, 30)
        font_quotes_mark = ImageFont.truetype(font_path, 80)
    except:
        font_title = font_subtitle = font_body = font_chart_label = font_chart_val = font_quote = font_quotes_mark = ImageFont.load_default()

    margin = 50
    # 绘制主卡片背景
    draw.rounded_rectangle([margin, margin, width - margin, height - margin], radius=40, fill=card_bg_color, outline=(230, 201, 201), width=3)
    
    # 1. 标题区域 (顶部)
    cursor_x = margin + 50
    cursor_y = margin + 60
    draw.text((cursor_x, cursor_y), "WEEKLY", fill=title_color, font=font_title)
    draw.text((cursor_x, cursor_y + 80), "FITNESS LOG", fill=title_color, font=font_title)
    # 装饰线
    draw.line((cursor_x, cursor_y + 170, cursor_x + 300, cursor_y + 170), fill=title_color, width=4)

    # 时间和天数
    cursor_y += 200
    draw.text((cursor_x, cursor_y), f"Time: {week_str}", fill=text_color, font=font_subtitle)
    draw.text((cursor_x, cursor_y + 45), f"本周训练: {total_days} 天", fill=text_color, font=font_subtitle)

    # 2. 图表区域 (居中)
    chart_size = 360 # 稍微变大一点
    chart_img = create_donut_chart_image_static(parts_summary, card_bg_color, size_px=chart_size)
    
    # 计算水平居中位置
    chart_x = (width - chart_size) // 2 
    chart_y = cursor_y + 100
    img.paste(chart_img, (chart_x, chart_y), chart_img)

    # 图表中心文字
    total_sessions = sum(parts_summary.values()) if parts_summary else 0
    if total_sessions > 0:
        top_part, top_count = parts_summary.most_common(1)[0]
        top_pct = (top_count / total_sessions) * 100
        center_text_1, center_text_2 = str(top_part), f"{top_pct:.1f}%"
    else:
        center_text_1, center_text_2 = "休息", "100%"

    cx, cy = chart_x + chart_size // 2, chart_y + chart_size // 2
    bbox1 = draw.textbbox((0, 0), center_text_1, font=font_chart_label)
    bbox2 = draw.textbbox((0, 0), center_text_2, font=font_chart_val)
    total_h = (bbox1[3]-bbox1[1]) + (bbox2[3]-bbox2[1]) + 10
    draw.text((cx - (bbox1[2]-bbox1[0])/2, cy - total_h/2), center_text_1, fill=title_color, font=font_chart_label)
    draw.text((cx - (bbox2[2]-bbox2[0])/2, cy - total_h/2 + (bbox1[3]-bbox1[1]) + 10), center_text_2, fill=title_color, font=font_chart_val)

    # 3. 数据列表区域 (居中，位于图表下方)
    # 不再放在旁边，而是放在图表下方
    list_y_start = chart_y + chart_size + 30
    
    # 标题 "训练重点"
    title_w = draw.textlength("训练重点", font=font_subtitle)
    draw.text(((width - title_w) // 2, list_y_start), "训练重点", fill=(60, 60, 60), font=font_subtitle)
    
    item_y = list_y_start + 50
    items = parts_summary.most_common(4) if parts_summary else []
    
    if not items: 
        text = "• 彻底放松"
        w = draw.textlength(text, font=font_body)
        draw.text(((width - w)//2, item_y), text, fill=text_color, font=font_body)
    
    # 绘制居中的列表项 (垂直排列，更稳重)
    for part, count in items:
        item_text = f"{part}: {count}次"
        # 简单计算一下宽度以居中
        # 这里画一个小圆点 + 文字
        full_text_w = 20 + draw.textlength(item_text, font=font_body) # 20是圆点宽度和间距
        start_x = (width - full_text_w) // 2
        
        draw.ellipse((start_x, item_y + 10, start_x + 10, item_y + 20), fill=accent_color)
        draw.text((start_x + 20, item_y), item_text, fill=text_color, font=font_body)
        item_y += 40

    # 4. 底部总结框
    box_height = 200
    box_y = height - margin - box_height - 30 # 底部留白
    box_x = margin + 40
    box_w = width - 2*margin - 80
    
    draw.rounded_rectangle((box_x, box_y, box_x + box_w, box_y + box_height), radius=20, fill=(255, 255, 255), outline=(230, 201, 201), width=2)
    draw.text((box_x + 20, box_y + 10), "“", fill=accent_color, font=font_quotes_mark)
    draw.text((box_x + 30, box_y + 25), "一句话总结:", fill=title_color, font=font_subtitle)
    
    text_start_y = box_y + 80
    for line in textwrap.wrap(summary_sentence, width=24)[:3]:
        draw.text((box_x + 30, text_start_y), line, fill=text_color, font=font_quote)
        text_start_y += 40
        
    # 右上角装饰
    icon_x, icon_y = width - 150, 100
    draw.line((icon_x, icon_y + 15, icon_x + 60, icon_y + 15), fill=(220, 180, 180), width=8)
    draw.rounded_rectangle((icon_x - 10, icon_y, icon_x, icon_y + 30), radius=4, fill=accent_color)
    draw.rounded_rectangle((icon_x + 60, icon_y, icon_x + 70, icon_y + 30), radius=4, fill=accent_color)

    return img

# ==================== 4. 动态交互图表 (保持悬停卡片效果) ====================

def get_interactive_donut_chart(parts_summary):
    """
    Plotly 动态圆环图 - 悬停显示白底卡片
    """
    import plotly.graph_objects as go

    if not parts_summary:
        parts_summary = {"休息": 1}
        colors = ["#eee"]
    else:
        palette = ["#FFB7B2", "#A6D189", "#FFE4B5", "#8CAAEE", "#D4A5A5", "#E0BBE4"]
        colors = [palette[i % len(palette)] for i in range(len(parts_summary))]

    labels = list(parts_summary.keys())
    values = list(parts_summary.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.65, 
        marker=dict(colors=colors, line=dict(color='#FFF', width=3)),
        
        # 交互核心：平时不显示文字，悬停显示卡片
        textinfo='none', 
        hoverinfo='none', 
        hovertemplate=(
            "<b>%{label}</b><br>" +
            "<span style='color:#666'>次数:</span> <b>%{value}</b><br>" +
            "<span style='color:#666'>占比:</span> <b>%{percent}</b>" +
            "<extra></extra>"
        )
    )])

    fig.update_layout(
        showlegend=False, 
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        height=250,
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Microsoft YaHei",
            bordercolor="#FFB7B2",
            font_color="#555",
            align="left"
        ),
        annotations=[] 
    )
    return fig

# ==================== 5. AI & 辅助逻辑 ====================

def generate_week_summary_sentence(training_days, part_counts, mood_text):
    top_parts = [p for p, _ in part_counts.most_common(2)] if part_counts else []
    mood_text = mood_text or ""
    score = sum(w in mood_text for w in ["不错", "开心", "爽", "轻松"]) - sum(w in mood_text for w in ["累", "酸", "困", "emo"])
    mood_phrase = "状态还挺在线" if score >= 2 else "有点累但也没摆烂" if score <= -2 else "整体还算稳"
    parts = []
    if training_days <= 0: parts.append("这周主打休息恢复")
    else:
        parts.append(f"这周练了{training_days}天")
        if top_parts: parts.append(f"{'、'.join(top_parts)}是主场")
        parts.append(mood_phrase)
    return "，".join(parts) + "～"

def consult_ai_advisor(system_prompt, user_prompt):
    api_key = get_setting("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "AI_API_KEY", default="").strip()
    base_url = get_setting("OPENAI_BASE_URL", "DEEPSEEK_BASE_URL", default="https://api.deepseek.com").strip() or "https://api.deepseek.com"
    model = get_setting("OPENAI_MODEL", "DEEPSEEK_MODEL", default="deepseek-chat").strip() or "deepseek-chat"
    
    if not api_key: 
        return "⚠️ 未检测到 API Key：本地请在 `.env` 配置；线上 Streamlit Cloud 请在 Settings → Secrets 配置。"
        
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        msg = str(e)
        if api_key and api_key in msg:
            msg = msg.replace(api_key, "***")
        return f"AI 暂时掉线了 ({msg})"

# ==================== 6. 主程序逻辑 ====================

def main():
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

    # --- 侧边栏 (已去除 AI 设置) ---
    with st.sidebar:
        col_img, col_info = st.columns([1, 2.5])
        with col_img:
            st.markdown("# 🍑") 
        with col_info:
            st.markdown("### Hi, 仙女\n<span style='color:#888;font-size:14px'>今天也是元气满满的一天!</span>", unsafe_allow_html=True)
        
        st.markdown("---")

        selected_page = option_menu(
            menu_title=None,
            options=["今日记录", "历史记录", "生成周报", "今天吃什么", "急救指南"],
            icons=["pencil-square", "calendar-check", "image", "egg-fried", "heart-pulse"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#FFF0F5"},
                "icon": {"color": "#8B5F65", "font-size": "16px"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#ffe4e1"},
                "nav-link-selected": {"background-color": "#E6C9C9", "color": "white"},
            }
        )
        
        st.markdown("---")

        # 迷你仪表盘
        today = datetime.today().date()
        start_week, end_week = get_week_range(today)
        weekly_records = [d for d in st.session_state.data if start_week <= datetime.strptime(d['date'], "%Y-%m-%d").date() <= end_week]
        weekly_trained_days = len({d['date'] for d in weekly_records if any(t != "休息日" for t in d.get('training', []))})
        
        st.markdown("##### 📊 本周战绩")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(label="本周训练", value=f"{weekly_trained_days} 天", delta="Keep Going")
        with col_m2:
            st.metric(label="总记录", value=f"{len(st.session_state.data)} 条")

        st.write("")
        st.info("💡 **Daily Tips:**\n肌肉是在休息时生长的，不要忘了睡个好觉💤")

    # --- 页面逻辑 ---
    
    # 1. 今日记录
    if selected_page == "今日记录":
        st.subheader("📝 今天的汗水时刻")
        target_days = 5
        progress = min(weekly_trained_days / target_days, 1.0)
        st.caption(f"本周目标进度 ({weekly_trained_days}/{target_days})")
        st.progress(progress)

        with st.form("record_form"):
            col1, col2 = st.columns([1.5, 1])
            with col1:
                date = st.date_input("日期", datetime.today())
                date_str = date.strftime("%Y-%m-%d")
            with col2:
                st.write("") 
                existing = next((r for r in st.session_state.data if r.get("date") == date_str), None)
                if existing:
                    st.markdown("<span style='color:#8B5F65;font-size:12px'>⚠️ 今日已记，保存将覆盖</span>", unsafe_allow_html=True)
            
            default_train = existing["training"] if existing else ["臀腿"]
            options = ["臀腿", "肩背", "有氧/滚泡沫轴", "休息日", "生理期调整"]
            safe_default = [t for t in default_train if t in options]

            training = st.multiselect("今天练了什么？", options, default=safe_default)
            
            c_diet, c_mood = st.columns(2)
            with c_diet:
                diet = st.text_area("饮食记录", height=100, placeholder="早餐:...\n午餐:...", value=existing.get("diet", "") if existing else "")
            with c_mood:
                mood = st.text_area("今日感受", height=100, placeholder="状态不错，重量涨了...", value=existing.get("mood", "") if existing else "")
            
            submit_btn = st.form_submit_button("💾 保存记录", use_container_width=True)
            
            if submit_btn:
                new_record = {
                    "id": existing["id"] if existing else str(datetime.now().timestamp()),
                    "date": date_str, "training": training, "diet": diet, "mood": mood
                }
                st.session_state.data = [r for r in st.session_state.data if r.get("date") != date_str]
                st.session_state.data.append(new_record)
                save_data(st.session_state.data)
                st.success("记录已保存！今天也要美美哒~ 🎉")
                st.rerun()

    # 2. 历史记录
    elif selected_page == "历史记录":
        st.subheader("📅 你的坚持足迹")
        if not st.session_state.data: st.info("还没有记录哦，快去记录第一天吧！")
        else:
            import pandas as pd

            df = pd.DataFrame(st.session_state.data)
            df['date_obj'] = pd.to_datetime(df['date'])
            for _, row in df.sort_values(by='date_obj', ascending=False).iterrows():
                with st.expander(f"{row['date']} | {' '.join(row['training'])}"):
                    st.markdown(f"**🥗 饮食**: {row['diet']}")
                    st.markdown(f"**💭 感受**: {row['mood']}")
                    if st.button("🗑️ 删除", key=row['id']):
                        st.session_state.data = [d for d in st.session_state.data if d['id'] != row['id']]
                        save_data(st.session_state.data)
                        st.rerun()

    # 3. 生成周报 (重点修改)
    elif selected_page == "生成周报":
        st.subheader("✨ 生成你的周报")
        ref_date = st.date_input("选择本周任意一天", datetime.today())
        start, end = get_week_range(ref_date)
        current_data = [d for d in st.session_state.data if start <= datetime.strptime(d['date'], "%Y-%m-%d").date() <= end]
        week_str = f"{start:%m.%d} - {end:%m.%d}"

        if not current_data:
            st.warning("这一周还没有数据哦！")
        else:
            from collections import Counter
            all_parts = [p for d in current_data for p in d.get("training", []) if p != "休息日"]
            training_days = len([d for d in current_data if any(t != "休息日" for t in d.get("training", []))])
            part_counts = Counter(all_parts)
            mood_text = " ".join([d.get("mood", "") for d in current_data])
            summary = generate_week_summary_sentence(training_days, part_counts, mood_text)
            
            # --- 动态预览区域 (Bento Style) ---
            st.markdown("##### 📱 动态预览")
            # 标题卡片
            st.markdown(f"""
            <div class="bento-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <p style="color:#8B5F65;font-family:'Times New Roman';font-size:28px;font-weight:bold;margin:0;">WEEKLY LOG</p>
                        <div style="color:#666;font-size:14px;">📅 {week_str}</div>
                    </div>
                    <div style="text-align:right;">
                         <div style="background:#FFB7B2;color:white;padding:5px 10px;border-radius:10px;font-size:14px;font-weight:bold;">
                            练了 {training_days} 天
                         </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 图表和数据并排 (网页预览保持左右布局比较好看，静态图再居中)
            c_chart, c_list = st.columns([1.2, 1])
            with c_chart:
                fig = get_interactive_donut_chart(part_counts)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            with c_list:
                st.markdown("**🎯 训练重点**")
                if part_counts:
                    for part, count in part_counts.most_common(4):
                         st.markdown(f"""
                         <div style="margin-bottom:8px;font-size:14px;color:#555;">
                            <span class="stat-badge">🥑</span> {part}: <b>{count}次</b>
                         </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("✨ 主打一个休息")

            st.markdown("---")

            # --- 功能区 ---
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 🖼️ 朋友圈打卡图")
                if st.button("生成图片", key="gen_img"):
                    # 调用修改后的 create_summary_image，生成居中布局的图片
                    img = create_summary_image(week_str, training_days, part_counts, summary)
                    st.image(img, caption="长按/右键保存", use_container_width=True)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button("📥 下载原图", buf.getvalue(), "weekly.png", "image/png")
            
            with col2:
                st.markdown("##### ✍️ 小红书文案")
                if st.button("AI 写文案", key="gen_copy"):
                    with st.spinner("AI 正在头脑风暴..."):
                        prompt = f"请为我写一篇健身周报小红书文案。\n数据：练了{training_days}天，部位{', '.join(part_counts.keys())}。\n记录：\n" + "\n".join([f"{d['date']}:{d['mood']}" for d in current_data])
                        sys_prompt = "你是一个健身博主。写小红书文案，第一人称，真实接地气，不要AI味。结尾加互动和Hashtag。"
                        res = consult_ai_advisor(sys_prompt, prompt)
                        st.session_state.weekly_copy = res
                
                if st.session_state.get("weekly_copy"):
                    render_copy_button(st.session_state.weekly_copy)
                    st.text_area("文案结果", st.session_state.weekly_copy, height=350)

    # 4. 今天吃什么
    elif selected_page == "今天吃什么":
        st.subheader("🍽️ 营养师帮你选")
        with st.container():
            col1, col2 = st.columns(2)
            with col1: goal = st.selectbox("当前目标", ["减脂", "维持体重", "增肌"])
            with col2: scenario = st.selectbox("场景", ["点外卖", "自己做", "外出聚餐", "便利店"])
            preference = st.text_input("想吃什么类型？", placeholder="例：想吃辣的、想嗦粉...")
            
            if st.button("💡 给我推荐", use_container_width=True):
                with st.spinner("正在扫描菜单库..."):
                    sys = "你是一个懂营养学的健身搭子。推荐1-2个具体搭配，说明理由，如果是外卖给出一个避雷技巧。语气轻松。"
                    user = f"目标{goal}，场景{scenario}，偏好{preference}。请推荐。"
                    advice = consult_ai_advisor(sys, user)
                    st.markdown(f"<div class='chat-bubble'><b>🥑 推荐方案：</b><br>{advice.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

    # 5. 急救指南
    elif selected_page == "急救指南":
        st.subheader("🆘 吃多了别慌")
        food = st.text_input("吃了什么？", placeholder="火锅、蛋糕...")
        feeling = st.select_slider("现在的感觉", options=["有点撑", "好撑啊", "撑到怀疑人生"])
        
        if st.button("🧘‍♀️ 帮我分析 & 补救", use_container_width=True):
            if not food: st.warning("先告诉我是啥呀~")
            else:
                with st.spinner("正在安抚你的胃..."):
                    sys = "温暖治愈的健身博主。1.安抚情绪拒绝焦虑。2.给出未来24h饮食运动建议。语气温柔像闺蜜。"
                    user = f"吃了{food}，感觉{feeling}。很焦虑。"
                    res = consult_ai_advisor(sys, user)
                    st.markdown(f"<div class='chat-bubble'>{res.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
