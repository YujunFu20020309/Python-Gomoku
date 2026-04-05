import pygame
import sys
import random
import json
import os
import time

# --- 基礎設定 ---
BOARD_SIZE = 15
GRID_SIZE = 40
MARGIN = 40
SIDE_PANEL_WIDTH = 250
WINDOW_WIDTH = BOARD_SIZE * GRID_SIZE + MARGIN * 2 - GRID_SIZE + SIDE_PANEL_WIDTH
WINDOW_HEIGHT = BOARD_SIZE * GRID_SIZE + MARGIN * 2 - GRID_SIZE

# 顏色定義
C_BG = (250, 240, 245)      
C_BOARD = (222, 184, 135)   
C_BOARD_BORDER = (139, 69, 19) 
C_ACCENT = (255, 140, 170)  
C_TEXT = (60, 45, 45)       
C_WHITE = (255, 255, 255)
C_BLACK = (20, 20, 20)

STATE_LOGIN = "LOGIN"
STATE_MENU = "MENU"
STATE_GAME = "GAME"

# --- 確保紀錄檔存在本地 ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATS_FILE = os.path.join(BASE_DIR, "user_profiles.json")

def load_data():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"users": {}}

def save_data(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 遊戲主程式 ---
class AnimeGomoku:
    def __init__(self):
        pygame.init()
        # 開啟抗鋸齒支援，讓圓形更平滑
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.display.set_caption("專業五子棋")
        
        # 開啟系統文字輸入 (支援中文輸入法)
        pygame.key.start_text_input()
        
        # 字體設定
        font_path = "Microsoft JhengHei"
        try:
            self.font_s = pygame.font.SysFont(font_path, 18)
            self.font_m = pygame.font.SysFont(font_path, 24, bold=True)
            self.font_l = pygame.font.SysFont(font_path, 40, bold=True)
        except:
            self.font_s = pygame.font.Font(None, 18)
            self.font_m = pygame.font.Font(None, 24)
            self.font_l = pygame.font.Font(None, 40)
        
        # 載入新的高級介面圖片
        self.gomoku_display_img = None
        display_img_path = os.path.join(BASE_DIR, "e7082167.jpg")
        if os.path.exists(display_img_path):
            try:
                self.gomoku_display_img = pygame.image.load(display_img_path)
                self.gomoku_display_img = pygame.transform.smoothscale(self.gomoku_display_img, (200, 200))
            except:
                pass

        self.data = load_data()
        self.current_user = ""
        self.input_text = ""
        self.state = STATE_LOGIN
        
        self.mode = "AI"
        self.difficulty = 3 # 1:簡單, 2:普通, 3:困難
        self.turn_limit = 30
        
        # 預先建立一個空的按鈕防止 Crash
        self.btn_back = pygame.Rect(0, 0, 0, 0) 
        self.reset_game_state()

    def reset_game_state(self):
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_turn = 1 # 1:黑, 2:白
        self.game_over = False
        self.winner = None
        self.turn_start_time = time.time()
        self.btn_back = pygame.Rect(0, 0, 0, 0) # 重置按鈕範圍

    def draw_text(self, text, font, color, x, y, center=False):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center: rect.center = (x, y)
        else: rect.topleft = (x, y)
        self.screen.blit(surf, rect)

    def draw_button(self, text, rect_coord, color, active=False):
        rect = pygame.Rect(rect_coord)
        border_color = C_ACCENT if active else C_TEXT
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, rect, 3 if active else 2, border_radius=10)
        self.draw_text(text, self.font_m, C_TEXT, rect.centerx, rect.centery, True)
        return rect

    def run(self):
        clock = pygame.time.Clock()
        while True:
            if self.state == STATE_LOGIN: self.scene_login()
            elif self.state == STATE_MENU: self.scene_menu()
            elif self.state == STATE_GAME: self.scene_game()
            pygame.display.flip()
            clock.tick(60)

    def scene_login(self):
        self.screen.fill(C_BG)
        self.draw_text("五子棋", self.font_l, C_TEXT, WINDOW_WIDTH//2, 150, True)
        self.draw_text("請輸入你的玩家代號：", self.font_m, C_TEXT, WINDOW_WIDTH//2, 230, True)
        
        input_box = pygame.Rect(WINDOW_WIDTH//2 - 150, 260, 300, 50)
        pygame.draw.rect(self.screen, C_WHITE, input_box, border_radius=8)
        pygame.draw.rect(self.screen, C_ACCENT, input_box, 2, border_radius=8)
        self.draw_text(self.input_text, self.font_m, C_BLACK, input_box.centerx, input_box.centery, True)
        
        self.draw_text("輸入完畢請按 Enter 鍵", self.font_s, (120, 100, 100), WINDOW_WIDTH//2, 330, True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            # 支援中文輸入的核心 (TEXTINPUT 事件)
            if event.type == pygame.TEXTINPUT:
                if len(self.input_text) < 12: self.input_text += event.text
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.input_text.strip():
                    self.current_user = self.input_text.strip()
                    if self.current_user not in self.data["users"]:
                        self.data["users"][self.current_user] = {"ai_w":0, "ai_l":0, "pvp_w":0, "pvp_l":0}
                        save_data(self.data)
                    # 離開登入畫面，關閉輸入法避免影響遊戲
                    pygame.key.stop_text_input()
                    self.state = STATE_MENU
                elif event.key == pygame.K_BACKSPACE: 
                    self.input_text = self.input_text[:-1]

    def scene_menu(self):
        self.screen.fill(C_BG)
        user_info = self.data["users"][self.current_user]
        self.draw_text(f"歡迎回來，{self.current_user}！", self.font_m, C_TEXT, 50, 50)
        
        self.draw_text(f"對戰 AI：{user_info['ai_w']} 勝 / {user_info['ai_l']} 敗", self.font_s, C_TEXT, 50, 85)
        self.draw_text(f"本地雙人：{user_info['pvp_w']} 勝 / {user_info['pvp_l']} 敗", self.font_s, C_TEXT, 50, 110)

        # 模式選擇
        self.draw_text("遊戲模式", self.font_m, C_ACCENT, WINDOW_WIDTH//2, 170, True)
        btn_ai = self.draw_button("對戰電腦 (AI)", (WINDOW_WIDTH//2-210, 200, 200, 50), C_WHITE, self.mode=="AI")
        btn_pvp = self.draw_button("本地雙人 (PVP)", (WINDOW_WIDTH//2+10, 200, 200, 50), C_WHITE, self.mode=="PVP")
        
        # 電腦難度選擇
        diff_btns = []
        if self.mode == "AI":
            self.draw_text("電腦難度", self.font_m, C_ACCENT, WINDOW_WIDTH//2, 280, True)
            btn_d1 = self.draw_button("簡單", (WINDOW_WIDTH//2-180, 310, 100, 40), C_WHITE, self.difficulty==1)
            btn_d2 = self.draw_button("普通", (WINDOW_WIDTH//2-50, 310, 100, 40), C_WHITE, self.difficulty==2)
            btn_d3 = self.draw_button("困難", (WINDOW_WIDTH//2+80, 310, 100, 40), C_WHITE, self.difficulty==3)
            diff_btns = [(btn_d1, 1), (btn_d2, 2), (btn_d3, 3)]

        btn_start = self.draw_button("進入對局", (WINDOW_WIDTH//2-100, 420, 200, 60), (255, 200, 215))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_ai.collidepoint(event.pos): self.mode = "AI"
                if btn_pvp.collidepoint(event.pos): self.mode = "PVP"
                for btn, lvl in diff_btns:
                    if btn.collidepoint(event.pos): self.difficulty = lvl
                if btn_start.collidepoint(event.pos):
                    self.reset_game_state()
                    self.state = STATE_GAME

    def scene_game(self):
        self.screen.fill(C_BG)
        self.draw_board()
        self.draw_side_panel()
        
        # 倒數計時判定 (如果遊戲還沒結束)
        if not self.game_over:
            elapsed = time.time() - self.turn_start_time
            if elapsed > self.turn_limit:
                self.game_over = True
                self.winner = 3 - self.current_turn
                self.update_stats()

        # AI 行動
        if not self.game_over and self.mode == "AI" and self.current_turn == 2:
            pygame.display.flip() 
            pygame.time.delay(300) 
            self.ai_move_main()

        # 事件處理
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_over:
                    # 遊戲結束時，只能點擊返回按鈕
                    if self.btn_back.collidepoint(event.pos): 
                        self.state = STATE_MENU
                else:
                    # 遊戲進行中，處理下棋
                    x, y = event.pos
                    if MARGIN-20 < x < WINDOW_WIDTH-SIDE_PANEL_WIDTH and MARGIN-20 < y < WINDOW_HEIGHT-MARGIN+20:
                        c = round((x - MARGIN) / GRID_SIZE)
                        r = round((y - MARGIN) / GRID_SIZE)
                        if 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and self.board[r][c] == 0:
                            self.make_move(r, c)

    def draw_board(self):
        # 1. 畫棋盤底座陰影
        board_w = (BOARD_SIZE-1)*GRID_SIZE+40
        shadow_rect = pygame.Rect(MARGIN-15, MARGIN-15, board_w, board_w)
        pygame.draw.rect(self.screen, (200, 180, 185), shadow_rect, border_radius=8)
        
        # 2. 畫木質棋盤與深色邊框
        board_rect = pygame.Rect(MARGIN-20, MARGIN-20, board_w, board_w)
        pygame.draw.rect(self.screen, C_BOARD, board_rect, border_radius=8)
        pygame.draw.rect(self.screen, C_BOARD_BORDER, board_rect, 4, border_radius=8)
        
        # 3. 畫格線
        for i in range(BOARD_SIZE):
            pygame.draw.line(self.screen, C_TEXT, (MARGIN, MARGIN+i*GRID_SIZE), (MARGIN+(BOARD_SIZE-1)*GRID_SIZE, MARGIN+i*GRID_SIZE))
            pygame.draw.line(self.screen, C_TEXT, (MARGIN+i*GRID_SIZE, MARGIN), (MARGIN+i*GRID_SIZE, MARGIN+(BOARD_SIZE-1)*GRID_SIZE))
            
        # 4. 畫 5 個星位 (國際標準)
        star_points = [(3,3), (11,3), (3,11), (11,11), (7,7)]
        for sr, sc in star_points:
            pygame.draw.circle(self.screen, C_TEXT, (MARGIN+sc*GRID_SIZE, MARGIN+sr*GRID_SIZE), 5)
            
        # 5. 畫具有立體感的棋子
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != 0:
                    x = MARGIN + c * GRID_SIZE
                    y = MARGIN + r * GRID_SIZE
                    
                    # 落子陰影
                    pygame.draw.circle(self.screen, (100, 80, 60), (x+3, y+3), 17)
                    
                    if self.board[r][c] == 1:
                        # 黑子：黑曜石高光效果
                        pygame.draw.circle(self.screen, C_BLACK, (x, y), 18)
                        pygame.draw.circle(self.screen, (80, 80, 80), (x-5, y-5), 8) 
                        pygame.draw.circle(self.screen, (130, 130, 130), (x-6, y-6), 4) 
                    elif self.board[r][c] == 2: 
                        # 白子：玉石內陰影效果
                        pygame.draw.circle(self.screen, (240, 240, 240), (x, y), 18)
                        pygame.draw.circle(self.screen, (200, 200, 200), (x, y), 18, 1) 
                        pygame.draw.circle(self.screen, C_WHITE, (x-4, y-4), 10) 

    def draw_side_panel(self):
        panel_x = WINDOW_WIDTH - SIDE_PANEL_WIDTH + 20
        # 畫新的高級圖片
        avatar_rect = pygame.Rect(panel_x, 40, 200, 200)
        pygame.draw.rect(self.screen, C_WHITE, avatar_rect.inflate(10, 10), border_radius=15)
        
        if self.gomoku_display_img:
            self.screen.blit(self.gomoku_display_img, avatar_rect)
        else:
            pygame.draw.rect(self.screen, (100, 100, 110), avatar_rect, border_radius=10)
            self.draw_text("GOMOKU PRO", self.font_m, C_WHITE, avatar_rect.centerx, avatar_rect.centery, True)
        
        diff_text = ["簡單", "普通", "困難"][self.difficulty-1] if self.mode == "AI" else ""
        title = f"電腦 ({diff_text})" if self.mode == "AI" else "對手：玩家(白)"
        self.draw_text(title, self.font_m, C_TEXT, panel_x, 270)
        
        elapsed = time.time() - self.turn_start_time
        remaining = max(0, self.turn_limit - int(elapsed))
        color = C_ACCENT if remaining > 10 else (220, 50, 50)
        
        pygame.draw.arc(self.screen, (220, 220, 220), (panel_x+50, 320, 100, 100), 0, 6.28, 8) 
        pygame.draw.arc(self.screen, color, (panel_x+50, 320, 100, 100), 0, 6.28 * (remaining/30), 8) 
        self.draw_text(f"{remaining}s", self.font_l, color, panel_x+100, 370, True)
        
        turn_txt = f"輪到：{self.current_user}(黑)" if self.current_turn == 1 else f"輪到：{title}"
        self.draw_text(turn_txt, self.font_s, C_TEXT, panel_x, 440)

        # 遊戲結束處理
        if self.game_over:
            win_msg = "勝利！" if self.winner == 1 else "落敗！"
            color_win = (50, 180, 50) if self.winner == 1 else (220, 50, 50)
            self.draw_text(f"遊戲結束：{win_msg}", self.font_m, color_win, panel_x, 470)
            # 將 btn_back 的座標確實賦值，避免點擊 Crash
            self.btn_back = self.draw_button("返回主選單", (panel_x, 520, 180, 45), C_WHITE)

    # =========================================================
    # --- 關鍵修復區：修正了 self.board 傳遞導致閃退的問題 ---
    # =========================================================
    def make_move(self, r, c):
        self.board[r][c] = self.current_turn
        # 這裡正確加入了 self.board 給 check_win 判斷
        if self.check_win(self.board, r, c, self.current_turn):
            self.game_over = True
            self.winner = self.current_turn
            self.update_stats()
        else:
            self.current_turn = 3 - self.current_turn
            self.turn_start_time = time.time()

    def update_stats(self):
        u = self.data["users"][self.current_user]
        if self.mode == "AI":
            if self.winner == 1: u["ai_w"] += 1
            else: u["ai_l"] += 1
        else:
            if self.winner == 1: u["pvp_w"] += 1
            else: u["pvp_l"] += 1
        save_data(self.data)

    def check_win(self, board, r, c, s):
        for dr, dc in [(1,0), (0,1), (1,1), (1,-1)]:
            count = 1
            for i in range(1, 5):
                nr, nc = r+dr*i, c+dc*i
                if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc] == s: count += 1
                else: break
            for i in range(1, 5):
                nr, nc = r-dr*i, c-dc*i
                if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc] == s: count += 1
                else: break
            if count >= 5: return True
        return False

    # =========================================================
    # --- 終極大師大腦：完美的攻守平衡與陣型預判 ---
    # =========================================================

    def ai_move_main(self):
        empty_spots = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c] == 0]
        if not empty_spots: return

        stones_count = sum(row.count(1) + row.count(2) for row in self.board)
        if stones_count == 0:
            self.make_move(BOARD_SIZE//2, BOARD_SIZE//2)
            return

        if self.difficulty == 1:
            # 簡單模式：隨便找個有鄰居的空格下
            spots = [p for p in empty_spots if self.has_neighbor(self.board, p[0], p[1])]
            if not spots: spots = empty_spots
            m = random.choice(spots)
            self.make_move(m[0], m[1])
            return

        best_score = -float('inf')
        best_moves = []

        # 掃描盤面上每一個有鄰居的空位
        for r, c in empty_spots:
            if not self.has_neighbor(self.board, r, c): continue
            
            score = self.evaluate_spot_master(self.board, r, c)
            
            if score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))

        # 在多個最高分的走法中隨機選一個，增加變化性
        final_move = random.choice(best_moves)
        self.make_move(final_move[0], final_move[1])

    def has_neighbor(self, board, r, c):
        """只評估周圍兩格內有棋子的位置，極大提升運算速度"""
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] != 0:
                    return True
        return False

    def evaluate_spot_master(self, board, r, c):
        """大師級評估：綜合考慮自己下這裡的攻擊力，以及阻止對手下這裡的防禦力"""
        # ai_score 是「如果我(白)下這裡，能形成什麼陣型」
        ai_score, ai_shapes = self.get_shape_score(board, r, c, 2)
        # pl_score 是「如果玩家(黑)下這裡，能形成什麼陣型」(也就是我防守的價值)
        pl_score, pl_shapes = self.get_shape_score(board, r, c, 1)

        if self.difficulty == 3:
            # --- 絕對優先級 (生死交關，必須無條件執行) ---
            if "FIVE" in ai_shapes: return 20000000  # 1. 我能贏，直接下
            if "FIVE" in pl_shapes: return 15000000  # 2. 玩家下一步要贏了，必須擋
            if "LIVE4" in ai_shapes: return 10000000 # 3. 我能做活四 (對方擋不住)，下！
            if "LIVE4" in pl_shapes: return 8000000  # 4. 玩家要做活四了，必須死命擋！
            
            # --- 致命組合技 (無法單步防守的殺招) ---
            if ai_shapes.count("DEAD4") >= 2: return 7000000  # 雙死四 (必殺)
            if pl_shapes.count("DEAD4") >= 2: return 6000000  # 阻止玩家雙死四
            
            if "DEAD4" in ai_shapes and "LIVE3" in ai_shapes: return 5000000 # 死四+活三
            if "DEAD4" in pl_shapes and "LIVE3" in pl_shapes: return 4000000 # 阻止玩家死四+活三
            
            if ai_shapes.count("LIVE3") >= 2: return 3000000  # 雙活三
            if pl_shapes.count("LIVE3") >= 2: return 2000000  # 阻止玩家雙活三

            # --- 平衡期：像真正的高手一樣攻守兼備 ---
            # 防守玩家的潛在威脅 (pl_score) 稍微加權 1.1 倍，確保穩健
            return ai_score + pl_score * 1.1
            
        else:
            # 普通難度：不會考慮太深的組合技，只是單純的攻守相加
            if "FIVE" in ai_shapes: return 20000000
            if "FIVE" in pl_shapes: return 15000000
            if "LIVE4" in pl_shapes: return 8000000
            return ai_score + pl_score * 1.2

    def get_shape_score(self, board, r, c, stone):
        """精確計算如果將棋子下在 (r, c)，會形成什麼陣型"""
        board[r][c] = stone
        shapes = []
        
        for dr, dc in [(1,0), (0,1), (1,1), (1,-1)]:
            s = ""
            for i in range(-4, 5):
                nr, nc = r + dr*i, c + dc*i
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    val = board[nr][nc]
                    if val == stone: s += "X"
                    elif val == 0: s += "."
                    else: s += "O"
                else:
                    s += "O" # 邊界視同對手的棋子(擋住)
            
            # 字串特徵比對：找出這條線上形成的最強陣型
            if "XXXXX" in s: shapes.append("FIVE")
            elif ".XXXX." in s: shapes.append("LIVE4")
            # 死四 (被擋住一邊的四顆)
            elif "XXXX." in s or ".XXXX" in s or "XXX.X" in s or "X.XXX" in s or "XX.XX" in s: 
                shapes.append("DEAD4")
            # 活三 (兩端有空間的連三或跳三)
            elif ".XXX.." in s or "..XXX." in s or ".XX.X." in s or ".X.XX." in s: 
                shapes.append("LIVE3")
            # 死三 (被擋住一邊的三顆)
            elif "XXX." in s or ".XXX" in s or "XX.X" in s or "X.XX" in s: 
                shapes.append("DEAD3")
            # 活二
            elif "..XX.." in s or ".XX..." in s or "...XX." in s or ".X.X." in s: 
                shapes.append("LIVE2")
            else: 
                shapes.append("NONE")
            
        # 測試完畢，把棋盤復原
        board[r][c] = 0
        
        # 根據形成的陣型給予基礎分數
        score = 0
        for sh in shapes:
            if sh == "DEAD4": score += 2000
            # ★ 重大修正：防守/製造「活三」的分數 (5000) 必須大於盲目衝「死四」的分數 (2000)
            elif sh == "LIVE3": score += 5000  
            elif sh == "DEAD3": score += 500
            elif sh == "LIVE2": score += 100
            
        return score, shapes

if __name__ == "__main__":
    game = AnimeGomoku()
    game.run()