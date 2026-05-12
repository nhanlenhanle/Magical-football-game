"""
profile.py – Hệ thống tài khoản & nâng cấp của người chơi.
"""
import json
import os

PROFILE_PATH = "player_profile.json"

# XP cần để lên level n → n+1
def xp_for_next_level(level: int) -> int:
    """Tính lượng XP cần thiết để tăng từ level hiện tại lên level kế tiếp."""
    return 100 * level   # lv1→2: 100, lv2→3: 200, …


# ─────────────── Định nghĩa cây nâng cấp ──────────────────────────────────
# Mỗi entry:  key, name, group, max_level, costs[], desc_template, bonus_per_level, stat_cap
UPGRADE_DEFS = {
    "physical": [
        {
            "key": "kick_power",
            "name": "Kick Power",
            "max_level": 5,
            "costs": [100, 200, 350, 550, 800],
            "desc_template": "+{:.0f}% luc sut",
            "bonus_per_level": 0.10,
            "stat_cap": 0.50,
        },
        {
            "key": "speed",
            "name": "Speed",
            "max_level": 5,
            "costs": [120, 240, 400, 600, 900],
            "desc_template": "+{:.0f}% toc do",
            "bonus_per_level": 0.07,
            "stat_cap": 0.35,
        },
        {
            "key": "mass",
            "name": "Mass",
            "max_level": 5,
            "costs": [100, 200, 350, 550, 800],
            "desc_template": "+{:.0f}% khoi luong",
            "bonus_per_level": 0.08,
            "stat_cap": 0.40,
        },
        {
            "key": "acceleration",
            "name": "Acceleration",
            "max_level": 4,
            "costs": [150, 300, 500, 750],
            "desc_template": "+{:.0f}% gia toc",
            "bonus_per_level": 0.10,
            "stat_cap": 0.40,
        },
    ],
    "skill": [
        {
            "key": "cooldown_reduction",
            "name": "Cooldown Red.",
            "max_level": 5,
            "costs": [200, 400, 650, 950, 1300],
            "desc_template": "-{:.0f}% hoi chieu",
            "bonus_per_level": 0.06,
            "stat_cap": 0.30,
        },
        {
            "key": "skill_duration",
            "name": "Skill Duration",
            "max_level": 4,
            "costs": [180, 360, 600, 900],
            "desc_template": "+{:.0f}% thoi gian",
            "bonus_per_level": 0.08,
            "stat_cap": 0.32,
        },
        {
            "key": "skill_effectiveness",
            "name": "Skill Power",
            "max_level": 3,
            "costs": [250, 500, 850],
            "desc_template": "+{:.0f}% hieu qua",
            "bonus_per_level": 0.10,
            "stat_cap": 0.30,
        },
    ],
}

# Phẳng hoá để tra cứu nhanh
_DEFS_BY_KEY = {
    udef["key"]: udef
    for group in UPGRADE_DEFS.values()
    for udef in group
}

_DEFAULT_STATS = {key: 0 for key in _DEFS_BY_KEY}


