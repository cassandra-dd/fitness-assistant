import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
from openai import OpenAI
import matplotlib
import textwrap
import plotly.graph_objects as go 

# 设置 matplotlib 后端
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ==================== 1. 配置与样式 ====================

st.set_page_config(
    page_title="健身小助手 Pro",
    page_icon="🍑",
    layout="centered"
)

# 自定义 CSS：Bento Grid 风格
st.markdown("""
    <style>
    /* 全局背景 */
    .stApp {
        background-color: #FFF0F5;
    }
    
    /* 按钮样式 */
    .stButton>button {
        background-color: #FFB7B2;
        color: white;
        border-radius: 20px;
        border: none;
        font-weight: bold;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #FF9E99;
        transform: translateY(-2px);
    }
    
    /* 侧边栏 */
    .stSidebar {
        background-color: #FFF5F7;
    }
    
    /* 标题颜色 */
    h1, h2, h3 {
        color: #8B4513 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* --- Bento Card 通用卡片样式 --- */
    .bento-card {
        background-color: #FFFDF9; /* 奶油白 */
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        border: 2px solid #FFF5EE;
        margin-bottom: 15px;
    }

    .card-title {
        color: #8B4513;
        font-family: "Times New Roman", serif;
        font-size: 32px;
        font-weight: bold;
        line-height: 1.1;
        margin: 0;
    }
    
    .stat-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        font-size: 14px;
        color: #555;
    }
    
    .stat-badge {
        background-color: #FFF5EE;
        padding: 5px 10px;
        border-radius: 8px;
        font-weight: bold;
        color: #8B4513;
        margin-right: 8px;
    }

    /* --- 聊天气泡样式 --- */
    .chat-bubble {
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
        border: 1px solid #FFE4E1;
        color: #555;
        line-height: 1.6;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        font-size: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 文件路径
DATA_FILE = "fitness_data.json"

def load_env_file(path=".env"):
    if not os.path.exists(path): return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")
    except Exception: pass

load_env_file(".env")

def get_setting(*keys, default=""):
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    try:
        secrets = st.secrets
        for key in keys:
            if key in secrets:
                secret_value = secrets[key]
                if secret_value is None:
                    continue
                secret_str = str(secret_value).strip()
                if secret_str:
                    return secret_str
    except Exception:
        pass
    return default

# ==================== 2. 数据处理与绘图逻辑 ====================

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
          <button style="background:#FFB7B2;color:white;border:none;padding:8px 14px;border-radius:999px;cursor:pointer;font-weight:600;"
            onclick="navigator.clipboard.writeText({json.dumps(text)}).then(() => {{document.getElementById('copied').innerText='已复制！'; setTimeout(()=>document.getElementById('copied').innerText='', 1500);}})">
            {label}
          </button>
          <span id="copied" style="margin-left:10px;color:#8B4513;font-weight:600;font-family:sans-serif;"></span>
        </div>
        """, height=54,
    )

def create_donut_chart_image_static(parts_summary, bg_color_rgb, size_px=280):
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
    width, height = 750, 1000
    app_bg_color = (255, 245, 247)
    card_bg_color = (255, 251, 240)
    title_color = (106, 57, 62)
    text_color = (80, 80, 80)
    accent_color = (255, 158, 177)
    img = Image.new('RGB', (width, height), color=app_bg_color)
    draw = ImageDraw.Draw(img)
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
    draw.rounded_rectangle([margin, margin, width - margin, height - margin], radius=40, fill=card_bg_color, outline=(230, 201, 201), width=3)
    cursor_x, cursor_y = margin + 50, margin + 60
    draw.text((cursor_x, cursor_y), "WEEKLY", fill=title_color, font=font_title)
    draw.text((cursor_x, cursor_y + 80), "FITNESS LOG", fill=title_color, font=font_title)
    draw.line((cursor_x, cursor_y + 170, cursor_x + 300, cursor_y + 170), fill=title_color, width=4)
    cursor_y += 200
    draw.text((cursor_x, cursor_y), f"Time: {week_str}", fill=text_color, font=font_subtitle)
    draw.text((cursor_x, cursor_y + 45), f"本周训练: {total_days} 天", fill=text_color, font=font_subtitle)
    chart_size = 320
    chart_img = create_donut_chart_image_static(parts_summary, card_bg_color, size_px=chart_size)
    chart_x, chart_y = margin + 30, cursor_y + 100
    img.paste(chart_img, (chart_x, chart_y), chart_img)
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
    list_x, list_y = chart_x + chart_size + 20, chart_y + 60
    draw.text((list_x, list_y), "训练重点:", fill=(60, 60, 60), font=font_subtitle)
    item_y = list_y + 50
    items = parts_summary.most_common(4) if parts_summary else []
    if not items: draw.text((list_x, item_y), "• 彻底放松", fill=text_color, font=font_body)
    for part, count in items:
        draw.ellipse((list_x, item_y + 10, list_x + 10, item_y + 20), fill=accent_color)
        draw.text((list_x + 20, item_y), f"{part}: {count}次", fill=text_color, font=font_body)
        item_y += 45
    box_x, box_y = margin + 40, chart_y + chart_size + 30
    draw.rounded_rectangle((box_x, box_y, box_x + width - 2*margin - 80, box_y + 220), radius=20, fill=(255, 255, 255), outline=(230, 201, 201), width=2)
    draw.text((box_x + 20, box_y + 10), "“", fill=accent_color, font=font_quotes_mark)
    draw.text((box_x + 30, box_y + 25), "一句话总结:", fill=title_color, font=font_subtitle)
    text_start_y = box_y + 80
    for line in textwrap.wrap(summary_sentence, width=24)[:3]:
        draw.text((box_x + 30, text_start_y), line, fill=text_color, font=font_quote)
        text_start_y += 40
    icon_x, icon_y = width - 150, 100
    draw.line((icon_x, icon_y + 15, icon_x + 60, icon_y + 15), fill=(220, 180, 180), width=8)
    draw.rounded_rectangle((icon_x - 10, icon_y, icon_x, icon_y + 30), radius=4, fill=accent_color)
    draw.rounded_rectangle((icon_x + 60, icon_y, icon_x + 70, icon_y + 30), radius=4, fill=accent_color)
    return img

