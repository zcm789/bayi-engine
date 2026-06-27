import json
import random
from typing import List, Dict, Tuple, Optional, Any

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class BaYiEngine:
    """八易全息引擎 (64卦 · 智能变爻)"""

    TRIGRAM_NAMES = {
        0b000: "坤☷", 0b001: "震☳", 0b010: "坎☵", 0b011: "兑☱",
        0b100: "艮☶", 0b101: "离☲", 0b110: "巽☴", 0b111: "乾☰"
    }
    BA_YI_CYCLE = [0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111]
    BA_YI_NAMES = ["归藏(坤)", "震易", "坎易", "兑易", "连山(艮)", "离易", "巽易", "周易(乾)"]
    PURE_64_NAMES_MAP = {}

    def __init__(self, seed: int = 42, internal_steps: int = 3, mode: str = "deterministic"):
        self.seed = seed
        self.internal_steps = internal_steps
        self.mode = mode
        random.seed(self.seed)
        self._pure_64_starts = [self._expand_to_64(t) for t in self.BA_YI_CYCLE]
        # 初始化 PURE_64_NAMES_MAP
        for _t in self.BA_YI_CYCLE:
            _key = (_t << 3) | _t
            _val = f"{self.TRIGRAM_NAMES[_t]}为{self.TRIGRAM_NAMES[_t]}"
            self.PURE_64_NAMES_MAP[_key] = _val

    @staticmethod
    def _to_bin6(n: int) -> str:
        return f"{n:06b}"[::-1]

    @staticmethod
    def _expand_to_64(trigram: int) -> int:
        return (trigram << 3) | trigram

    @staticmethod
    def _hamming_distance(a: int, b: int) -> int:
        return bin(a ^ b).count("1")

    @staticmethod
    def _get_diff_bits(a: int, b: int) -> List[int]:
        return [i for i in range(6) if ((a >> i) & 1) != ((b >> i) & 1)]

    @staticmethod
    def _flip_bit(n: int, pos: int) -> int:
        return n ^ (1 << pos)

    @staticmethod
    def opposite(h: int) -> int:
        return h ^ 0b111111

    @staticmethod
    def reverse(h: int) -> int:
        res = 0
        for i in range(6):
            if h & (1 << i):
                res |= (1 << (5 - i))
        return res

    @staticmethod
    def mutual(h: int) -> int:
        lower = (h >> 1) & 0b111
        upper = (h >> 2) & 0b111
        return (upper << 3) | lower

    def intelligent_transition(self, start: int, target: int) -> List[int]:
        if start == target:
            return [start]
        diff_bits = self._get_diff_bits(start, target)
        diff_bits.sort()
        path = [start]
        current = start
        for bit in diff_bits:
            current = self._flip_bit(current, bit)
            path.append(current)
        return path

    def _simulate_phase(self, start_hex: int) -> List[int]:
        path = [start_hex]
        current = start_hex
        visited: set[int] = {start_hex}
        for _ in range(self.internal_steps):
            found_new = False
            for i in range(6):
                candidate = self._flip_bit(current, i)
                if candidate not in visited:
                    current = candidate
                    visited.add(current)
                    path.append(current)
                    found_new = True
                    break
            if found_new:
                continue
            candidate = self.opposite(current)
            if candidate not in visited:
                current = candidate
                visited.add(current)
                path.append(current)
                continue
            candidate = self.reverse(current)
            if candidate not in visited:
                current = candidate
                visited.add(current)
                path.append(current)
                continue
            candidate = self.mutual(current)
            if candidate not in visited:
                current = candidate
                visited.add(current)
                path.append(current)
                continue
            candidate = self._flip_bit(current, random.randint(0, 5))
            current = candidate
            visited.add(current)
            path.append(current)
        return path

    def run_cycle(
        self,
        start_index: int = 0,
        direction: str = "forward",
        internal_steps: Optional[int] = None
    ) -> Tuple[List[int], Dict[str, List[int]]]:
        steps = internal_steps if internal_steps is not None else self.internal_steps
        cycle_len = len(self._pure_64_starts)
        step = 1 if direction == "forward" else -1
        full_path: List[int] = []
        transition_log: Dict[str, List[int]] = {}
        idx = start_index
        for phase in range(cycle_len):
            start_hex = self._pure_64_starts[idx]
            next_idx = (idx + step) % cycle_len
            target_hex = self._pure_64_starts[next_idx]
            internal_path = self._simulate_phase(start_hex)
            if phase == 0:
                full_path.extend(internal_path)
            else:
                full_path.extend(internal_path[1:])
            last_state = internal_path[-1]
            trans_path = self.intelligent_transition(last_state, target_hex)
            from_name = self.PURE_64_NAMES_MAP.get(start_hex, f"{start_hex:06b}")
            to_name = self.PURE_64_NAMES_MAP.get(target_hex, f"{target_hex:06b}")
            key = f"{from_name} → {to_name}"
            transition_log[key] = trans_path
            full_path.extend(trans_path[1:])
            idx = next_idx
        return full_path, transition_log

    def get_path_between(self, start_hex: int, target_hex: int) -> List[int]:
        return self.intelligent_transition(start_hex, target_hex)

    def save_path(self, path: List[int], filepath: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        data = {
            "version": "1.0",
            "path": path,
            "length": len(path),
            "start": path[0] if path else None,
            "end": path[-1] if path else None,
            "metadata": metadata or {}
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_path(filepath: str) -> Tuple[List[int], Dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("path", []), data.get("metadata", {})

    def plot_path(self, path: List[int], title: str = "八易路径轨迹", figsize: tuple = (14, 6)):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("请安装 matplotlib: pip install matplotlib")
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(range(len(path)), path, marker='o', markersize=4, linewidth=1.5, color='navy', alpha=0.7)
        pure_set = set(self._pure_64_starts)
        for i, val in enumerate(path):
            if val in pure_set:
                ax.scatter(i, val, color='red', s=40, zorder=5, edgecolors='black')
                name = self.PURE_64_NAMES_MAP.get(val, "")
                if name:
                    ax.annotate(name, (i, val), xytext=(5, 5), textcoords='offset points',
                                fontsize=8, alpha=0.8, rotation=45)
        ax.scatter(0, path[0], color='green', s=100, label=f'起点: {path[0]}', zorder=6)
        ax.scatter(len(path)-1, path[-1], color='purple', s=100, label=f'终点: {path[-1]}', zorder=6)
        ax.set_xlabel("推演步数 (时间)")
        ax.set_ylabel("卦值 (0-63)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        return fig, ax

    def plot_hexagram_map(self, path: List[int], title: str = "六十四卦访问热度图 (8x8)", figsize: tuple = (10, 8)):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("请安装 matplotlib: pip install matplotlib")
        matrix = [[0] * 8 for _ in range(8)]
        for h in path:
            lower = h & 0b111
            upper = (h >> 3) & 0b111
            matrix[lower][upper] += 1
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', origin='lower')
        for i in range(8):
            for j in range(8):
                val = matrix[i][j]
                if val > 0:
                    ax.text(j, i, str(val), ha='center', va='center',
                            color='black' if val < max(1, max(max(row) for row in matrix)) / 2 else 'white')
        trigram_labels = ["坤", "震", "坎", "兑", "艮", "离", "巽", "乾"]
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(trigram_labels)
        ax.set_yticklabels(trigram_labels)
        ax.set_xlabel("上卦 (天)")
        ax.set_ylabel("下卦 (地)")
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label='访问次数')
        fig.tight_layout()
        return fig, ax

    def plot_cycle_summary(self, path: List[int], transition_log: Dict, figsize: tuple = (15, 10)):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("请安装 matplotlib: pip install matplotlib")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        ax1.plot(range(len(path)), path, marker='.', markersize=2, linewidth=1, color='steelblue', alpha=0.6)
        pure_set = set(self._pure_64_starts)
        for i, val in enumerate(path):
            if val in pure_set:
                ax1.scatter(i, val, color='red', s=30, zorder=5)
        ax1.set_xlabel("步数")
        ax1.set_ylabel("卦值 (0-63)")
        ax1.set_title("路径时序轨迹")
        ax1.grid(True, alpha=0.2)
        matrix = [[0] * 8 for _ in range(8)]
        for h in path:
            lower = h & 0b111
            upper = (h >> 3) & 0b111
            matrix[lower][upper] += 1
        im = ax2.imshow(matrix, cmap='viridis', aspect='auto', origin='lower')
        trigram_labels = ["坤", "震", "坎", "兑", "艮", "离", "巽", "乾"]
        ax2.set_xticks(range(8))
        ax2.set_yticks(range(8))
        ax2.set_xticklabels(trigram_labels)
        ax2.set_yticklabels(trigram_labels)
        ax2.set_xlabel("上卦")
        ax2.set_ylabel("下卦")
        ax2.set_title("卦象访问热度")
        plt.colorbar(im, ax=ax2, label='次数')
        fig.suptitle("八易循环综合视图", fontsize=14)
        fig.tight_layout()
        return fig, (ax1, ax2)

    def map_dataframe(self, df: Any, column: str, min_val: Optional[float] = None,
                      max_val: Optional[float] = None, new_column: str = "hexagram",
                      drop_original: bool = False) -> Any:
        if not PANDAS_AVAILABLE:
            raise ImportError("请安装 pandas: pip install pandas")
        result_df = df.copy()
        series = result_df[column]
        if min_val is None:
            min_val = float(series.min())
        if max_val is None:
            max_val = float(series.max())
        if max_val == min_val:
            result_df[new_column] = 0
        else:
            def _map_val(v):
                v_clamped = max(min_val, min(max_val, v))
                normalized = (v_clamped - min_val) / (max_val - min_val)
                return int(round(normalized * 63))
            result_df[new_column] = series.apply(_map_val)
        if drop_original:
            result_df.drop(columns=[column], inplace=True)
        return result_df

    def map_dataframe_with_series(self, df: Any, column: str, min_val: Optional[float] = None,
                                   max_val: Optional[float] = None, new_column: str = "hexagram") -> Any:
        if not PANDAS_AVAILABLE:
            raise ImportError("请安装 pandas: pip install pandas")
        result_df = self.map_dataframe(df, column, min_val, max_val, new_column)
        result_df[f"{new_column}_bin"] = result_df[new_column].apply(self._to_bin6)
        result_df[f"{new_column}_name"] = result_df[new_column].apply(
            lambda h: self.PURE_64_NAMES_MAP.get(h, f"卦{h}")
        )
        return result_df

    def get_hexagram_name(self, h: int) -> str:
        return self.PURE_64_NAMES_MAP.get(h, f"未知({self._to_bin6(h)})")

    def explain_transition(self, start: int, target: int) -> Dict:
        path = self.intelligent_transition(start, target)
        diff_bits = self._get_diff_bits(start, target)
        return {
            "start": start,
            "target": target,
            "path": path,
            "path_bin": [self._to_bin6(x) for x in path],
            "hamming_distance": len(diff_bits),
            "changed_bits": diff_bits,
            "steps": len(path) - 1
        }

    def verify_symmetry(self, verbose: bool = True) -> bool:
        all_passed = True
        for i in range(7):
            start_t = self.BA_YI_CYCLE[i]
            target_t = self.BA_YI_CYCLE[i + 1]
            start_64 = self._expand_to_64(start_t)
            target_64 = self._expand_to_64(target_t)
            f_path = self.intelligent_transition(start_64, target_64)
            b_path = self.intelligent_transition(target_64, start_64)
            if f_path != b_path[::-1]:
                all_passed = False
                if verbose:
                    print(f"❌ 对称性失败: {self._to_bin6(start_64)} ↔ {self._to_bin6(target_64)}")
        start = self._expand_to_64(0b011)
        target = self._expand_to_64(0b100)
        if self.intelligent_transition(start, target) != self.intelligent_transition(target, start)[::-1]:
            all_passed = False
            if verbose:
                print("❌ 兑↔艮 全翻转测试失败")
        if verbose and all_passed:
            print("✅ 时间反演对称性验证通过")
        return all_passed
