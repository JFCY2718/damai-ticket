"""
大麦网 App 自动抢票脚本 (Android + uiautomator2)

使用前准备：
1. 手机开启 USB 调试，用数据线连接电脑
2. pip install -r requirements.txt
3. 手机上打开大麦 App，登录账号，进入目标演出详情页
4. 运行脚本，等待自动抢票

用法：
    python damai_ticket.py --time "19:00:00" --ticket-index 0 --count 1
"""

import uiautomator2 as u2
import time
import datetime
import argparse
import ntplib
import sys


class DamaiSnatcher:
    def __init__(self, target_time: str, ticket_index: int = 0, count: int = 1):
        """
        target_time: 抢票时间，格式 "HH:MM:SS"
        ticket_index: 票档索引（0=第一档，1=第二档...）
        count: 购买张数
        """
        self.ticket_index = ticket_index
        self.count = count
        self.device = None

        # 解析目标时间
        today = datetime.date.today()
        t = datetime.datetime.strptime(target_time, "%H:%M:%S").time()
        self.target_time = datetime.datetime.combine(today, t)

        # 时间偏移量（本地时间与NTP服务器的差值）
        self.time_offset = 0.0

    def connect(self):
        """连接手机"""
        print("[*] 正在连接手机...")
        self.device = u2.connect()  # 自动检测USB连接的设备
        info = self.device.info
        print(f"[+] 已连接: {info.get('productName', 'Unknown')} "
              f"(屏幕 {self.device.window_size()})")

        # 确认大麦App在前台
        current = self.device.app_current()
        if "damai" not in current.get("package", "").lower():
            print("[!] 警告: 当前前台不是大麦App，请手动切换到大麦App的演出详情页")
        else:
            print("[+] 大麦App已在前台")

    def sync_time(self):
        """通过NTP同步时间，获取精确时间偏移"""
        print("[*] 正在同步网络时间...")
        ntp_servers = [
            "ntp.aliyun.com",
            "time.windows.com",
            "cn.ntp.org.cn",
            "ntp.tencent.com",
        ]
        client = ntplib.NTPClient()
        for server in ntp_servers:
            try:
                resp = client.request(server, timeout=3)
                self.time_offset = resp.offset
                print(f"[+] NTP同步成功 (服务器: {server}, 偏移: {self.time_offset:.3f}s)")
                return
            except Exception:
                continue
        print("[!] NTP同步失败，使用本地时间（可能有几百毫秒误差）")

    def now(self) -> datetime.datetime:
        """获取校准后的当前时间"""
        return datetime.datetime.now() + datetime.timedelta(seconds=self.time_offset)

    def wait_until_target(self):
        """等待到目标时间"""
        while True:
            remaining = (self.target_time - self.now()).total_seconds()
            if remaining <= 0:
                print("[!] 目标时间已过，立即开始抢票!")
                return
            if remaining > 60:
                print(f"[*] 距离开抢还有 {remaining:.0f} 秒，等待中...")
                time.sleep(30)
            elif remaining > 3:
                print(f"[*] 距离开抢还有 {remaining:.1f} 秒...")
                time.sleep(0.5)
            elif remaining > 0.1:
                # 最后几秒，高精度等待
                time.sleep(0.01)
            else:
                return

    def click_buy_button(self) -> bool:
        """点击购买按钮"""
        # 大麦App常见的购买按钮文案
        buy_texts = ["立即抢购", "立即购买", "立即预订", "选座购买", "确定"]
        for text in buy_texts:
            btn = self.device(text=text)
            if btn.exists(timeout=0.3):
                btn.click()
                print(f"[+] 点击了「{text}」")
                return True
        # 兜底：尝试点击右下角区域（购买按钮通常在这里）
        w, h = self.device.window_size()
        self.device.click(int(w * 0.75), int(h * 0.92))
        print("[*] 未找到按钮文字，点击了右下角区域")
        return True

    def select_ticket_tier(self):
        """选择票档"""
        time.sleep(0.2)
        # 尝试通过索引选择票档
        # 大麦的票档通常是一组可点击的标签
        tiers = self.device(resourceId="cn.damai:id/project_detail_perform_price_recycler")
        if tiers.exists(timeout=0.5):
            children = tiers.child(className="android.widget.TextView")
            if children.count > self.ticket_index:
                children[self.ticket_index].click()
                print(f"[+] 选择了第 {self.ticket_index + 1} 档票")
                return

        # 备选：直接点击第一个可选票档
        price_tags = self.device(className="android.widget.TextView", clickable=True)
        for tag in price_tags:
            text = tag.get_text()
            if "¥" in text or "元" in text:
                tag.click()
                print(f"[+] 选择了票档: {text}")
                return

    def select_ticket_count(self):
        """选择购票数量"""
        if self.count <= 1:
            return
        # 点击 "+" 按钮增加数量
        plus_btn = self.device(resourceId="cn.damai:id/img_jia")
        if not plus_btn.exists(timeout=0.3):
            plus_btn = self.device(description="增加")
        if plus_btn.exists(timeout=0.3):
            for _ in range(self.count - 1):
                plus_btn.click()
                time.sleep(0.05)
            print(f"[+] 已选择 {self.count} 张票")

    def confirm_order(self):
        """确认订单"""
        confirm_texts = ["确认", "立即支付", "提交订单", "立即下单", "确认订单"]
        for _ in range(10):  # 最多尝试10次
            for text in confirm_texts:
                btn = self.device(text=text)
                if btn.exists(timeout=0.2):
                    btn.click()
                    print(f"[+] 点击了「{text}」")
                    return True
            time.sleep(0.1)
        print("[-] 未找到确认按钮")
        return False

    def run(self):
        """主流程"""
        print("=" * 50)
        print("  大麦网自动抢票脚本 - 明日方舟音律联觉")
        print("=" * 50)

        self.connect()
        self.sync_time()

        print(f"\n[*] 目标抢票时间: {self.target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[*] 票档选择: 第 {self.ticket_index + 1} 档")
        print(f"[*] 购买数量: {self.count} 张")
        print("[*] 请确保大麦App已打开到演出详情页，且已登录")
        print("-" * 50)

        self.wait_until_target()

        print("\n[!!!] 开始抢票!")
        start = time.time()

        # 第一步：疯狂点击购买按钮
        max_retry = 50
        for attempt in range(max_retry):
            self.click_buy_button()
            time.sleep(0.05)

            # 检查是否进入了选票/确认页面
            if self.device(text="确认").exists(timeout=0.1) or \
               self.device(text="提交订单").exists(timeout=0.1) or \
               self.device(textContains="¥").exists(timeout=0.1):
                print(f"[+] 第 {attempt + 1} 次尝试进入了订单页面")
                break
        else:
            print("[-] 多次尝试后仍未进入订单页面，继续尝试...")

        # 第二步：选择票档和数量
        self.select_ticket_tier()
        self.select_ticket_count()

        # 第三步：确认订单
        self.confirm_order()

        elapsed = time.time() - start
        print(f"\n[*] 抢票流程完成，耗时 {elapsed:.2f} 秒")
        print("[*] 请在手机上检查订单状态并完成支付!")


def main():
    parser = argparse.ArgumentParser(description="大麦网自动抢票脚本")
    parser.add_argument("--time", "-t", default="19:00:00",
                        help="抢票时间，格式 HH:MM:SS（默认 19:00:00）")
    parser.add_argument("--ticket-index", "-i", type=int, default=0,
                        help="票档索引，0=第一档（默认 0）")
    parser.add_argument("--count", "-c", type=int, default=1,
                        help="购买张数（默认 1）")
    parser.add_argument("--advance", "-a", type=float, default=0.5,
                        help="提前多少秒开始点击（默认 0.5）")
    args = parser.parse_args()

    snatcher = DamaiSnatcher(
        target_time=args.time,
        ticket_index=args.ticket_index,
        count=args.count,
    )
    # 提前量：在目标时间前一点点就开始点
    snatcher.target_time -= datetime.timedelta(seconds=args.advance)

    try:
        snatcher.run()
    except KeyboardInterrupt:
        print("\n[*] 用户中断")
    except Exception as e:
        print(f"\n[!] 出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
