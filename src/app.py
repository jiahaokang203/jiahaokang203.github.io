from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from .action_engine import ActionEngine
from .config_store import ConfigStore
from .models import GameConfig
from .wechat_listener import Command, WeChatListener


CARD_COLORS = [
    "#A6E22E",
    "#3AA0FF",
    "#FFCC33",
    "#F78C6C",
    "#C792EA",
    "#7FDBCA",
]


class LauncherApp:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.store = ConfigStore(base_dir)
        self.games = self.store.load_games()
        self.game_by_id = {g.id: g for g in self.games}

        self.root = tk.Tk()
        self.root.title("游戏远程启动器")
        self.root.geometry("1200x760")
        self.root.minsize(1000, 680)
        self.root.configure(bg="#0D1321")

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.action_engine = ActionEngine(self.log)
        self.listener: WeChatListener | None = None
        self.current_game_id = self.games[0].id if self.games else ""

        self.main_frame = tk.Frame(self.root, bg="#0D1321")
        self.detail_frame = tk.Frame(self.root, bg="#101A2F")

        self.chat_entry: tk.Entry | None = None
        self.listen_btn: tk.Button | None = None
        self.log_text: tk.Text | None = None

        self.detail_title: tk.Label | None = None
        self.exe_var = tk.StringVar(value="")
        self.config_var = tk.StringVar(value="")
        self.actions_count_var = tk.StringVar(value="动作数量: 0")

        self._build_main_ui()
        self._build_detail_ui()
        self.show_main()
        self._tick_log()

    def run(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_main_ui(self) -> None:
        self.main_frame.pack(fill="both", expand=True)

        top_bar = tk.Frame(self.main_frame, bg="#0D1321")
        top_bar.pack(fill="x", padx=20, pady=(14, 10))

        tk.Label(
            top_bar,
            text="游戏远程启动器",
            font=("Microsoft YaHei", 24, "bold"),
            fg="#F5F7FF",
            bg="#0D1321",
        ).pack(side="left")

        wx_box = tk.Frame(top_bar, bg="#0D1321")
        wx_box.pack(side="right")

        tk.Label(
            wx_box,
            text="监听会话:",
            font=("Microsoft YaHei", 10),
            fg="#D4DCEE",
            bg="#0D1321",
        ).pack(side="left", padx=(0, 6))

        self.chat_entry = tk.Entry(
            wx_box,
            font=("Microsoft YaHei", 10),
            width=16,
            relief="flat",
        )
        self.chat_entry.insert(0, "文件传输助手")
        self.chat_entry.pack(side="left", padx=(0, 8))

        self.listen_btn = tk.Button(
            wx_box,
            text="启动微信监听",
            font=("Microsoft YaHei", 10, "bold"),
            command=self.toggle_listener,
            bg="#2D7EF7",
            fg="#FFFFFF",
            activebackground="#1C68D8",
            relief="flat",
            padx=10,
        )
        self.listen_btn.pack(side="left")

        banner = tk.Canvas(self.main_frame, height=390, bg="#131E37", highlightthickness=0)
        banner.pack(fill="x", padx=20)
        self._draw_banner(banner)

        tk.Label(
            banner,
            text="选择游戏",
            font=("Microsoft YaHei", 26, "bold"),
            fg="#FFFFFF",
            bg="#131E37",
        ).place(x=32, y=24)
        tk.Label(
            banner,
            text="点击下方卡片进入游戏配置页",
            font=("Microsoft YaHei", 12),
            fg="#C8D4EC",
            bg="#131E37",
        ).place(x=34, y=72)

        cards_host = tk.Frame(banner, bg="#131E37")
        cards_host.place(x=24, y=250, relwidth=0.95, height=120)

        left_btn = tk.Button(
            cards_host,
            text="<",
            font=("Consolas", 18, "bold"),
            width=2,
            command=lambda: self.cards_canvas.xview_scroll(-2, "units"),
            bg="#1B2847",
            fg="#DCE6FF",
            relief="flat",
        )
        left_btn.pack(side="left", padx=(0, 6))

        self.cards_canvas = tk.Canvas(
            cards_host, bg="#131E37", height=112, highlightthickness=0
        )
        self.cards_canvas.pack(side="left", fill="x", expand=True)

        right_btn = tk.Button(
            cards_host,
            text=">",
            font=("Consolas", 18, "bold"),
            width=2,
            command=lambda: self.cards_canvas.xview_scroll(2, "units"),
            bg="#1B2847",
            fg="#DCE6FF",
            relief="flat",
        )
        right_btn.pack(side="left", padx=(6, 0))

        self.cards_inner = tk.Frame(self.cards_canvas, bg="#131E37")
        self.cards_canvas.create_window((0, 0), window=self.cards_inner, anchor="nw")

        self.cards_inner.bind(
            "<Configure>",
            lambda e: self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all")),
        )
        self.cards_canvas.bind(
            "<MouseWheel>",
            lambda e: self.cards_canvas.xview_scroll(int(-e.delta / 120), "units"),
        )

        for idx, game in enumerate(self.games):
            self._create_game_card(self.cards_inner, game, idx)

        log_box = tk.Frame(self.main_frame, bg="#0D1321")
        log_box.pack(fill="both", expand=True, padx=20, pady=(12, 16))

        tk.Label(
            log_box,
            text="运行日志",
            font=("Microsoft YaHei", 12, "bold"),
            fg="#E4EBFF",
            bg="#0D1321",
        ).pack(anchor="w", pady=(0, 6))

        self.log_text = tk.Text(
            log_box,
            bg="#0B1221",
            fg="#B9C8EA",
            font=("Consolas", 10),
            height=9,
            relief="flat",
        )
        self.log_text.pack(fill="both", expand=True)

    def _draw_banner(self, canvas: tk.Canvas) -> None:
        width = 1200
        height = 390
        for i in range(height):
            color = self._mix_color("#1B2D52", "#2B3E70", i / height)
            canvas.create_line(0, i, width, i, fill=color)

        canvas.create_oval(760, -80, 1220, 360, fill="#3E5A99", outline="")
        canvas.create_oval(900, 20, 1320, 420, fill="#2C477F", outline="")
        canvas.create_oval(620, 70, 980, 430, fill="#455E96", outline="")

    @staticmethod
    def _mix_color(c1: str, c2: str, t: float) -> str:
        def parse(c: str) -> tuple[int, int, int]:
            return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)

        r1, g1, b1 = parse(c1)
        r2, g2, b2 = parse(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _create_game_card(self, parent: tk.Frame, game: GameConfig, idx: int) -> None:
        card = tk.Frame(
            parent,
            bg=CARD_COLORS[idx % len(CARD_COLORS)],
            width=220,
            height=96,
            cursor="hand2",
            highlightthickness=2,
            highlightbackground="#22314D",
            highlightcolor="#D5E2FF",
        )
        card.pack(side="left", padx=8, pady=8)
        card.pack_propagate(False)

        status = "已定位" if game.has_location else "未定位"
        label1 = tk.Label(
            card,
            text=game.name,
            font=("Microsoft YaHei", 13, "bold"),
            fg="#0E1320",
            bg=card["bg"],
        )
        label1.pack(anchor="w", padx=10, pady=(14, 2))

        label2 = tk.Label(
            card,
            text=f"状态: {status}",
            font=("Microsoft YaHei", 10),
            fg="#1B2740",
            bg=card["bg"],
        )
        label2.pack(anchor="w", padx=10)

        for widget in (card, label1, label2):
            widget.bind("<Button-1>", lambda _e, gid=game.id: self.enter_game(gid))

    def _build_detail_ui(self) -> None:
        bar = tk.Frame(self.detail_frame, bg="#101A2F")
        bar.pack(fill="x", padx=20, pady=(14, 8))

        tk.Button(
            bar,
            text="返回主界面",
            font=("Microsoft YaHei", 10, "bold"),
            command=self.show_main,
            bg="#2A3B63",
            fg="#FFFFFF",
            relief="flat",
            padx=10,
        ).pack(side="left")

        self.detail_title = tk.Label(
            bar,
            text="",
            font=("Microsoft YaHei", 22, "bold"),
            fg="#F5F7FF",
            bg="#101A2F",
        )
        self.detail_title.pack(side="left", padx=14)

        body = tk.Frame(self.detail_frame, bg="#101A2F")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        panel = tk.Frame(body, bg="#162341", padx=20, pady=16)
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="1) 定位游戏（必填）",
            font=("Microsoft YaHei", 13, "bold"),
            fg="#ECF2FF",
            bg="#162341",
        ).pack(anchor="w")

        row1 = tk.Frame(panel, bg="#162341")
        row1.pack(fill="x", pady=(8, 16))

        tk.Entry(
            row1,
            textvariable=self.exe_var,
            font=("Consolas", 10),
            state="readonly",
            readonlybackground="#0F1A33",
            fg="#BDD0F8",
            relief="flat",
        ).pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(
            row1,
            text="选择游戏exe",
            command=self.pick_exe,
            font=("Microsoft YaHei", 10, "bold"),
            bg="#2D7EF7",
            fg="#FFFFFF",
            relief="flat",
            padx=10,
        ).pack(side="left", padx=(10, 0))

        tk.Label(
            panel,
            text="2) 导入配置（可选）",
            font=("Microsoft YaHei", 13, "bold"),
            fg="#ECF2FF",
            bg="#162341",
        ).pack(anchor="w")

        row2 = tk.Frame(panel, bg="#162341")
        row2.pack(fill="x", pady=(8, 8))

        tk.Entry(
            row2,
            textvariable=self.config_var,
            font=("Consolas", 10),
            state="readonly",
            readonlybackground="#0F1A33",
            fg="#BDD0F8",
            relief="flat",
        ).pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(
            row2,
            text="导入JSON配置",
            command=self.import_config,
            font=("Microsoft YaHei", 10, "bold"),
            bg="#22A679",
            fg="#FFFFFF",
            relief="flat",
            padx=10,
        ).pack(side="left", padx=(10, 0))

        tk.Label(
            panel,
            textvariable=self.actions_count_var,
            font=("Microsoft YaHei", 10),
            fg="#AFC2EB",
            bg="#162341",
        ).pack(anchor="w", pady=(2, 16))

        ops = tk.Frame(panel, bg="#162341")
        ops.pack(fill="x", pady=(10, 6))

        tk.Button(
            ops,
            text="保存当前配置",
            command=self.save_games,
            font=("Microsoft YaHei", 10, "bold"),
            bg="#355A9E",
            fg="#FFFFFF",
            relief="flat",
            padx=10,
        ).pack(side="left")

        tk.Button(
            ops,
            text="本地测试启动",
            command=self.local_launch_current,
            font=("Microsoft YaHei", 10, "bold"),
            bg="#F28B30",
            fg="#FFFFFF",
            relief="flat",
            padx=10,
        ).pack(side="left", padx=(10, 0))

        tips = (
            "微信指令格式: 启动游戏名\n"
            "示例: 启动原神\n"
            "动作支持: wait / key / hotkey / click / image_click"
        )
        tk.Label(
            panel,
            text=tips,
            justify="left",
            font=("Microsoft YaHei", 10),
            fg="#9AB0DE",
            bg="#162341",
        ).pack(anchor="w", pady=(18, 0))

    def show_main(self) -> None:
        self.detail_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def enter_game(self, game_id: str) -> None:
        self.current_game_id = game_id
        game = self.game_by_id[game_id]

        if self.detail_title:
            self.detail_title.configure(text=game.name)
        self.exe_var.set(game.exe_path)
        self.config_var.set(game.config_path)
        self.actions_count_var.set(f"动作数量: {len(game.actions)}")

        self.main_frame.pack_forget()
        self.detail_frame.pack(fill="both", expand=True)

    def pick_exe(self) -> None:
        game = self.current_game
        if game is None:
            return

        file_path = filedialog.askopenfilename(
            title=f"选择 {game.name} 的可执行文件",
            filetypes=[("Executable", "*.exe")],
        )
        if not file_path:
            return

        game.exe_path = file_path
        self.exe_var.set(file_path)
        self.log(f"已定位游戏 {game.name}: {file_path}")

    def import_config(self) -> None:
        game = self.current_game
        if game is None:
            return

        file_path = filedialog.askopenfilename(
            title="选择动作配置(JSON)",
            filetypes=[("JSON", "*.json")],
        )
        if not file_path:
            return

        try:
            self.store.import_action_config(game, Path(file_path))
            self.config_var.set(file_path)
            self.actions_count_var.set(f"动作数量: {len(game.actions)}")
            self.log(f"已导入配置: {file_path}")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def save_games(self) -> None:
        self.store.save_games(self.games)
        self.log("配置已保存到 config/games.json")
        messagebox.showinfo("保存成功", "配置已保存")

    def local_launch_current(self) -> None:
        game = self.current_game
        if game is None:
            return
        self.launch_game(game.name)

    def toggle_listener(self) -> None:
        if self.listener is not None:
            self.listener.stop()
            self.listener = None
            if self.listen_btn:
                self.listen_btn.configure(text="启动微信监听", bg="#2D7EF7")
            self.log("已停止微信监听")
            return

        target_chat = self.chat_entry.get().strip() if self.chat_entry else "文件传输助手"
        if not target_chat:
            messagebox.showerror("错误", "请输入要监听的微信会话名称")
            return

        self.listener = WeChatListener(
            target_chat=target_chat,
            on_command=self.on_wechat_command,
            log=self.log,
        )
        self.listener.start()

        if self.listen_btn:
            self.listen_btn.configure(text="停止微信监听", bg="#D64242")
        self.log("微信监听线程已启动")

    def on_wechat_command(self, cmd: Command) -> None:
        self.root.after(0, lambda: self.launch_game(cmd.game_name))

    def launch_game(self, game_name: str) -> None:
        game = self._find_game_by_name(game_name)
        if game is None:
            self.log(f"未匹配到游戏: {game_name}")
            return

        if not game.has_location:
            self.log(f"游戏 {game.name} 尚未定位，无法启动")
            return

        self.log(f"准备启动: {game.name}")
        thread = threading.Thread(target=self._launch_worker, args=(game,), daemon=True)
        thread.start()

    def _launch_worker(self, game: GameConfig) -> None:
        try:
            self.action_engine.launch(game)
        except Exception as exc:
            self.log(f"启动失败({game.name}): {exc}")

    def _find_game_by_name(self, raw_name: str) -> GameConfig | None:
        name = raw_name.replace(" ", "")
        for game in self.games:
            n = game.name.replace(" ", "")
            if name == n or name in n or n in name:
                return game
        return None

    @property
    def current_game(self) -> GameConfig | None:
        return self.game_by_id.get(self.current_game_id)

    def log(self, message: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{ts}] {message}")

    def _tick_log(self) -> None:
        if self.log_text:
            while not self.log_queue.empty():
                line = self.log_queue.get_nowait()
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")

        self.root.after(200, self._tick_log)

    def _on_close(self) -> None:
        if self.listener is not None:
            self.listener.stop()
        self.root.destroy()
