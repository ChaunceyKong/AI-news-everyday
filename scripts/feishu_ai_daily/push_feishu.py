import os
import sys
import json
import time
import hmac
import hashlib
import base64
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# 解决 Windows 控制台默认 GBK 编码输出 Emoji 或特殊字符报错问题
if sys.platform == "win32":
    import io
    try:
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding.lower() != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))
USER_AGENT = "aihot-skill/1.7.1 (+https://aihot.news/aihot-skill/)"

def load_env(env_path=None):
    """简易加载 .env 文件，避免依赖第三方库 python-dotenv"""
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key not in os.environ:
                os.environ[key] = val

def fetch_aihot_items(mode="selected", window="24h", limit=8):
    """
    从 aihot.news API 获取 AI 资讯
    mode: selected (精选) / all (全部公开) / hot (热点榜)
    """
    if mode == "hot":
        url = "https://aihot.news/api/v1/hot-topics"
    else:
        url = f"https://aihot.news/api/v1/items?mode={mode}&window={window}&limit={limit}"
    
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("items", [])
    except Exception as e:
        print(f"[Error] 获取 AIHOT 数据失败: {e}", file=sys.stderr)
        return []

def format_time(pub_iso, disc_iso):
    """把 ISO 时间转成北京时间格式字符串"""
    if pub_iso:
        dt = datetime.fromisoformat(pub_iso.replace("Z", "+00:00")).astimezone(BEIJING_TZ)
        return dt.strftime("%m月%d日 %H:%M")
    elif disc_iso:
        dt = datetime.fromisoformat(disc_iso.replace("Z", "+00:00")).astimezone(BEIJING_TZ)
        return dt.strftime("%m月%d日 %H:%M") + " (收录)"
    return "未知时间"

def build_feishu_card(items, mode="selected", window="24h"):
    """
    构建飞书交互式卡片消息 (Interactive Card)
    """
    now_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    today_str = datetime.now(BEIJING_TZ).strftime("%Y年%m月%d日")
    
    if mode == "hot":
        title_text = f"🔥 当前最热 AI 话题榜 Top 10 | {today_str}"
        card_color = "orange"
    else:
        title_text = f"🤖 AI 圈 24小时重点精选 | {today_str}"
        card_color = "blue"

    elements = []
    
    # 顶部导语
    elements.append({
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": f"📅 **推送时间**：{now_str} (北京时间) · **精选条目**：共 {len(items)} 条"
        }
    })
    elements.append({"tag": "hr"})

    for i, item in enumerate(items, 1):
        title = item.get("title", "无标题")
        link = item.get("links", {}).get("aihot", "https://aihot.news")
        source_name = item.get("source", {}).get("name", "网络资讯")
        summary = (item.get("summary") or "").strip()
        reason = (item.get("reason") or "").strip()
        
        md_parts = []
        if mode == "hot":
            rank = item.get("rank", i)
            md_parts.append(f"**第 {rank} 名 · [{title}]({link})**")
            md_parts.append(f"📌 来源：`{source_name}`")
        else:
            time_str = format_time(item.get("publishedAt"), item.get("discoveredAt"))
            md_parts.append(f"**{i}. [{title}]({link})**")
            md_parts.append(f"🕒 `{source_name}` · {time_str}")
            if summary:
                md_parts.append(f"📝 {summary}")
            if reason:
                md_parts.append(f"💡 **值得关注**：{reason}")

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "\n".join(md_parts)
            }
        })
        # 条目间分隔线
        if i < len(items):
            elements.append({"tag": "hr"})

    # 底部备注
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": "数据来源：AIHOT 公开精选资讯 · 自动定时推送"
            }
        ]
    })

    card_payload = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title_text
                },
                "template": card_color
            },
            "elements": elements
        }
    }
    return card_payload

def generate_sign(secret, timestamp):
    """计算飞书机器人的 HMAC-SHA256 签名"""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")

def send_to_feishu(webhook_url, payload, secret=None):
    """通过 HTTP POST 发送卡片到飞书 Webhook"""
    if secret:
        timestamp = str(int(time.time()))
        sign = generate_sign(secret, timestamp)
        payload["timestamp"] = timestamp
        payload["sign"] = sign

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            result = json.loads(resp_body)
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                print(f"[Success] 飞书推送成功: {resp_body}")
                return True
            else:
                print(f"[Warning] 飞书返回错误: {resp_body}", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        print(f"[Error] HTTP 请求异常: {e.code} {e.read().decode('utf-8')}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[Error] 发送失败: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="AI 圈 24小时重点资讯飞书定时推送脚本")
    parser.add_argument("--webhook", help="飞书自定义机器人的 Webhook URL")
    parser.add_argument("--secret", help="飞书自定义机器人的安全设置签名密钥 (可选)")
    parser.add_argument("--mode", default="selected", choices=["selected", "all", "hot"], help="资讯模式: selected(精选，默认), all(全量), hot(最热话题榜)")
    parser.add_argument("--limit", type=int, default=8, help="推送条数 (默认 8 条)")
    parser.add_argument("--window", default="24h", choices=["24h", "7d"], help="时间窗口 (默认 24h)")
    parser.add_argument("--dry-run", action="store_true", help="演练模式，仅打印卡片内容而不向飞书发送")
    args = parser.parse_args()

    # 加载 .env
    load_env()

    webhook_url = args.webhook or os.environ.get("FEISHU_WEBHOOK_URL")
    secret = args.secret or os.environ.get("FEISHU_SECRET")

    if not args.dry_run and not webhook_url:
        print("[Error] 未配置飞书 Webhook URL！", file=sys.stderr)
        print("请在 .env 中设置 FEISHU_WEBHOOK_URL 或在命令行中传入 --webhook 参数。", file=sys.stderr)
        print("若仅测试卡片内容生成，可使用 --dry-run 参数。", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 正在拉取 AIHOT 资讯 (mode={args.mode}, window={args.window}, limit={args.limit})...")
    items = fetch_aihot_items(mode=args.mode, window=args.window, limit=args.limit)
    if not items:
        print("[Warning] 未获取到资讯条目，跳过推送。")
        sys.exit(0)

    print(f"[*] 成功获取到 {len(items)} 条资讯，正在构建飞书卡片...")
    card_payload = build_feishu_card(items, mode=args.mode, window=args.window)

    if args.dry_run:
        print("\n=== [Dry Run 演练模式] 飞书卡片 Payload ===")
        print(json.dumps(card_payload, indent=2, ensure_ascii=False))
        print("\n演练完成，卡片格式有效。")
        return

    print("[*] 正在推送到飞书群...")
    success = send_to_feishu(webhook_url, card_payload, secret=secret)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
