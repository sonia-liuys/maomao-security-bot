#!/usr/bin/env python3
"""
多維度情緒分析命令擴展
支援：開心、傷心、生氣、焦慮、興奮 (1-10分)
"""

def add_mood_commands(assistant):
    """為語音助手添加情緒相關命令"""
    
    def handle_mood_commands(text):
        """處理心情相關命令"""
        text_lower = text.lower()
        
        if "心情統計" in text or "心情報告" in text or "情緒統計" in text or "情緒報告" in text:
            return get_mood_report(assistant)
        elif "心情歷史" in text or "心情記錄" in text or "情緒歷史" in text or "情緒記錄" in text:
            return get_mood_history(assistant)
        elif "我的心情" in text or "我的情緒" in text or "目前心情" in text or "目前情緒" in text:
            return get_current_mood(assistant)
        elif "重設心情" in text or "重設情緒" in text or "清除心情" in text or "清除情緒" in text:
            return reset_mood_history(assistant)
        
        return None
    
    def get_mood_report(assistant):
        """獲取詳細情緒報告"""
        if not assistant.mood_history:
            return "您還沒有情緒記錄呢！開始和我聊天吧！"
        
        # 計算每個情緒的統計數據
        emotion_stats = {
            '開心': {'total': 0, 'max': 0, 'min': 10},
            '傷心': {'total': 0, 'max': 0, 'min': 10},
            '生氣': {'total': 0, 'max': 0, 'min': 10},
            '焦慮': {'total': 0, 'max': 0, 'min': 10},
            '興奮': {'total': 0, 'max': 0, 'min': 10}
        }
        
        for entry in assistant.mood_history:
            for emotion, score in entry['emotions'].items():
                emotion_stats[emotion]['total'] += score
                emotion_stats[emotion]['max'] = max(emotion_stats[emotion]['max'], score)
                emotion_stats[emotion]['min'] = min(emotion_stats[emotion]['min'], score)
        
        num_records = len(assistant.mood_history)
        
        # 計算每個情緒的平均值
        emotion_averages = {}
        for emotion, stats in emotion_stats.items():
            emotion_averages[emotion] = round(stats['total'] / num_records, 1)
        
        # 分析趨勢
        trend_analysis = ""
        if num_records >= 3:
            recent_emotions = {emotion: 0 for emotion in emotion_stats}
            earlier_emotions = {emotion: 0 for emotion in emotion_stats}
            
            # 最近3次的平均
            for entry in assistant.mood_history[-3:]:
                for emotion, score in entry['emotions'].items():
                    recent_emotions[emotion] += score / 3
            
            # 之前的平均
            if num_records > 3:
                for entry in assistant.mood_history[:-3]:
                    for emotion, score in entry['emotions'].items():
                        earlier_emotions[emotion] += score / (num_records - 3)
            
            # 分析每個情緒的趨勢
            trends = []
            for emotion in emotion_stats:
                if recent_emotions[emotion] > earlier_emotions[emotion] + 1:
                    trends.append(f"{emotion}↑")
                elif recent_emotions[emotion] < earlier_emotions[emotion] - 1:
                    trends.append(f"{emotion}↓")
            
            if trends:
                trend_analysis = "趨勢: " + ", ".join(trends)
            else:
                trend_analysis = "情緒相對穩定"
        else:
            trend_analysis = "資料不足以分析趨勢"
        
        # 建立報告
        report = f"""
🎭 多維度情緒分析報告
{'=' * 40}
📊 平均情緒分數:
"""
        
        emotion_icons = {'開心': '😊', '傷心': '😢', '生氣': '😠', '焦慮': '😰', '興奮': '🤩'}
        
        for emotion, avg in emotion_averages.items():
            icon = emotion_icons.get(emotion, '🎭')
            bar = '█' * int(avg) + '░' * (10 - int(avg))
            report += f"  {icon} {emotion}: [{bar}] {avg}/10\n"
        
        report += f"""
📈 統計資料:
  - 總對話次數: {len(assistant.conversation_history)}
  - 記錄次數: {num_records}
  - {trend_analysis}

💭 主導情緒: {assistant._get_dominant_emotion(emotion_averages)}
        """
        
        return report.strip()
    
    def get_mood_history(assistant):
        """獲取情緒歷史"""
        if not assistant.mood_history:
            return "暫無情緒記錄。"
        
        history = "📈 最近情緒記錄:\n"
        history += "=" * 40 + "\n"
        
        emotion_icons = {'開心': '😊', '傷心': '😢', '生氣': '😠', '焦慮': '😰', '興奮': '🤩'}
        
        for entry in assistant.mood_history[-5:]:  # 顯示最近5次
            history += f"\n⏰ {entry['timestamp']}\n"
            history += f"💭 主導情緒: {entry['dominant_emotion']}\n"
            
            # 顯示每個情緒的分數
            for emotion, score in entry['emotions'].items():
                icon = emotion_icons.get(emotion, '🎭')
                if score >= 5:
                    history += f"  {icon} {emotion}: {score}/10\n"
            
            history += "-" * 30 + "\n"
        
        return history
    
    def get_current_mood(assistant):
        """獲取當前情緒"""
        emotions = assistant.current_emotions
        dominant = assistant._get_dominant_emotion(emotions)
        
        result = "🎭 您目前的情緒狀態:\n"
        result += "=" * 30 + "\n"
        
        emotion_icons = {'開心': '😊', '傷心': '😢', '生氣': '😠', '焦慮': '😰', '興奮': '🤩'}
        
        for emotion, score in emotions.items():
            icon = emotion_icons.get(emotion, '🎭')
            bar = '█' * int(score) + '░' * (10 - int(score))
            description = assistant._get_emotion_level_description(emotion, score)
            result += f"{icon} {emotion}: [{bar}] {score}/10 ({description})\n"
        
        result += f"\n💭 主導情緒: {dominant}"
        
        return result
    
    def reset_mood_history(assistant):
        """重設情緒歷史"""
        assistant.mood_history.clear()
        assistant.conversation_history.clear()
        assistant.current_emotions = {
            '開心': 5,
            '傷心': 1,
            '生氣': 1,
            '焦慮': 1,
            '興奮': 5
        }
        return "情緒記錄已重設，讓我們重新開始記錄您的情緒吧！"
    
    return handle_mood_commands