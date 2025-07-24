#!/usr/bin/env python3
import speech_recognition as sr
import os
import time
import threading
import queue
import pygame
from gtts import gTTS
import tempfile
import requests
import json
from mood_commands import add_mood_commands

class ChineseVoiceAssistant:
    def __init__(self):
        # 初始化語音識別
        self.recognizer = sr.Recognizer()
        
        # 尋找並使用 ReSpeaker 麥克風 (card 2, device 0)
        try:
            self.microphone = sr.Microphone(device_index=None)
            # 嘗試找到 ReSpeaker 設備
            for i, name in enumerate(sr.Microphone.list_microphone_names()):
                if "ReSpeaker" in name or "ArrayUAC10" in name:
                    self.microphone = sr.Microphone(device_index=i)
                    print(f"使用麥克風: {name}")
                    break
        except:
            print("使用預設麥克風")
            self.microphone = sr.Microphone()
        
        # 初始化 pygame for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # AI 服務配置
        self.ai_service = "ollama"  # 預設使用本地 Ollama
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Ollama 配置
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "llama2-chinese"  # 或其他支援中文的模型
        
        # 用於控制程序流程
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # 對話歷史和心情分析
        self.conversation_history = []
        self.mood_history = []
        # 多維度情緒系統 (1-10分)
        self.current_emotions = {
            '開心': 5,  # Happy
            '傷心': 1,  # Sad
            '生氣': 1,  # Angry
            '焦慮': 1,  # Anxious
            '興奮': 5   # Excited
        }
        
        # 檢查可用的 AI 服務
        self._check_available_services()
        
        # 初始化心情命令處理器
        self.mood_command_handler = add_mood_commands(self)
        
    def listen_for_audio(self):
        """持續監聽麥克風輸入"""
        with self.microphone as source:
            # 調整環境噪音
            print("正在調整環境噪音，請稍候...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("準備就緒！請說話...")
            
            while self.is_listening:
                try:
                    # 監聽音頻
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"監聽錯誤: {e}")
    
    def process_speech(self, audio):
        """將語音轉換為文字"""
        try:
            # 使用 Google 語音識別 (支持中文)
            text = self.recognizer.recognize_google(audio, language="zh-TW")
            print(f"您說: {text}")
            return text
        except sr.UnknownValueError:
            print("無法識別語音")
            return None
        except sr.RequestError as e:
            print(f"語音識別服務錯誤: {e}")
            return None
    
    def _check_available_services(self):
        """檢查可用的 AI 服務"""
        print("檢查可用的 AI 服務...")
        
        # 檢查 Ollama
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if response.status_code == 200:
                print("✓ Ollama 服務可用")
                return
        except:
            print("✗ Ollama 服務不可用")
        
        # 檢查 OpenAI
        if self.openai_api_key:
            self.ai_service = "openai"
            print("✓ 將使用 OpenAI API")
            return
            
        # 檢查 Anthropic Claude
        if self.anthropic_api_key:
            self.ai_service = "anthropic"
            print("✓ 將使用 Anthropic Claude API")
            return
            
        # 檢查 Google Gemini
        if self.gemini_api_key:
            self.ai_service = "gemini"
            print("✓ 將使用 Google Gemini API")
            return
            
        # 使用智能回應生成器 (免費)
        self.ai_service = "huggingface"
        print("✓ 將使用智能回應生成器 (無需 API)")

    def get_ai_response(self, text):
        """獲取 AI 回應"""
        try:
            if self.ai_service == "ollama":
                return self._get_ollama_response(text)
            elif self.ai_service == "openai":
                return self._get_openai_response(text)
            elif self.ai_service == "anthropic":
                return self._get_anthropic_response(text)
            elif self.ai_service == "gemini":
                return self._get_gemini_response(text)
            elif self.ai_service == "huggingface":
                return self._get_huggingface_response(text)
            else:
                return self.simple_response(text)
        except Exception as e:
            print(f"AI 服務錯誤: {e}")
            return self.simple_response(text)
    
    def _get_ollama_response(self, text):
        """使用 Ollama 本地模型"""
        try:
            data = {
                "model": self.ollama_model,
                "prompt": f"請用繁體中文回答：{text}",
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate", 
                json=data, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '抱歉，我無法理解您的問題。')
            else:
                raise Exception(f"Ollama API 錯誤: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama 連接失敗: {e}")
    
    def _get_openai_response(self, text):
        """使用 OpenAI API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "你是一個友善的中文助手，請用繁體中文回答，保持回答簡潔。"},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenAI API 錯誤: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"OpenAI 連接失敗: {e}")
    
    def _get_anthropic_response(self, text):
        """使用 Anthropic Claude API"""
        try:
            headers = {
                'x-api-key': self.anthropic_api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 150,
                "messages": [
                    {"role": "user", "content": f"請用繁體中文回答，保持簡潔：{text}"}
                ]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                raise Exception(f"Anthropic API 錯誤: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Anthropic 連接失敗: {e}")
    
    def _get_gemini_response(self, text):
        """使用 Google Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_api_key}"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"請用繁體中文回答，保持簡潔：{text}"
                    }]
                }]
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                raise Exception(f"Gemini API 錯誤: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Gemini 連接失敗: {e}")
    
    def _get_huggingface_response(self, text):
        """使用替代的免費 AI 服務"""
        try:
            # 使用 Groq 免費 API (需要註冊但有免費額度)
            groq_key = os.getenv('GROQ_API_KEY')
            if groq_key:
                return self._get_groq_response(text, groq_key)
            
            # 使用簡單的翻譯服務作為對話回應
            return self._get_mock_ai_response(text)
                
        except Exception as e:
            raise Exception(f"免費 AI 服務連接失敗: {e}")
    
    def _get_groq_response(self, text, api_key):
        """使用 Groq 免費 API"""
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "你是一個友善的中文助手，請用繁體中文回答，保持回答簡潔。"},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"Groq API 錯誤: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Groq 連接失敗: {e}")
    
    def _get_mock_ai_response(self, text):
        """智能回應生成器（無需 API）"""
        import random
        
        # 根據關鍵字生成相應回應
        if any(word in text for word in ["你好", "哈囉", "嗨"]):
            responses = ["你好！很高興與您對話！", "哈囉！有什麼我可以幫助您的嗎？", "嗨！今天過得如何？"]
            return random.choice(responses)
        
        elif any(word in text for word in ["時間", "幾點", "現在"]):
            import datetime
            now = datetime.datetime.now()
            return f"現在是 {now.strftime('%Y年%m月%d日 %H點%M分')}"
        
        elif any(word in text for word in ["天氣", "氣溫", "下雨"]):
            responses = ["我無法查詢即時天氣，建議您查看天氣應用程式。", "今天記得帶傘出門喔！", "希望今天是個好天氣！"]
            return random.choice(responses)
        
        elif any(word in text for word in ["謝謝", "感謝", "辛苦"]):
            responses = ["不客氣！很高興能幫助您！", "這是我應該做的！", "隨時為您服務！"]
            return random.choice(responses)
        
        elif any(word in text for word in ["怎麼", "如何", "方法"]):
            responses = ["這是個好問題！不過我需要更多資訊才能給您準確的建議。", "讓我想想...這個問題可能需要查詢更詳細的資料。", "建議您可以搜尋相關資訊或詢問專家。"]
            return random.choice(responses)
        
        elif any(word in text for word in ["再見", "掰掰", "結束"]):
            responses = ["再見！祝您有美好的一天！", "掰掰！期待下次與您對話！", "再會！保重身體！"]
            return random.choice(responses)
        
        else:
            # 通用回應
            responses = [
                "我理解您的意思，這確實是個有趣的話題。",
                "感謝您與我分享這個想法！",
                "這讓我想到很多相關的事情。",
                "您說得很有道理！",
                "這是個值得深入思考的問題。",
                "我會記住您說的話。",
                "感謝您的耐心，讓我們繼續聊天吧！"
            ]
            return random.choice(responses)
    
    def analyze_mood(self, user_text, ai_response):
        """分析用戶多維度情緒 (1-10分)"""
        try:
            # 記錄對話
            conversation_entry = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'user': user_text,
                'ai': ai_response
            }
            self.conversation_history.append(conversation_entry)
            
            # 保持最近20輪對話
            if len(self.conversation_history) > 20:
                self.conversation_history.pop(0)
            
            # 分析情緒
            emotion_scores = self._calculate_emotion_scores(user_text)
            
            # 更新當前情緒
            self.current_emotions = emotion_scores.copy()
            
            # 記錄情緒歷史
            mood_entry = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'text': user_text,
                'emotions': emotion_scores.copy(),
                'dominant_emotion': self._get_dominant_emotion(emotion_scores)
            }
            self.mood_history.append(mood_entry)
            
            # 保持最近10次情緒記錄
            if len(self.mood_history) > 10:
                self.mood_history.pop(0)
            
            # 顯示情緒分析
            self._display_emotion_analysis(emotion_scores)
            
            return emotion_scores
            
        except Exception as e:
            print(f"情緒分析錯誤: {e}")
            return self.current_emotions  # 返回當前情緒
    
    def _calculate_emotion_scores(self, text):
        """計算多維度情緒分數"""
        # 初始化情緒分數
        emotions = {
            '開心': 1,
            '傷心': 1,
            '生氣': 1,
            '焦慮': 1,
            '興奮': 1
        }
        
        # 情緒關鍵字映射
        emotion_keywords = {
            '開心': {
                "開心": 3, "高興": 3, "快樂": 3, "喜歡": 2, "愛": 2.5, "棒": 2,
                "好": 1.5, "讚": 2, "太好了": 3, "哈哈": 2.5, "笑": 2, "滿意": 2,
                "感謝": 2, "謝謝": 2, "幸福": 3, "美好": 2.5, "完美": 3, "成功": 2.5,
                "勝利": 3, "厲害": 2, "優秀": 2, "讚美": 2, "鼓勵": 2, "享受": 2.5,
                "愉快": 2, "歡樂": 3, "有趣": 2, "可愛": 2
            },
            '傷心': {
                "難過": 3, "傷心": 3, "失望": 2.5, "憂鬱": 3, "沮喪": 3, "哭": 3,
                "痛苦": 3, "寂寞": 2.5, "孤單": 2.5, "落淚": 3, "心痛": 3, "失落": 2.5,
                "悲傷": 3, "痛": 2, "不開心": 2, "鬱悶": 2.5, "難受": 2.5, "委屈": 2.5
            },
            '生氣': {
                "生氣": 3, "憤怒": 3, "討厭": 2.5, "恨": 3, "煩": 2, "煩躁": 2.5,
                "火大": 3, "暴怒": 3, "氣死": 3, "不滿": 2, "抱怨": 2, "不爽": 2.5,
                "可惡": 2.5, "該死": 3, "混蛋": 3, "憎恨": 3, "厭惡": 2.5
            },
            '焦慮': {
                "焦慮": 3, "擔心": 2.5, "害怕": 2.5, "恐懼": 3, "緊張": 2.5, "不安": 2.5,
                "煩惱": 2, "壓力": 2.5, "慌張": 2.5, "著急": 2.5, "急": 2, "怕": 2,
                "憂慮": 2.5, "忐忑": 2.5, "心慌": 2.5, "擔憂": 2.5, "恐慌": 3
            },
            '興奮': {
                "興奮": 3, "激動": 3, "期待": 2.5, "熱情": 2.5, "衝動": 2, "亢奮": 3,
                "狂喜": 3, "欣喜": 2.5, "雀躍": 3, "熱血": 2.5, "激昂": 2.5, "振奮": 2.5,
                "高昂": 2.5, "迫不及待": 3, "躍躍欲試": 2.5, "熱烈": 2.5
            }
        }
        
        # 強化詞
        intensifiers = {
            "很": 1.3, "非常": 1.5, "超": 1.6, "超級": 1.8, "極": 1.7, "特別": 1.4,
            "真的": 1.2, "實在": 1.2, "太": 1.5, "好": 1.2, "十分": 1.4, "相當": 1.3,
            "異常": 1.6, "格外": 1.4, "極其": 1.7, "極度": 1.8
        }
        
        # 否定詞
        negators = ["不", "沒", "無", "別", "未", "否", "非"]
        
        # 分析文本
        words = list(text)  # 改為字元列表以更好地處理中文
        text_lower = text.lower()
        
        # 計算每個情緒的分數
        for emotion, keywords in emotion_keywords.items():
            for keyword, weight in keywords.items():
                if keyword in text_lower:
                    # 基礎分數
                    base_score = weight
                    
                    # 檢查強化詞
                    for intensifier, multiplier in intensifiers.items():
                        if intensifier + keyword in text_lower:
                            base_score *= multiplier
                            break
                    
                    # 檢查否定詞
                    is_negated = False
                    for negator in negators:
                        if negator + keyword in text_lower or negator + "是" + keyword in text_lower:
                            is_negated = True
                            break
                    
                    if is_negated:
                        # 否定詞反轉情緒
                        opposite_emotions = {
                            '開心': '傷心',
                            '傷心': '開心',
                            '生氣': '開心',
                            '焦慮': '開心',
                            '興奮': '傷心'
                        }
                        if emotion in opposite_emotions:
                            emotions[opposite_emotions[emotion]] = min(10, emotions[opposite_emotions[emotion]] + base_score * 0.7)
                    else:
                        emotions[emotion] = min(10, emotions[emotion] + base_score)
        
        # 語調和標點符號分析
        if "！" in text:
            if any(word in text for word in ["好", "棒", "讚", "太好了"]):
                emotions['興奮'] = min(10, emotions['興奮'] + 1)
                emotions['開心'] = min(10, emotions['開心'] + 0.5)
            elif any(word in text for word in ["煩", "氣", "討厭"]):
                emotions['生氣'] = min(10, emotions['生氣'] + 1)
        
        if "？" in text:
            emotions['焦慮'] = min(10, emotions['焦慮'] + 0.3)
        
        if "..." in text or "。。。" in text:
            emotions['傷心'] = min(10, emotions['傷心'] + 0.5)
            emotions['焦慮'] = min(10, emotions['焦慮'] + 0.3)
        
        # 確保所有分數在1-10範圍內
        for emotion in emotions:
            emotions[emotion] = max(1, min(10, round(emotions[emotion], 1)))
        
        return emotions
    
    def _get_dominant_emotion(self, emotions):
        """獲取主導情緒"""
        # 找出分數最高的情緒
        max_emotion = max(emotions, key=emotions.get)
        max_score = emotions[max_emotion]
        
        # 如果最高分太低，返回"平靜"
        if max_score <= 3:
            return "平靜"
        
        return max_emotion
    
    def _display_emotion_analysis(self, emotions):
        """顯示情緒分析結果"""
        print("\n🎭 情緒分析結果:")
        print("─" * 40)
        
        # 情緒圖標
        emotion_icons = {
            '開心': '😊',
            '傷心': '😢',
            '生氣': '😠',
            '焦慮': '😰',
            '興奮': '🤩'
        }
        
        # 顯示每個情緒的分數條
        for emotion, score in emotions.items():
            icon = emotion_icons.get(emotion, '🎭')
            bar = '█' * int(score) + '░' * (10 - int(score))
            print(f"{icon} {emotion}: [{bar}] {score}/10")
        
        # 顯示主導情緒
        dominant = self._get_dominant_emotion(emotions)
        print(f"\n💭 主導情緒: {dominant}")
        print("─" * 40)
    
    def _get_emotion_level_description(self, emotion, score):
        """根據情緒類型和分數獲取描述"""
        level_descriptions = {
            '開心': {
                (9, 10): "極度開心",
                (7, 9): "非常開心",
                (5, 7): "愉快",
                (3, 5): "略感愉悅",
                (1, 3): "平靜"
            },
            '傷心': {
                (9, 10): "極度傷心",
                (7, 9): "非常難過",
                (5, 7): "有些失落",
                (3, 5): "略感憂傷",
                (1, 3): "情緒平穩"
            },
            '生氣': {
                (9, 10): "極度憤怒",
                (7, 9): "非常生氣",
                (5, 7): "有些惱火",
                (3, 5): "略感不滿",
                (1, 3): "心平氣和"
            },
            '焦慮': {
                (9, 10): "極度焦慮",
                (7, 9): "非常緊張",
                (5, 7): "有些擔心",
                (3, 5): "略感不安",
                (1, 3): "輕鬆自在"
            },
            '興奮': {
                (9, 10): "極度興奮",
                (7, 9): "非常激動",
                (5, 7): "充滿期待",
                (3, 5): "略感振奮",
                (1, 3): "情緒平靜"
            }
        }
        
        descriptions = level_descriptions.get(emotion, {})
        for (min_score, max_score), description in descriptions.items():
            if min_score <= score <= max_score:
                return description
        
        return "情緒狀態"
    
    def get_mood_aware_response(self, text):
        """獲取考慮情緒的 AI 回應"""
        # 檢查是否為情緒相關命令
        mood_response = self.mood_command_handler(text)
        if mood_response:
            return mood_response
        
        # 先獲取基本 AI 回應
        base_response = self.get_ai_response(text)
        
        # 分析用戶情緒
        emotions = self.analyze_mood(text, base_response)
        
        # 獲取主導情緒
        dominant_emotion = self._get_dominant_emotion(emotions)
        
        # 根據不同情緒給予適當回應
        emotion_response = ""
        
        if emotions['傷心'] >= 7:
            # 用戶很傷心，給予安慰
            emotion_response = self._get_comfort_response()
        elif emotions['生氣'] >= 7:
            # 用戶很生氣，給予理解
            emotion_response = self._get_anger_response()
        elif emotions['焦慮'] >= 7:
            # 用戶很焦慮，給予支持
            emotion_response = self._get_anxiety_response()
        elif emotions['開心'] >= 7 or emotions['興奮'] >= 7:
            # 用戶很開心或興奮，表示祝賀
            emotion_response = self._get_celebration_response()
        
        if emotion_response:
            return f"{base_response} {emotion_response}"
        else:
            return base_response
    
    def _get_comfort_response(self):
        """安慰回應"""
        responses = [
            "我能感受到您現在心情不太好，希望我能幫助您感覺好一些。",
            "每個人都會有低潮的時候，這很正常。我會陪伴您度過這段時間。",
            "雖然現在可能不太順利，但相信明天會更好的！",
            "如果需要聊天或發洩，我隨時都在這裡聽您說。",
            "深呼吸一下，讓我們一起面對這個挑戰吧。"
        ]
        import random
        return random.choice(responses)
    
    def _get_celebration_response(self):
        """慶祝回應"""
        responses = [
            "聽起來您現在心情很好呢！我也為您感到開心！",
            "您的快樂也感染了我，真是太棒了！",
            "看到您這麼開心，我也覺得很愉快！",
            "保持這樣的好心情，繼續享受美好的時光吧！",
            "您的笑聲是最美的音樂！"
        ]
        import random
        return random.choice(responses)
    
    def _get_anger_response(self):
        """生氣時的理解回應"""
        responses = [
            "我能理解您現在很生氣，有什麼我可以幫助的嗎？",
            "深呼吸一下，讓情緒慢慢平復。我在這裡聽您訴說。",
            "發洩出來會好一些的，請告訴我發生了什麼事。",
            "我明白這種感覺很不好受，希望能幫您緩解一下。",
            "生氣是正常的情緒反應，讓我們一起處理這個問題。"
        ]
        import random
        return random.choice(responses)
    
    def _get_anxiety_response(self):
        """焦慮時的支持回應"""
        responses = [
            "別擔心，我們一步一步來解決問題。",
            "深呼吸，放鬆一下。一切都會好起來的。",
            "我理解您的焦慮，讓我來幫您整理一下思緒。",
            "記住，您並不孤單。我會陪著您度過這段時間。",
            "讓我們專注於現在能做的事情，其他的慢慢來。"
        ]
        import random
        return random.choice(responses)
    
    def get_mood_summary(self):
        """獲取情緒統計摘要"""
        if not self.mood_history:
            return "暫無情緒記錄"
        
        # 計算每個情緒的平均分數
        emotion_totals = {
            '開心': 0,
            '傷心': 0,
            '生氣': 0,
            '焦慮': 0,
            '興奮': 0
        }
        
        for entry in self.mood_history:
            for emotion, score in entry['emotions'].items():
                emotion_totals[emotion] += score
        
        # 計算平均值
        num_records = len(self.mood_history)
        emotion_averages = {
            emotion: round(total / num_records, 1)
            for emotion, total in emotion_totals.items()
        }
        
        # 找出主導情緒
        dominant_emotion = self._get_dominant_emotion(emotion_averages)
        
        # 構建摘要
        summary = f"\n📊 最近 {num_records} 次對話的情緒統計:\n"
        summary += "─" * 35 + "\n"
        
        emotion_icons = {
            '開心': '😊',
            '傷心': '😢',
            '生氣': '😠',
            '焦慮': '😰',
            '興奮': '🤩'
        }
        
        for emotion, avg_score in emotion_averages.items():
            icon = emotion_icons.get(emotion, '🎭')
            bar = '█' * int(avg_score) + '░' * (10 - int(avg_score))
            summary += f"{icon} {emotion}: [{bar}] {avg_score}/10\n"
        
        summary += f"\n💭 平均主導情緒: {dominant_emotion}"
        
        return summary
    
    def simple_response(self, text):
        """簡單的回應邏輯（當沒有 AI API 時使用）"""
        responses = {
            "你好": "你好！很高興見到你！",
            "你是誰": "我是你的語音助手！",
            "現在幾點": f"現在是 {time.strftime('%H點%M分')}",
            "再見": "再見！祝你有美好的一天！"
        }
        
        for key in responses:
            if key in text:
                return responses[key]
        
        return "抱歉，我不太明白你的意思。"
    
    def speak(self, text):
        """將文字轉換為語音並播放"""
        try:
            # 使用 gTTS 生成中文語音
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts = gTTS(text=text, lang='zh-tw')
                tts.save(tmp_file.name)
                tmp_filename = tmp_file.name
            
            # 使用 pygame 播放音頻
            pygame.mixer.music.load(tmp_filename)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # 刪除臨時文件
            os.unlink(tmp_filename)
            
        except Exception as e:
            print(f"語音合成錯誤: {e}")
            print(f"AI 回應: {text}")
    
    def run(self):
        """主程序循環"""
        self.is_listening = True
        
        # 在背景線程中持續監聽
        listen_thread = threading.Thread(target=self.listen_for_audio)
        listen_thread.daemon = True
        listen_thread.start()
        
        print("\n中文語音助手已啟動！")
        print("說 '再見' 或按 Ctrl+C 結束程序\n")
        
        try:
            while self.is_listening:
                # 檢查是否有新的音頻
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get()
                    
                    # 處理語音
                    text = self.process_speech(audio)
                    if text:
                        # 檢查是否要結束
                        if "再見" in text or "結束" in text:
                            self.speak("再見！祝你有美好的一天！")
                            self.is_listening = False
                            break
                        
                        # 獲取並播放考慮心情的 AI 回應
                        response = self.get_mood_aware_response(text)
                        print(f"AI: {response}")
                        self.speak(response)
                        
                        # 顯示心情統計
                        print(f"📊 {self.get_mood_summary()}")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n程序被中斷")
        finally:
            self.is_listening = False
            pygame.mixer.quit()
            print("語音助手已關閉")

if __name__ == "__main__":
    assistant = ChineseVoiceAssistant()
    assistant.run()