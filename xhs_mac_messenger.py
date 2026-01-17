#!/usr/bin/env python3
"""
小紅書 Mac App 私訊自動化工具
用於在 Mac 版小紅書 App 中發送私訊

使用前請先：
1. pip install pyautogui pillow pyobjc-framework-Quartz
2. 在系統偏好設置中授予「輔助使用」權限給 Terminal/IDE
3. 安裝並登入小紅書 Mac App
"""

import subprocess
import time
import random
import os
import csv
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

try:
    import pyautogui
    # Mac 上需要這個來支持 Retina 顯示器
    pyautogui.PAUSE = 0.5  # 每個操作後暫停 0.5 秒
    pyautogui.FAILSAFE = True  # 移動滑鼠到左上角可中止
except ImportError:
    print("請安裝 pyautogui: pip install pyautogui")
    exit(1)

# ========== 配置 ==========
# 小紅書 App Bundle ID
XHS_BUNDLE_ID = "com.xingin.discover"  # 小紅書 Mac App 的 Bundle ID
XHS_APP_NAME = "小红书"  # App 名稱

# 私訊配置
MAX_MESSAGES_PER_RUN = 5  # 每次運行最多發送幾條私訊
MESSAGE_DELAY_MIN = 300   # 發私訊最小間隔 (秒) = 5分鐘
MESSAGE_DELAY_MAX = 600   # 發私訊最大間隔 (秒) = 10分鐘

# 暗語訊息模板列表
SECRET_MESSAGES = [
    "你好～看到你家童裝很不錯，可以伽V聊聊合作嗎？",
    "親，想了解批發價，方便加嘉嗎？",
    "你好，對你們家童裝有興趣，能加薇聊嗎？",
    "這款真好看！想拿貨，可以夾V嗎？",
    "想做代理，方便加徽詳聊嗎？",
    "有興趣合作，煮頁有聯繫方式嗎？",
    "想了解更多，看主有詳細嗎？",
    "求合作～煮叶留了聯繫方式嗎？",
    "想批發，可以si我詳情嗎？",
    "對童裝很有興趣，絲我可以聊嗎？",
    "做代購的，想斯聊批發價～",
    "香港批發商，薰的來，想長期合作",
    "想做童裝批發，懂的懂，求私",
    "同行求拿貨渠道，薰的来聯繫",
    "你好！童裝質量看起來不錯，我是香港的，想了解代理方式，方便伽薇聊聊嗎？",
    "親愛的～我在做童裝批發，對你家款式很有興趣，可以看煮頁嗎？",
    "你好，我是做跨境電商的，想長期合作拿貨，si我可以詳聊嗎？",
]

# 數據文件
DATA_FILE = "suppliers_data.csv"

# 日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# ========== 數據模型 ==========
@dataclass
class Supplier:
    user_id: str
    nickname: str
    bio: str = ""
    followers: int = 0
    notes_count: int = 0
    ip_location: str = ""
    supplier_type: str = "未知"
    wechat: str = ""
    score: float = 0.0
    profile_url: str = ""
    keywords: str = ""
    message_sent: bool = False
    message_content: str = ""
    message_time: str = ""
    reply_received: bool = False
    reply_content: str = ""
    reply_time: str = ""
    created_at: str = ""
    updated_at: str = ""

