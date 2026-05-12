from collections import deque
class ReplayBuffer:
    """Bộ nhớ vòng lưu các frame gần nhất để phát lại sau bàn thắng."""

    def __init__(self):
        """Tạo replay buffer rỗng với số frame tối đa cố định."""
        self.max_frames = 300 * 2
        self.frames = deque()

    def save(self, ball, p1, p2, effects=None):
        """Lưu một frame gồm trạng thái bóng, cầu thủ và hiệu ứng nếu có."""
        self.frames.append({
            "ball_pos": ball.pos.copy(),
            "ball_vel": ball.vel.copy(),
            "p1_pos": p1.pos.copy(),
            "p1_vel": p1.vel.copy(),
            "p2_pos": p2.pos.copy(),
            "p2_vel": p2.vel.copy(),
            "effects": effects.get_state() if effects is not None else None,
        })
        if len(self.frames) > self.max_frames:
            self.frames.popleft()

    def get_frames(self):
        """Trả về bản sao dạng list của các frame đã lưu."""
        return list(self.frames)

    def clear(self):
        """Xóa toàn bộ frame đang lưu trong replay buffer."""
        self.frames.clear()


replay_buffer = ReplayBuffer()