class PlayerProfile:
    """Dữ liệu persistent của người chơi: level, xp, coins, stats."""

    def __init__(self):
        self.data = {
            "level": 1,
            "xp": 0,
            "coins": 0,
            "stats": dict(_DEFAULT_STATS),
        }
        self.load()

    # ──────────── persistence ─────────────────────────────────────────────
    def load(self):
        """Tải dữ liệu profile từ file JSON nếu tồn tại."""
        if os.path.exists(PROFILE_PATH):
            try:
                with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # merge để đảm bảo không mất key mới
                for k, v in saved.items():
                    if k == "stats":
                        for sk in _DEFAULT_STATS:
                            self.data["stats"][sk] = saved["stats"].get(sk, 0)
                    else:
                        self.data[k] = v
            except Exception:
                pass

    def save(self):
        """Lưu dữ liệu profile hiện tại vào file JSON."""
        try:
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # ──────────── properties tiện lợi ────────────────────────────────────
    @property
    def level(self) -> int:
        """Trả về cấp độ hiện tại của người chơi."""
        return self.data["level"]

    @property
    def xp(self) -> int:
        """Trả về lượng XP hiện tại của người chơi."""
        return self.data["xp"]

    @property
    def coins(self) -> int:
        """Trả về số lượng coins hiện tại của người chơi."""
        return self.data["coins"]

    @property
    def stats(self) -> dict:
        """Trả về dict chứa cấp độ của các chỉ số nâng cấp."""
        return self.data["stats"]

    def xp_to_next(self) -> int:
        """Trả về tổng XP cần có để đạt tới level tiếp theo."""
        return xp_for_next_level(self.level)

    # ──────────── XP / level ──────────────────────────────────────────────
    def add_xp(self, amount: int) -> int:
        """Thêm XP, tự động lên level. Trả về số lần lên level."""
        self.data["xp"] += amount
        leveled = 0
        while self.data["xp"] >= self.xp_to_next():
            self.data["xp"] -= self.xp_to_next()
            self.data["level"] += 1
            leveled += 1
        return leveled

    def add_coins(self, amount: int):
        """Thêm một lượng coins cho người chơi."""
        self.data["coins"] += amount

    # ──────────── upgrade helpers ─────────────────────────────────────────
    def get_stat_level(self, key: str) -> int:
        """Lấy cấp độ hiện tại của một chỉ số cụ thể."""
        return self.data["stats"].get(key, 0)

    def get_stat_bonus(self, key: str) -> float:
        """Trả về tỷ lệ bonus (0.0 – stat_cap) cho một stat."""
        udef = _DEFS_BY_KEY.get(key)
        if udef is None:
            return 0.0
        lvl = self.get_stat_level(key)
        return min(lvl * udef["bonus_per_level"], udef["stat_cap"])

    def get_max_level(self, key: str) -> int:
        """Lấy cấp độ tối đa có thể đạt được của một chỉ số."""
        udef = _DEFS_BY_KEY.get(key)
        return udef["max_level"] if udef else 0

    def get_upgrade_cost(self, key: str):
        """Trả về chi phí nâng cấp tiếp theo, hoặc None nếu đã max."""
        udef = _DEFS_BY_KEY.get(key)
        if udef is None:
            return None
        lvl = self.get_stat_level(key)
        if lvl >= udef["max_level"]:
            return None
        return udef["costs"][lvl]

    def can_upgrade(self, key: str) -> bool:
        """Kiểm tra xem người chơi có đủ coins để nâng cấp chỉ số này không."""
        cost = self.get_upgrade_cost(key)
        return cost is not None and self.coins >= cost

    def purchase_upgrade(self, key: str) -> bool:
        if not self.can_upgrade(key):
            return False
        cost = self.get_upgrade_cost(key)
        self.data["coins"] -= cost
        self.data["stats"][key] = self.data["stats"].get(key, 0) + 1
        self.save()
        return True

    # ──────────── áp dụng vào player ─────────────────────────────────────
    def apply_to_player(self, player, config):
        """Áp stats bonus lên player object ngay khi bắt đầu trận."""
        player.max_speed = config.PLAYER_MAX_SPEED * (1 + self.get_stat_bonus("speed"))
        player.acceleration = config.PLAYER_ACCELERATION * (1 + self.get_stat_bonus("acceleration"))
        player.mass = config.PLAYER_MASS * (1 + self.get_stat_bonus("mass"))
        # kick_power lưu trên player để dùng trong kick()
        player.kick_power_bonus = self.get_stat_bonus("kick_power")
        # skill bonuses
        player.cooldown_reduction_bonus = self.get_stat_bonus("cooldown_reduction")
        player.skill_duration_bonus = self.get_stat_bonus("skill_duration")
        player.skill_effectiveness_bonus = self.get_stat_bonus("skill_effectiveness")

    # ──────────── reward sau trận ─────────────────────────────────────────
    def award_match(self, result: str) -> dict:
        """
        result: 'win' | 'loss' | 'draw'
        Trả về dict {"xp": ..., "coins": ..., "leveled_up": bool}
        """
        rewards = {
            "win":  {"xp": 100, "coins": 50},
            "loss": {"xp":  30, "coins": 15},
            "draw": {"xp":  60, "coins": 30},
        }.get(result, {"xp": 0, "coins": 0})
        xp_gained = rewards["xp"]
        coins_gained = rewards["coins"]
        leveled = self.add_xp(xp_gained)
        self.add_coins(coins_gained)
        self.save()
        return {"xp": xp_gained, "coins": coins_gained, "leveled_up": leveled > 0}
