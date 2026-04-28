import pyautogui
import time
import os
import numpy as np
import cv2
from PIL import Image

# ================= 配置 =================
WAIT_SEC = 1.0       # 每屏间隔
SAVE_DIR = "wx_chat_snap"
MERGE_FILE = "微信群完整长图.png"
# ========================================

os.makedirs(SAVE_DIR, exist_ok=True)

def select_region_with_mask():
    """全屏半透明遮罩，拖拽选聊天区域，回车确认"""
    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    h, w = screen.shape[:2]

    mask = np.zeros_like(screen, dtype=np.uint8)
    mask[:] = (0, 0, 0)
    alpha = 0.6
    show_img = cv2.addWeighted(mask, alpha, screen, 1 - alpha, 0)

    region = None
    drawing = False
    start_x = start_y = 0

    def mouse_event(event, x, y, flags, param):
        nonlocal drawing, start_x, start_y, region, show_img
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_x, start_y = x, y
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            temp = show_img.copy()
            cv2.rectangle(temp, (start_x, start_y), (x, y), (0, 0, 255), 2)
            cv2.imshow("框选单条消息显示区域 | 回车确定", temp)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            x1 = min(start_x, x)
            y1 = min(start_y, y)
            ww = abs(x - start_x)
            hh = abs(y - start_y)
            region = (x1, y1, ww, hh)

    cv2.namedWindow("框选单条消息显示区域 | 回车确定", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("框选单条消息显示区域 | 回车确定", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("框选单条消息显示区域 | 回车确定", mouse_event)
    cv2.imshow("框选单条消息显示区域 | 回车确定", show_img)

    while True:
        key = cv2.waitKey(1)
        if key == 13 and region is not None:
            break
        if key == 27:
            exit()
    cv2.destroyAllWindows()
    return region

def get_img_fingerprint(img: Image.Image):
    """图片指纹，判断到底重复"""
    small = img.resize((80, 50), Image.Resampling.LANCZOS)
    arr = np.array(small)
    return hash(arr.tobytes())

def merge_vertical(img_list, save_path):
    """垂直拼接所有消息截图"""
    if not img_list:
        return
    w = img_list[0].width
    total_h = sum(i.height for i in img_list)
    new_img = Image.new("RGB", (w, total_h), (255, 255, 255))
    y = 0
    for im in img_list:
        new_img.paste(im, (0, y))
        y += im.height
    new_img.save(save_path)
    print(f"\n✅ 完整长图已保存：{save_path}")

if __name__ == "__main__":
    print("🖱 即将打开全屏遮罩，框选【一屏消息显示区域】，回车确认")
    time.sleep(2)
    # 手动圈定聊天可视区
    chat_box = select_region_with_mask()
    x, y, box_w, box_h = chat_box
    print(f"✅ 单屏消息区域已选定：{chat_box}")

    # 鼠标定位到聊天窗口中间
    center_x = x + box_w // 2
    center_y = y + box_h // 2
    pyautogui.moveTo(center_x, center_y)

    img_cache = []
    hash_set = set()
    count = 0

    print("⏳ 5秒后开始逐屏截取消息，请勿操作鼠标键盘...")
    time.sleep(5)

    while True:
        # 截取当前一屏完整消息
        frame = pyautogui.screenshot(region=chat_box)
        fp = get_img_fingerprint(frame)

        # 重复画面=到底停止
        if fp in hash_set:
            print("\n📭 已到达聊天记录底部，自动结束采集")
            break

        hash_set.add(fp)
        img_cache.append(frame)
        frame.save(os.path.join(SAVE_DIR, f"msg_{count:04d}.png"))
        print(f"📸 已截取第 {count+1} 条消息屏")
        count += 1

        # 模拟键盘 PageDown 精准下移一整屏（完美匹配消息框）
        pyautogui.press("pagedown")
        time.sleep(WAIT_SEC)

    # 自动合并成长图
    merge_vertical(img_cache, MERGE_FILE)
    print("🎉 全部完成")