# ========== 數據管理器 ==========
class DataManager:
    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self.suppliers: Dict[str, Supplier] = {}
        self.load()
    
    def load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    s = Supplier(
                        user_id=row.get('user_id', ''),
                        nickname=row.get('nickname', ''),
                        bio=row.get('bio', ''),
                        followers=int(row.get('followers', 0) or 0),
                        notes_count=int(row.get('notes_count', 0) or 0),
                        ip_location=row.get('ip_location', ''),
                        supplier_type=row.get('supplier_type', '未知'),
                        wechat=row.get('wechat', ''),
                        score=float(row.get('score', 0) or 0),
                        profile_url=row.get('profile_url', ''),
                        keywords=row.get('keywords', ''),
                        message_sent=row.get('message_sent', '').lower() == 'true',
                        message_content=row.get('message_content', ''),
                        message_time=row.get('message_time', ''),
                        reply_received=row.get('reply_received', '').lower() == 'true',
                        reply_content=row.get('reply_content', ''),
                        reply_time=row.get('reply_time', ''),
                        created_at=row.get('created_at', ''),
                        updated_at=row.get('updated_at', ''),
                    )
                    if s.user_id:
                        self.suppliers[s.user_id] = s
            logger.info(f"已加載 {len(self.suppliers)} 個供應商記錄")
        except Exception as e:
            logger.error(f"加載數據失敗: {e}")
    
    def save(self):
        if not self.suppliers:
            return
        fieldnames = [
            'user_id', 'nickname', 'bio', 'followers', 'notes_count', 'ip_location',
            'supplier_type', 'wechat', 'score', 'profile_url', 'keywords',
            'message_sent', 'message_content', 'message_time',
            'reply_received', 'reply_content', 'reply_time',
            'created_at', 'updated_at'
        ]
        try:
            with open(self.filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for s in self.suppliers.values():
                    writer.writerow(asdict(s))
            logger.info(f"已保存 {len(self.suppliers)} 個供應商記錄")
        except Exception as e:
            logger.error(f"保存數據失敗: {e}")
    
    def update(self, user_id: str, **kwargs):
        if user_id not in self.suppliers:
            return
        s = self.suppliers[user_id]
        for k, v in kwargs.items():
            if hasattr(s, k):
                setattr(s, k, v)
        s.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save()
    
    def get_unsent(self) -> List[Supplier]:
        return [s for s in self.suppliers.values() if not s.message_sent]
    
    def get_all(self) -> List[Supplier]:
        return list(self.suppliers.values())

# ========== Mac App 自動化 ==========
class MacAppAutomation:
    """Mac App 自動化控制器"""
    
    def __init__(self):
        self.app_name = XHS_APP_NAME
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"螢幕尺寸: {self.screen_width} x {self.screen_height}")
    
    def open_app(self) -> bool:
        """打開小紅書 App"""
        try:
            # 使用 AppleScript 打開 App
            script = f'''
            tell application "{self.app_name}"
                activate
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            time.sleep(3)  # 等待 App 啟動
            logger.info(f"✓ 已打開 {self.app_name}")
            return True
        except Exception as e:
            logger.error(f"無法打開 App: {e}")
            # 嘗試通過 Spotlight 搜索
            try:
                pyautogui.hotkey('command', 'space')
                time.sleep(0.5)
                pyautogui.typewrite('xiaohongshu', interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(3)
                return True
            except:
                return False
    
    def is_app_running(self) -> bool:
        """檢查 App 是否正在運行"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', self.app_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def bring_to_front(self):
        """將 App 帶到前台"""
        script = f'''
        tell application "{self.app_name}"
            activate
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=False)
        time.sleep(1)
    
    def search_user(self, nickname: str) -> bool:
        """搜索用戶"""
        try:
            self.bring_to_front()
            time.sleep(0.5)
            
            # 點擊搜索框 (通常在頂部)
            # 使用 Command+F 或點擊搜索圖標
            pyautogui.hotkey('command', 'f')
            time.sleep(1)
            
            # 清空搜索框
            pyautogui.hotkey('command', 'a')
            time.sleep(0.2)
            
            # 輸入暱稱
            # 注意：pyautogui.write() 不支持中文，需要用剪貼板
            self._type_chinese(nickname)
            time.sleep(0.5)
            
            # 按 Enter 搜索
            pyautogui.press('enter')
            time.sleep(2)
            
            logger.info(f"✓ 已搜索: {nickname}")
            return True
            
        except Exception as e:
            logger.error(f"搜索用戶失敗: {e}")
            return False
    
    def open_user_profile_by_url(self, profile_url: str) -> bool:
        """通過 URL 打開用戶主頁"""
        try:
            # 使用 open 命令打開 URL (會自動用小紅書 App 打開)
            # 小紅書的 URL scheme: xhsdiscover://
            
            # 先轉換 Web URL 為 App URL scheme
            # https://www.xiaohongshu.com/user/profile/xxx -> xhsdiscover://user/xxx
            user_id = profile_url.split('/user/profile/')[-1].split('?')[0]
            app_url = f"xhsdiscover://user/{user_id}"
            
            subprocess.run(['open', app_url], check=True)
            time.sleep(3)  # 等待頁面加載
            
            logger.info(f"✓ 已打開用戶主頁: {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"打開用戶主頁失敗: {e}")
            # 備用方案：直接打開 Web URL
            try:
                subprocess.run(['open', profile_url], check=True)
                time.sleep(3)
                return True
            except:
                return False
    
    def click_message_button(self) -> bool:
        """點擊私信按鈕"""
        try:
            self.bring_to_front()
            time.sleep(0.5)
            
            # 方法1: 使用圖像識別找到私信按鈕
            # (需要預先截圖保存按鈕圖片)
            button_images = [
                'msg_button.png',
                'private_msg.png',
                'chat_button.png',
            ]
            
            for img in button_images:
                if os.path.exists(img):
                    try:
                        location = pyautogui.locateOnScreen(img, confidence=0.8)
                        if location:
                            center = pyautogui.center(location)
                            pyautogui.click(center)
                            time.sleep(1)
                            logger.info("✓ 通過圖像識別點擊私信按鈕")
                            return True
                    except:
                        pass
            
            # 方法2: 使用固定位置 (需要根據實際 App 界面調整)
            # 私信按鈕通常在用戶主頁的右上角或關注按鈕旁邊
            # 這裡使用相對位置
            
            # 假設 App 窗口在螢幕中央，私信按鈕在右側
            # 這些座標需要根據實際情況調整
            possible_positions = [
                (self.screen_width * 0.7, self.screen_height * 0.15),  # 右上角
                (self.screen_width * 0.8, self.screen_height * 0.2),   # 更右邊
                (self.screen_width * 0.6, self.screen_height * 0.25),  # 關注按鈕旁
            ]
            
            logger.warning("⚠️ 無法自動定位私信按鈕")
            logger.info("請手動點擊私信按鈕，然後按 Enter 繼續...")
            input()
            return True
            
        except Exception as e:
            logger.error(f"點擊私信按鈕失敗: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """發送私訊"""
        try:
            time.sleep(1)
            
            # 等待聊天窗口出現
            # 點擊輸入框 (通常在底部)
            # 使用相對位置點擊底部輸入區域
            input_y = self.screen_height * 0.9  # 底部 10% 位置
            input_x = self.screen_width * 0.5   # 水平居中
            
            pyautogui.click(input_x, input_y)
            time.sleep(0.5)
            
            # 輸入訊息 (使用剪貼板支持中文)
            self._type_chinese(message)
            time.sleep(0.5)
            
            # 發送訊息
            # 方法1: 按 Enter
            pyautogui.press('enter')
            
            # 方法2: 點擊發送按鈕 (如果 Enter 不行)
            # send_x = self.screen_width * 0.9
            # send_y = input_y
            # pyautogui.click(send_x, send_y)
            
            time.sleep(1)
            logger.info(f"✓ 已發送訊息")
            return True
            
        except Exception as e:
            logger.error(f"發送訊息失敗: {e}")
            return False
    
    def _type_chinese(self, text: str):
        """輸入中文 (使用剪貼板)"""
        try:
            import subprocess
            
            # 將文字複製到剪貼板
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                env={**os.environ, 'LANG': 'en_US.UTF-8'}
            )
            process.communicate(text.encode('utf-8'))
            
            # 粘貼
            time.sleep(0.2)
            pyautogui.hotkey('command', 'v')
            time.sleep(0.3)
            
        except Exception as e:
            logger.error(f"輸入中文失敗: {e}")
            # 備用方案：逐字輸入
            for char in text:
                pyautogui.press(char) if char.isascii() else None
    
    def go_back(self):
        """返回上一頁"""
        try:
            # 使用 Command + [ 或 ESC
            pyautogui.hotkey('command', '[')
            time.sleep(1)
        except:
            pyautogui.press('escape')
            time.sleep(1)
    
    def take_screenshot(self, filename: str = None) -> str:
        """截圖保存"""
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        logger.info(f"📸 已保存截圖: {filename}")
        return filename

# ========== 私訊發送器 ==========
class MacMessenger:
    """Mac App 私訊發送器"""
    
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.mac = MacAppAutomation()
    
    def send_messages(self, max_count: int = MAX_MESSAGES_PER_RUN):
        """批量發送私訊"""
        unsent = self.dm.get_unsent()
        if not unsent:
            logger.info("沒有需要發送私訊的供應商")
            return
        
        logger.info(f"待發送私訊: {len(unsent)} 個供應商")
        logger.info(f"本次最多發送: {max_count} 條")
        
        # 打開小紅書 App
        if not self.mac.open_app():
            logger.error("無法打開小紅書 App")
            return
        
        # 隨機打亂順序
        random.shuffle(unsent)
        
        sent_count = 0
        for supplier in unsent:
            if sent_count >= max_count:
                break
            
            logger.info(f"\n{'='*50}")
            logger.info(f"[{sent_count+1}/{max_count}] 準備私訊: {supplier.nickname}")
            
            # 隨機選擇暗語訊息
            message = random.choice(SECRET_MESSAGES)
            logger.info(f"暗語: {message}")
            
            success = self._send_single_message(supplier, message)
            
            if success:
                # 更新數據
                self.dm.update(
                    supplier.user_id,
                    message_sent=True,
                    message_content=message,
                    message_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                sent_count += 1
                logger.info(f"✓ 已發送私訊給: {supplier.nickname}")
                
                # 低頻率延遲
                if sent_count < max_count and sent_count < len(unsent):
                    wait_time = random.randint(MESSAGE_DELAY_MIN, MESSAGE_DELAY_MAX)
                    logger.info(f"等待 {wait_time//60} 分 {wait_time%60} 秒後發送下一條...")
                    time.sleep(wait_time)
            else:
                logger.warning(f"✗ 發送失敗: {supplier.nickname}")
                # 截圖保存，方便調試
                self.mac.take_screenshot(f"debug_{supplier.user_id[:8]}.png")
            
            # 返回主頁
            self.mac.go_back()
            time.sleep(2)
        
        logger.info(f"\n本次共發送 {sent_count} 條私訊")
    
    def _send_single_message(self, supplier: Supplier, message: str) -> bool:
        """發送單條私訊"""
        try:
            # 1. 打開用戶主頁
            if not self.mac.open_user_profile_by_url(supplier.profile_url):
                return False
            
            time.sleep(2)
            
            # 2. 點擊私信按鈕
            if not self.mac.click_message_button():
                return False
            
            time.sleep(1)
            
            # 3. 發送訊息
            if not self.mac.send_message(message):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"發送私訊失敗: {e}")
            return False
    
    def interactive_mode(self):
        """交互式發送模式 (半自動)"""
        unsent = self.dm.get_unsent()
        if not unsent:
            logger.info("沒有需要發送私訊的供應商")
            return
        
        logger.info(f"共 {len(unsent)} 個供應商待發送私訊")
        logger.info("進入交互式模式 (半自動)")
        logger.info("="*50)
        
        # 打開小紅書 App
        self.mac.open_app()
        
        for i, supplier in enumerate(unsent):
            print(f"\n[{i+1}/{len(unsent)}] {supplier.nickname}")
            print(f"主頁: {supplier.profile_url}")
            print(f"簡介: {supplier.bio[:50]}..." if supplier.bio else "簡介: 無")
            
            message = random.choice(SECRET_MESSAGES)
            print(f"\n建議暗語: {message}")
            
            print("\n操作選項:")
            print("  1. 自動發送此訊息")
            print("  2. 手動輸入訊息")
            print("  3. 跳過此供應商")
            print("  4. 結束")
            
            choice = input("\n請選擇 (1/2/3/4): ").strip()
            
            if choice == '1':
                # 打開主頁
                self.mac.open_user_profile_by_url(supplier.profile_url)
                print("\n請手動點擊「私信」按鈕，然後按 Enter...")
                input()
                
                # 發送訊息
                self.mac.send_message(message)
                
                # 更新數據
                self.dm.update(
                    supplier.user_id,
                    message_sent=True,
                    message_content=message,
                    message_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                print("✓ 已發送並記錄")
                
            elif choice == '2':
                custom_msg = input("請輸入訊息: ").strip()
                if custom_msg:
                    self.mac.open_user_profile_by_url(supplier.profile_url)
                    print("\n請手動點擊「私信」按鈕，然後按 Enter...")
                    input()
                    
                    self.mac.send_message(custom_msg)
                    
                    self.dm.update(
                        supplier.user_id,
                        message_sent=True,
                        message_content=custom_msg,
                        message_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    print("✓ 已發送並記錄")
                    
            elif choice == '3':
                print("已跳過")
                continue
                
            elif choice == '4':
                print("結束")
                break
            
            # 等待一下再處理下一個
            time.sleep(2)
        
        print(f"\n完成！已發送的供應商數: {len([s for s in self.dm.get_all() if s.message_sent])}")

# ========== 主程序 ==========
def main():
    print("""
╔═══════════════════════════════════════════════════════╗
║     小紅書 Mac App 私訊工具 v1.0                      ║
╚═══════════════════════════════════════════════════════╝

⚠️  使用前請確保:
    1. 已安裝小紅書 Mac App
    2. 已在 App 中登入帳號
    3. 已授予 Terminal「輔助使用」權限
       (系統偏好設置 → 安全性與隱私 → 輔助使用)
    """)
    
    # 初始化
    dm = DataManager(DATA_FILE)
    messenger = MacMessenger(dm)
    
    while True:
        print("\n" + "="*50)
        print("請選擇操作:")
        print("  1. 🤖 自動發送私訊 (全自動)")
        print("  2. 🖱️  交互式發送 (半自動，更可靠)")
        print("  3. 📋 查看待發送列表")
        print("  4. 📊 查看統計")
        print("  5. 🔧 測試 App 控制")
        print("  6. 🚪 退出")
        print("="*50)
        
        choice = input("\n請輸入選項 (1-6): ").strip()
        
        if choice == '1':
            unsent = dm.get_unsent()
            if not unsent:
                print("\n沒有需要發送私訊的供應商")
                print("請先運行 xhs_scraper.py 搜索供應商")
                continue
            
            print(f"\n📮 待發送私訊: {len(unsent)} 個供應商")
            print(f"⏱️ 發送間隔: {MESSAGE_DELAY_MIN//60}-{MESSAGE_DELAY_MAX//60} 分鐘")
            print(f"📝 本次最多發送: {MAX_MESSAGES_PER_RUN} 條")
            
            confirm = input("\n確定開始自動發送? (y/n): ").strip().lower()
            if confirm == 'y':
                messenger.send_messages(MAX_MESSAGES_PER_RUN)
        
        elif choice == '2':
            unsent = dm.get_unsent()
            if not unsent:
                print("\n沒有需要發送私訊的供應商")
                continue
            
            print(f"\n📮 待發送: {len(unsent)} 個供應商")
            print("交互式模式：每個供應商會提示您確認後再發送")
            
            confirm = input("\n開始? (y/n): ").strip().lower()
            if confirm == 'y':
                messenger.interactive_mode()
        
        elif choice == '3':
            unsent = dm.get_unsent()
            if not unsent:
                print("\n沒有待發送的供應商")
                continue
            
            print(f"\n待發送列表 ({len(unsent)} 個):")
            for i, s in enumerate(unsent[:20], 1):
                print(f"  {i}. {s.nickname} - {s.profile_url}")
            if len(unsent) > 20:
                print(f"  ... 還有 {len(unsent)-20} 個")
        
        elif choice == '4':
            all_suppliers = dm.get_all()
            sent = [s for s in all_suppliers if s.message_sent]
            replied = [s for s in all_suppliers if s.reply_received]
            
            print("\n📋 數據統計:")
            print(f"   總供應商數: {len(all_suppliers)}")
            print(f"   已發私訊: {len(sent)}")
            print(f"   已收回覆: {len(replied)}")
            print(f"   待發送: {len(all_suppliers) - len(sent)}")
        
        elif choice == '5':
            print("\n🔧 測試 App 控制")
            print("1. 測試打開小紅書 App")
            
            mac = MacAppAutomation()
            if mac.open_app():
                print("✓ App 已打開")
                
                print("\n2. 測試截圖")
                mac.take_screenshot("test_screenshot.png")
                
                print("\n3. 測試中文輸入")
                print("將在 3 秒後輸入測試文字，請確保有輸入框聚焦...")
                time.sleep(3)
                mac._type_chinese("測試中文輸入")
                print("✓ 測試完成")
            else:
                print("✗ 無法打開 App")
        
        elif choice == '6':
            print("\n👋 再見!")
            break
        
        else:
            print("\n⚠️ 無效選項")

if __name__ == "__main__":
    main()
