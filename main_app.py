import streamlit as st
import os
import tempfile
from datetime import datetime
import base64
from music_generator import MusicGenerator
from zhipu_client import ZhipuClient

# 页面配置
st.set_page_config(
    page_title="AI音乐创作助手 - 元创营参赛作品",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化客户端（使用缓存避免重复初始化）
@st.cache_resource
def get_zhipu_client():
    return ZhipuClient()

@st.cache_resource
def get_music_generator():
    return MusicGenerator()

def autoplay_audio(file_path):
    """自动播放音频"""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
    <audio controls autoplay style="width: 100%;">
        <source src="data:audio/wav;base64,{b64}" type="audio/wav">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

def main():
    # 标题和介绍
    st.title("🎵 AI音乐创作助手")
    st.markdown("""
    **元创营参赛作品** - 帮助非音乐人士轻松制作音乐
    
    只需用文字描述你想要的音乐，AI将为你创作！
    """)
    
    # 侧边栏
    with st.sidebar:
        st.header("使用说明")
        st.markdown("""
        1. 在下方描述你想要的音乐
        2. AI会分析你的需求并生成音乐
        3. 收听生成结果，可以提供反馈进行优化
        4. 下载你满意的作品
        
        **支持的音乐类型：**
        - 流行、电子、古典、爵士、摇滚
        - 古风、轻音乐、背景音乐
        - 游戏配乐、视频配乐
        """)
        
        st.header("技术栈")
        st.markdown("""
        - **语言理解**：智谱AI ChatGLM
        - **音乐生成**：Meta MusicGen
        - **界面框架**：Streamlit
        - **编程语言**：Python
        """)
        
        # 系统状态
        st.header("系统状态")
        if 'generated_count' not in st.session_state:
            st.session_state.generated_count = 0
        st.metric("已生成音乐", st.session_state.generated_count)
    
    # 初始化session state
    if 'music_specs' not in st.session_state:
        st.session_state.music_specs = None
    if 'generated_audio' not in st.session_state:
        st.session_state.generated_audio = None
    if 'music_prompt' not in st.session_state:
        st.session_state.music_prompt = None
    if 'step' not in st.session_state:
        st.session_state.step = 1
    
    # 主界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎤 描述你的音乐")
        
        # 音乐时长选择
        duration = st.slider(
            "选择音乐时长（秒）",
            min_value=15,
            max_value=30,
            value=20,
            help="较长的音乐需要更多的生成时间"
        )
        
        # 用户输入
        user_input = st.text_area(
            "请详细描述你想要的音乐：",
            placeholder="例如：\n• 欢快的电子游戏背景音乐，带有钢琴和鼓点\n• 悲伤的钢琴曲，适合失恋时听\n• 中国古风音乐，使用古筝和笛子\n• 激昂的战斗配乐，有强烈的节奏感",
            height=100
        )
        
        # 快速示例按钮
        example_col1, example_col2, example_col3, example_col4 = st.columns(4)
        with example_col1:
            if st.button("🎮 游戏配乐", use_container_width=True):
                user_input = "电子游戏背景音乐，欢快活泼，有电子合成器和鼓点"
        with example_col2:
            if st.button("😢 悲伤钢琴", use_container_width=True):
                user_input = "悲伤的钢琴曲，缓慢的节奏，表达失落的情感"
        with example_col3:
            if st.button("🏮 中国古风", use_container_width=True):
                user_input = "中国古风音乐，使用古筝和笛子，优雅传统"
        with example_col4:
            if st.button("⚡ 激昂战斗", use_container_width=True):
                user_input = "激昂的战斗配乐，强烈的节奏，使用管弦乐和打击乐"
        
        if st.button("生成音乐", type="primary", use_container_width=True) and user_input:
            with st.spinner("AI正在分析你的音乐需求..."):
                # 分析用户需求
                zhipu_client = get_zhipu_client()
                st.session_state.music_specs = zhipu_client.analyze_music_request(user_input)
                
                # 更新时长设置
                st.session_state.music_specs["duration"] = duration
                
                # 显示分析结果
                st.subheader("🎯 音乐需求分析")
                specs = st.session_state.music_specs
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("风格", specs.get('style', '未知'))
                    st.metric("情绪", specs.get('mood', '未知'))
                with col_s2:
                    st.metric("节奏", specs.get('tempo', '未知'))
                    st.metric("时长", f"{duration}秒")
                with col_s3:
                    instruments = ", ".join(specs.get('instruments', []))
                    st.metric("主要乐器", instruments if instruments else "未指定")
            
            with st.spinner(f"AI正在创作{duration}秒音乐，这可能需要1-3分钟..."):
                # 生成音乐
                music_gen = get_music_generator()
                audio_file, prompt = music_gen.generate_music(st.session_state.music_specs, duration)
                
                st.session_state.generated_audio = audio_file
                st.session_state.music_prompt = prompt
                st.session_state.step = 2
                st.session_state.generated_count += 1
    
    with col2:
        st.subheader("📋 创作进度")
        
        # 步骤指示器
        step_icon = ["1️⃣", "2️⃣", "3️⃣"]
        step_text = ["描述音乐需求", "AI分析需求", "生成音乐"]
        
        for i in range(3):
            if st.session_state.step > i:
                st.success(f"✅ {step_icon[i]} {step_text[i]}")
            elif st.session_state.step == i:
                st.info(f"🔄 {step_icon[i]} {step_text[i]}")
            else:
                st.info(f"{step_icon[i]} {step_text[i]}")
        
        # 显示当前状态
        if st.session_state.music_specs:
            st.info("音乐需求已分析完成")
        if st.session_state.generated_audio:
            st.success("音乐已生成完成！")
    
    # 显示生成结果
    if st.session_state.generated_audio and st.session_state.step >= 2:
        st.markdown("---")
        st.subheader("🎧 生成结果")
        
        # 显示详细提示词
        with st.expander("查看AI使用的详细提示词"):
            st.code(st.session_state.music_prompt, language="text")
        
        # 播放音频
        st.audio(st.session_state.generated_audio)
        
        # 自动播放（可选）
        if st.checkbox("自动播放生成的音乐"):
            autoplay_audio(st.session_state.generated_audio)
        
        # 下载按钮
        with open(st.session_state.generated_audio, "rb") as f:
            st.download_button(
                label="📥 下载音乐文件",
                data=f,
                file_name=os.path.basename(st.session_state.generated_audio),
                mime="audio/wav",
                use_container_width=True
            )
        
        # 反馈和优化
        st.subheader("🔄 优化音乐")
        feedback = st.text_input(
            "对生成的音乐有什么反馈？我们可以优化：",
            placeholder="例如：节奏再快一点、加入更多钢琴元素、情绪再悲伤一些..."
        )
        
        if st.button("根据反馈重新生成", use_container_width=True) and feedback:
            with st.spinner("根据反馈优化音乐..."):
                zhipu_client = get_zhipu_client()
                new_specs = zhipu_client.refine_with_feedback(
                    st.session_state.music_specs, 
                    feedback
                )
                
                # 保持时长设置
                new_specs["duration"] = duration
                st.session_state.music_specs = new_specs
                
                # 重新生成音乐
                music_gen = get_music_generator()
                audio_file, prompt = music_gen.generate_music(new_specs, duration)
                
                st.session_state.generated_audio = audio_file
                st.session_state.music_prompt = prompt
                
                st.success("音乐已根据反馈重新生成！")
                st.rerun()

if __name__ == "__main__":
    main()