# ==================== 3. 动态交互图表 (核心修改) ====================

def get_interactive_donut_chart(parts_summary):
    """
    Plotly 动态圆环图
    优化点：
    1. 平时中间为空 (无文字)。
    2. 鼠标悬停时，显示类似 App 风格的详情卡片（部位+次数+占比）。
    """
    if not parts_summary:
        parts_summary = {"休息": 1}
        colors = ["#eee"]
    else:
        # 莫兰迪色系：蜜桃、抹茶、奶油、雾霾蓝、香芋紫
        palette = ["#FFB7B2", "#A6D189", "#FFE4B5", "#8CAAEE", "#D4A5A5", "#E0BBE4"]
        colors = [palette[i % len(palette)] for i in range(len(parts_summary))]

    labels = list(parts_summary.keys())
    values = list(parts_summary.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.65, # 甜甜圈圆环大小
        
        # 样式设置
        marker=dict(colors=colors, line=dict(color='#FFF', width=3)),
        
        # --- 核心交互设置 ---
        textinfo='none',      # 平时不显示任何乱七八糟的文字
        hoverinfo='none',     # 禁用默认悬停，使用下方自定义的
        
        # 这里定义悬停时显示的 HTML 格式
        # <extra></extra> 是为了隐藏旁边那个烦人的 "Trace 0" 标签
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
        
        # --- 悬停卡片的美化设置 (关键) ---
        hoverlabel=dict(
            bgcolor="white",       # 背景纯白
            font_size=16,          # 字体放大，看得更清
            font_family="Microsoft YaHei", # 尽量用微软雅黑
            bordercolor="#FFB7B2", # 边框颜色（蜜桃粉）
            font_color="#555"      # 文字颜色
        ),
        
        # 确保没有静态注释文字，保持圆心干净
        annotations=[] 
    )
    return fig

