import os
import threading
from datetime import timedelta
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask

# --- 1. Flask（簡易Webサーバー）の設定（Renderのポート対策） ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 2. Discord Botの設定 ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# 投票オブジェクトを作成するヘルパー関数
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=timedelta(hours=1)
    )
    poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
    poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
    return poll

# /m コマンド
@bot.tree.command(name="m", description="画像と投票を同時に送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    count="送信する回数（数字で指定）",
    text="投票のタイトルや画像と一緒に送るメッセージ"
)
async def send_m(
    interaction: discord.Interaction, 
    count: int = 1, 
    text: str = "さーもん万歳！"
):
    await interaction.response.defer(thinking=True)

    content_text = "@everyone サーモンの集い！！さーもん万歳！"

    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    success_count = 0

    try:
        for i in range(count):
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            poll_obj = create_salmon_poll(text)

            # followup.send を使えばチャンネルがNoneになる問題を回避できます
            if i == 0:
                if files_obj:
                    await interaction.followup.send(content=content_text, files=files_obj)
                else:
                    await interaction.followup.send(content=content_text)
                # 投票を送信
                await interaction.followup.send(poll=poll_obj)
            else:
                # 2回目以降は interaction.channel の代わりに followup を継続利用するか、ウェブフック等を使う形にします
                # ここでは安全に followup.send を使って連続送信します
                if files_obj:
                    await interaction.followup.send(content=content_text, files=files_obj)
                else:
                    await interaction.followup.send(content=content_text)
                await interaction.followup.send(poll=poll_obj)

            success_count += 1

    except Exception as e:
        print(f"送信エラー: {e}")
        if success_count == 0:
            try:
                await interaction.followup.send(f"エラーが発生しました: {e}")
            except:
                pass

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
