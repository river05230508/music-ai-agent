from transformers import pipeline
import scipy.io.wavfile
import torch
import os
from datetime import datetime
import numpy as np
import tempfile

class MusicGenerator:
    def __init__(self):
        self.model_loaded = False
        self.pipe = None
        self.current_device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {self.current_device}")
    
    def load_model(self):
        """加载音乐生成模型"""
        if not self.model_loaded:
            print("正在加载MusicGen模型，首次运行需要下载（约2GB）...")
            try:
                # 使用优化的配置
                self.pipe = pipeline(
                    "text-to-audio", 
                    model="facebook/musicgen-small",
                    device=-1 if self.current_device == "cpu" else 0,
                    torch_dtype=torch.float32
                )
                self.model_loaded = True
                print("模型加载完成！")
            except Exception as e:
                print(f"模型加载失败: {e}")
                # 尝试备用加载方式
                try:
                    self.pipe = pipeline(
                        "text-to-audio", 
                        model="facebook/musicgen-small"
                    )
                    self.model_loaded = True
                    print("模型加载完成（备用方式）！")
                except Exception as e2:
                    print(f"备用加载也失败: {e2}")
                    raise e2
    
    def generate_music(self, music_specs, duration_seconds=20):
        """根据音乐描述生成音乐"""
        if not self.model_loaded:
            self.load_model()
        
        try:
            # 构建详细的提示词
            prompt = self._build_music_prompt(music_specs)
            print(f"生成音乐提示词: {prompt}")
            
            # 计算合适的token数量（关键修改：增加时长）
            tokens_per_second = 50  # MusicGen的经验值
            max_new_tokens = int(tokens_per_second * duration_seconds)
            
            # 安全限制，避免内存溢出
            max_new_tokens = min(max_new_tokens, 1500)  # 最多30秒
            
            print(f"生成 {duration_seconds} 秒音乐，使用 {max_new_tokens} tokens")
            
            # 生成音乐
            print("正在生成音乐，请耐心等待...")
            result = self.pipe(
                prompt,
                forward_params={
                    "do_sample": True,
                    "max_new_tokens": max_new_tokens,
                    "temperature": 1.0  # 增加创造性
                }
            )
            
            # 使用临时文件避免存储问题
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                filename = tmp_file.name
            
            # 保存音频文件
            scipy.io.wavfile.write(
                filename, 
                rate=result["sampling_rate"], 
                data=result["audio"][0]
            )
            
            # 验证文件时长
            actual_duration = len(result["audio"][0]) / result["sampling_rate"]
            print(f"音乐生成完成: {filename}, 实际时长: {actual_duration:.1f}秒")
            
            return filename, prompt
            
        except Exception as e:
            print(f"生成音乐时出错: {e}")
            # 创建一个简单的备用音频文件
            return self._create_fallback_audio(duration_seconds), f"生成失败，使用备用音频: {str(e)}"
    
    def _build_music_prompt(self, music_specs):
        """构建音乐生成提示词"""
        if "music_prompt" in music_specs and music_specs["music_prompt"]:
            return music_specs["music_prompt"]
        
        # 如果没有提供详细提示词，根据其他信息构建
        style = music_specs.get("style", "")
        mood = music_specs.get("mood", "")
        instruments = music_specs.get("instruments", [])
        tempo = music_specs.get("tempo", "")
        
        prompt_parts = []
        if style:
            prompt_parts.append(f"{style}风格")
        if mood:
            prompt_parts.append(f"{mood}的情绪")
        if instruments:
            prompt_parts.append(f"使用{', '.join(instruments)}")
        if tempo:
            prompt_parts.append(f"{tempo}的节奏")
        
        if prompt_parts:
            return "创作一段" + "，".join(prompt_parts) + "的音乐"
        else:
            return "创作一段优美的背景音乐"
    
    def _create_fallback_audio(self, duration_seconds=10):
        """创建备用的简单音频文件（如果生成失败）"""
        sampling_rate = 44100
        duration_samples = int(duration_seconds * sampling_rate)
        
        # 生成简单的和弦进行
        t = np.linspace(0, duration_seconds, duration_samples, False)
        
        # 创建C大调和弦 (C, E, G)
        freq_c = 261.63  # C4
        freq_e = 329.63  # E4  
        freq_g = 392.00  # G4
        
        # 生成三个频率的正弦波
        note_c = 0.3 * np.sin(2 * np.pi * freq_c * t)
        note_e = 0.2 * np.sin(2 * np.pi * freq_e * t)
        note_g = 0.2 * np.sin(2 * np.pi * freq_g * t)
        
        # 合并音符并添加简单的包络
        audio = note_c + note_e + note_g
        envelope = np.ones_like(audio)
        
        # 添加淡入淡出
        fade_samples = int(0.1 * sampling_rate)  # 100ms淡入淡出
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        audio = audio * envelope
        
        # 转换为16位PCM格式
        audio = np.int16(audio * 32767)
        
        # 保存为WAV文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            filename = tmp_file.name
        
        scipy.io.wavfile.write(filename, sampling_rate, audio)
        return filename
    
    def cleanup_temp_files(self):
        """清理临时文件（可选）"""
        pass  # 使用tempfile会自动清理