def render_interactive_card_ui(week_str, total_days, parts_summary, summary_sentence):
    """Bento Grid 风格渲染"""
    # 模块 1: 标题卡片
    st.markdown(f"""
    <div class="bento-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p class="card-title">WEEKLY<br>FITNESS LOG</p>
                <div style="margin-top:10px;color:#666;font-size:14px;">
                    📅 {week_str}
                </div>
            </div>
            <div style="text-align:right;">
                 <div style="font-size:40px;">🥑</div>
                 <div style="background:#FFB7B2;color:white;padding:5px 10px;border-radius:10px;font-size:14px;font-weight:bold;margin-top:5px;">
                    练了 {total_days} 天
                 </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 模块 2: 图表与数据
    c_chart, c_list = st.columns([1.2, 1])
    
    with c_chart:
        fig = get_interactive_donut_chart(parts_summary)
        # config={'displayModeBar': False} 隐藏工具栏，看起来更干净
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    with c_list:
        list_html = '<div class="bento-card" style="height:250px;display:flex;flex-direction:column;justify-content:center;">'
        list_html += '<div style="font-weight:bold;color:#8B4513;margin-bottom:15px;">🎯 训练重点</div>'
        if parts_summary:
            items = parts_summary.most_common(4)
            bullets = ["🍑", "🥥", "🥑", "✨"]
            for i, (part, count) in enumerate(items):
                b = bullets[i % len(bullets)]
                list_html += f'<div class="stat-row"><span class="stat-badge">{b}</span> {part}: <b>{count}次</b></div>'
        else:
             list_html += '<div class="stat-row">✨ 主打一个休息</div>'
        list_html += '</div>'
        st.markdown(list_html, unsafe_allow_html=True)

    # 模块 3: 总结便利贴
    st.markdown(f"""
        <div class="bento-card" style="background:#FFFACD;border-color:#F0E68C;">
            <div style="position:absolute;margin-top:-30px;margin-left:45%;width:40px;height:15px;background:#E6E6FA;transform:rotate(-2deg);opacity:0.8;"></div>
            <b>📝 一句话总结：</b><br>
            <div style="color:#555;margin-top:5px;line-height:1.6;">{summary_sentence}</div>
        </div>
    """, unsafe_allow_html=True)

# ==================== 4. AI & 主逻辑 ====================

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

def consult_ai_advisor(api_key, base_url, model, system_prompt, user_prompt):
    if not api_key: return "AI 未配置：请在 Secrets/环境变量中设置 OPENAI_API_KEY（或 DEEPSEEK_API_KEY）。"
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 暂时掉线了 ({str(e)})"

def main():
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    with st.sidebar:
        st.title("🍑 健身小助手")
        page = st.radio("导航", ["📝 今日记录", "📅 历史记录", "✨ 生成本周内容", "🍽️ 今天吃什么", "🆘 吃多了怎么办"])
        st.markdown("---")

    api_key = get_setting("OPENAI_API_KEY", "DEEPSEEK_API_KEY", default="").strip()
    base_url = get_setting("OPENAI_BASE_URL", "DEEPSEEK_BASE_URL", default="https://api.deepseek.com").strip() or "https://api.deepseek.com"
    model_name = get_setting("OPENAI_MODEL", "DEEPSEEK_MODEL", default="deepseek-chat").strip() or "deepseek-chat"

    if page == "📝 今日记录":
        st.header("📝 今天的汗水时刻")
        with st.form("record_form"):
            date = st.date_input("日期", datetime.today())
            date_str = date.strftime("%Y-%m-%d")
            existing_record = next((r for r in st.session_state.data if r.get("date") == date_str), None)
            if existing_record: st.info("这一天已经有记录啦，保存会覆盖。")
            default_train = existing_record["training"] if existing_record else ["臀腿"]
            options = ["臀腿", "肩背", "有氧/滚泡沫轴", "休息日"]
            safe_default = [t for t in default_train if t in options]
            training = st.multiselect("今天练了什么？", options, default=safe_default)
            diet = st.text_area("饮食记录", height=80, value=existing_record.get("diet", "") if existing_record else "")
            mood = st.text_area("今日感受", height=80, value=existing_record.get("mood", "") if existing_record else "")
            if st.form_submit_button("💾 保存记录"):
                new_record = {
                    "id": existing_record["id"] if existing_record else str(datetime.now().timestamp()),
                    "date": date_str, "training": training, "diet": diet, "mood": mood
                }
                st.session_state.data = [r for r in st.session_state.data if r.get("date") != date_str]
                st.session_state.data.append(new_record)
                save_data(st.session_state.data)
                st.success("记录已保存！今天也要美美哒~ 🎉")

    elif page == "📅 历史记录":
        st.header("📅 你的坚持足迹")
        if not st.session_state.data: st.info("还没有记录哦，快去记录第一天吧！")
        else:
            df = pd.DataFrame(st.session_state.data)
            df['date_obj'] = pd.to_datetime(df['date'])
            for _, row in df.sort_values(by='date_obj', ascending=False).iterrows():
                with st.expander(f"{row['date']} | {' '.join(row['training'])}"):
                    st.write(f"**饮食**: {row['diet']}")
                    st.write(f"**感受**: {row['mood']}")
                    if st.button("删除", key=row['id']):
                        st.session_state.data = [d for d in st.session_state.data if d['id'] != row['id']]
                        save_data(st.session_state.data)
                        st.rerun()

    elif page == "✨ 生成本周内容":
        st.header("✨ 生成你的周报")
        ref_date = st.date_input("选择本周任意一天", datetime.today())
        start, end = get_week_range(ref_date)
        current_data = [d for d in st.session_state.data if start <= datetime.strptime(d['date'], "%Y-%m-%d").date() <= end]
        
        if not current_data: st.warning("这一周还没有数据哦！")
        else:
            from collections import Counter
            all_parts = [p for d in current_data for p in d.get("training", []) if p != "休息日"]
            training_days = len([d for d in current_data if any(t != "休息日" for t in d.get("training", []))])
            part_counts = Counter(all_parts)
            mood_text = " ".join([d.get("mood", "") for d in current_data])
            summary = generate_week_summary_sentence(training_days, part_counts, mood_text)
            week_str = f"{start:%m.%d} - {end:%m.%d}"
            
            st.subheader("📱 动态预览")
            st.caption("鼠标悬停图表可查看详情 👇")
            render_interactive_card_ui(week_str, training_days, part_counts, summary)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🖼️ 下载海报")
                st.caption("适合发朋友圈")
                if st.button("生成高清图片"):
                    img = create_summary_image(week_str, training_days, part_counts, summary)
                    st.image(img, use_container_width=True)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button("📥 下载图片", buf.getvalue(), "weekly.png", "image/png")
            with col2:
                st.subheader("✍️ AI 文案")
                st.caption("适合小红书")
                if st.button("AI 写文案"):
                    with st.spinner("生成中..."):
                        prompt = f"请为我写一篇健身周报小红书文案。\n数据：练了{training_days}天，部位{', '.join(part_counts.keys())}。\n记录：\n" + "\n".join([f"{d['date']}:{d['mood']}" for d in current_data])
                        sys_prompt = "你是一个健身博主。写小红书文案，第一人称，真实接地气，不要AI味，不要用'至关重要'等词。结尾加互动和Hashtag。"
                        res = consult_ai_advisor(api_key, base_url, model_name, sys_prompt, prompt)
                        st.session_state.weekly_copy = res
                if st.session_state.get("weekly_copy"):
                    render_copy_button(st.session_state.weekly_copy)
                    st.text_area("文案", st.session_state.weekly_copy, height=250)

    elif page == "🍽️ 今天吃什么":
        st.header("🍽️ 今天吃什么？")
        st.markdown("不知道吃什么？让 AI 营养师帮你选一个既好吃又符合目标的方案！")
        with st.container():
            col1, col2 = st.columns(2)
            with col1: goal = st.selectbox("当前目标", ["减脂", "维持体重", "增肌"], index=0)
            with col2: scenario = st.selectbox("就餐场景", ["点外卖", "自己做", "外出聚餐", "便利店"], index=0)
            preference = st.text_input("想吃什么口味/类型？（可选）", placeholder="例如：想吃辣的、想嗦粉、不想吃沙拉...")
            if st.button("💡 给我推荐", use_container_width=True):
                with st.spinner("AI 正在扫描菜单..."):
                    sys_prompt = "你是一个懂营养学的健身搭子，说话轻松有趣。请根据用户的【目标】和【场景】，推荐 1-2 个具体的餐食搭配。要求具体（如去皮鸡腿饭+白灼生菜），结合口味，给出简单理由。如果是外卖/外出，必须给一个避雷小技巧。"
                    user_prompt = f"我的目标是【{goal}】，场景【{scenario}】，偏好【{preference or '随便'}】。"
                    advice = consult_ai_advisor(api_key, base_url, model_name, sys_prompt, user_prompt)
                    st.markdown(f"""<div class="chat-bubble"><b>🥑 推荐方案：</b><br>{advice.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)

    elif page == "🆘 吃多了怎么办":
        st.header("🆘 救命！吃多了...")
        st.markdown("别慌！偶尔一顿不会胖的。来制定一个补救计划吧。")
        food_eaten = st.text_input("吃了什么？", placeholder="火锅、蛋糕、自助餐、暴饮暴食...")
        feeling = st.select_slider("现在的感觉", options=["有点撑", "好撑啊", "撑到怀疑人生"])
        if st.button("🧘‍♀️ 帮我分析 & 补救", use_container_width=True):
            if not food_eaten: st.warning("先告诉我吃了什么呀~")
            else:
                with st.spinner("正在安抚你的胃和心..."):
                    sys_prompt = "你是一个超级温暖的健身博主。用户吃多了感到焦虑。回复结构：1.情绪安抚（最重要，告诉她代谢很强，偶尔一顿没事）。2.接下来24h行动建议（饮食清淡、多喝水、简单运动）。语气温柔坚定，像闺蜜。"
                    user_prompt = f"我刚才吃了【{food_eaten}】，感觉【{feeling}】。我很焦虑。"
                    advice = consult_ai_advisor(api_key, base_url, model_name, sys_prompt, user_prompt)
                    st.markdown(f"""<div class="chat-bubble">{advice.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
