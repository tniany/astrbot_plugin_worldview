from typing import List


class PersonalityLearner:
    def __init__(self, window_size: int = 10):
        self.window_size = window_size

    def generate_hint(self, user_messages: List[str]) -> str:
        messages = [m for m in user_messages if isinstance(m, str) and m.strip()]
        if len(messages) < 2:
            return ""

        recent = messages[-self.window_size:]
        hints = []

        emoji_ratio = sum(1 for m in recent if self._has_emoji(m)) / len(recent)
        if emoji_ratio > 0.3:
            hints.append("用户喜欢使用表情符号，可适当使用 emoji 回应")

        short_ratio = sum(1 for m in recent if len(m) <= 15) / len(recent)
        if short_ratio > 0.5:
            hints.append("用户习惯简短回复，回答宜简洁")
        elif sum(len(m) for m in recent) / len(recent) > 80:
            hints.append("用户倾向完整表达，回答可适当详细")

        if any(m.endswith(("~", "～", "!", "！")) for m in recent):
            hints.append("用户语气较活泼，可保持轻松亲切")

        if not hints:
            return ""

        return "风格适配提示（在保持原有人设基础上）：" + "；".join(hints) + "。"

    def _has_emoji(self, text: str) -> bool:
        for char in text:
            if ord(char) > 0x1F300:
                return True
        return False
