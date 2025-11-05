import zhipuai
import os
from dotenv import load_dotenv
import json
import re

# 加载环境变量
load_dotenv()

class ZhipuClient:
    def __init__(self):
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            # 如果在部署环境中没有设置API密钥，使用模拟模式
            print("警告: 未找到ZHIPUAI_API_KEY，使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False
            zhipuai.api_key = self.api_key
    
    def analyze_music_request(self, user_input):
        """分析用户输入，提取音乐需求"""
        if self.mock_mode:
            # 模拟模式，用于测试和演示
            return self._create_mock_response(user_input)
        
        prompt = f"""
        你是一个专业的音乐制作AI助手。请分析用户的音乐需求，并返回JSON格式的分析结果。
        
        用户描述："{user_input}"
        
        请返回以下JSON格式：
        {{
            "style": "音乐风格（如：流行、电子、古典、爵士、摇滚、古风、轻音乐等）",
            "mood": "情绪（如：欢快、悲伤、激昂、轻松、浪漫、紧张、舒缓等）", 
            "instruments": ["主要乐器1", "主要乐器2", "主要乐器3"],
            "tempo": "节奏描述（如：快速、中等、慢速、渐快、渐慢）",
            "duration": 20,
            "music_prompt": "用于音乐生成模型的详细英文提示词，描述风格、乐器、情绪和节奏"
        }}
        
        示例：
        用户输入："想要一首在海边散步时听的轻松音乐"
        输出：
        {{
            "style": "轻音乐",
            "mood": "轻松、惬意",
            "instruments": ["钢琴", "弦乐", "海浪声"],
            "tempo": "慢速",
            "duration": 20,
            "music_prompt": "Relaxing beach walk music with gentle piano melody, soft string accompaniment, and subtle ocean wave sounds, creating a peaceful and soothing atmosphere, slow tempo"
        }}
        
        用户输入："激昂的战斗游戏配乐"
        输出：
        {{
            "style": "史诗音乐",
            "mood": "激昂、紧张",
            "instruments": ["管弦乐", "鼓", "合唱"],
            "tempo": "快速",
            "duration": 20,
            "music_prompt": "Epic battle music with powerful orchestra, dramatic drums, and choir vocals, creating intense and heroic atmosphere, fast tempo"
        }}
        """
        
        try:
            response = zhipuai.model_api.invoke(
                model="chatglm_pro",  # 可以使用 chatglm_std 或 chatglm_pro
                prompt=[{"role": "user", "content": prompt}],
                top_p=0.7,
                temperature=0.9,
            )
            
            if response['code'] == 200:
                content = response['data']['choices'][0]['content']
                print(f"智谱AI原始响应: {content}")
                
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # 处理可能的JSON格式问题
                    json_str = json_str.replace("'", '"')
                    return json.loads(json_str)
                else:
                    print("未找到JSON格式响应，使用备用方案")
                    return self._create_fallback_prompt(user_input)
            else:
                print(f"API调用失败: {response}")
                return self._create_fallback_prompt(user_input)
                
        except Exception as e:
            print(f"调用智谱AI时出错: {e}")
            return self._create_fallback_prompt(user_input)
    
    def _create_mock_response(self, user_input):
        """创建模拟响应（当没有API密钥时使用）"""
        # 简单的关键词匹配
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['快乐', '欢快', '开心', '愉快']):
            return {
                "style": "流行",
                "mood": "欢快",
                "instruments": ["钢琴", "鼓", "贝斯"],
                "tempo": "快速",
                "duration": 20,
                "music_prompt": "Happy and upbeat pop music with piano melody, drums and bass, cheerful atmosphere, fast tempo"
            }
        elif any(word in user_input_lower for word in ['悲伤', '伤心', '忧郁', '伤感']):
            return {
                "style": "古典",
                "mood": "悲伤",
                "instruments": ["钢琴", "小提琴"],
                "tempo": "慢速",
                "duration": 20,
                "music_prompt": "Sad and emotional classical music with piano and violin, melancholic atmosphere, slow tempo"
            }
        elif any(word in user_input_lower for word in ['战斗', '激昂', '史诗', '激烈']):
            return {
                "style": "史诗音乐",
                "mood": "激昂",
                "instruments": ["管弦乐", "鼓", "合唱"],
                "tempo": "快速",
                "duration": 20,
                "music_prompt": "Epic and intense battle music with orchestra, powerful drums and choir, heroic atmosphere, fast tempo"
            }
        elif any(word in user_input_lower for word in ['中国', '古风', '传统', '古筝']):
            return {
                "style": "中国古风",
                "mood": "优雅",
                "instruments": ["古筝", "笛子", "二胡"],
                "tempo": "中等",
                "duration": 20,
                "music_prompt": "Traditional Chinese music with guzheng, flute and erhu, elegant and cultural atmosphere, medium tempo"
            }
        else:
            return {
                "style": "流行",
                "mood": "轻松",
                "instruments": ["钢琴", "吉他"],
                "tempo": "中等",
                "duration": 20,
                "music_prompt": f"Beautiful background music based on the description: {user_input}, pleasant and relaxing atmosphere, medium tempo"
            }
    
    def _create_fallback_prompt(self, user_input):
        """创建备用的音乐提示词"""
        return {
            "style": "流行",
            "mood": "轻松",
            "instruments": ["钢琴", "鼓"],
            "tempo": "中等",
            "duration": 20,
            "music_prompt": f"Create a beautiful music piece based on: {user_input}, with pleasant melody and relaxing atmosphere"
        }
    
    def refine_with_feedback(self, original_specs, user_feedback):
        """根据用户反馈优化音乐描述"""
        if self.mock_mode:
            # 在模拟模式下简单调整
            new_specs = original_specs.copy()
            if "快" in user_feedback:
                new_specs["tempo"] = "快速"
                new_specs["music_prompt"] = new_specs["music_prompt"].replace("medium tempo", "fast tempo").replace("slow tempo", "fast tempo")
            elif "慢" in user_feedback:
                new_specs["tempo"] = "慢速" 
                new_specs["music_prompt"] = new_specs["music_prompt"].replace("fast tempo", "slow tempo").replace("medium tempo", "slow tempo")
            return new_specs
        
        prompt = f"""
        原始音乐描述：
        {json.dumps(original_specs, ensure_ascii=False, indent=2)}
        
        用户反馈："{user_feedback}"
        
        请根据用户反馈调整音乐描述，返回更新后的JSON格式。
        重点调整music_prompt字段，使其更符合用户的要求。
        """
        
        try:
            response = zhipuai.model_api.invoke(
                model="chatglm_pro",
                prompt=[{"role": "user", "content": prompt}],
                top_p=0.7,
                temperature=0.7,
            )
            
            if response['code'] == 200:
                content = response['data']['choices'][0]['content']
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    json_str = json_str.replace("'", '"')
                    return json.loads(json_str)
            
            return original_specs  # 如果解析失败，返回原始描述
            
        except Exception as e:
            print(f"优化描述时出错: {e}")
            return original_specs