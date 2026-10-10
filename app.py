import os
import threading
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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Logged in as {bot.user}")

# 投票オブジェクトを作成するヘルパー関数（エラー対策済み）
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=1  # 1時間に設定 (数値または対応する指定)
    )
    poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
    poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
    return poll

# /m コマンド（画像と投票を同時に送信）
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
    # 3秒タイムアウトを防ぐため先に応答を保留する
    await interaction.response.defer(thinking=True)

    content_text = "@everyone サーモンの集い！！さーもん万歳！"

    # 送信したい画像ファイルのリスト
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 回数分だけメッセージを送信
    for i in range(count):
        poll_obj = create_salmon_poll(text)
        files_obj = [discord.File(f) for f in existing_files] if existing_files else []

        try:
            if files_obj:
                if i == 0:
                    await interaction.followup.send(content=content_text, poll=poll_obj, files=files_obj)
                else:
                    await interaction.channel.send(content=content_text, poll=poll_obj, files=files_obj)
            else:
                if i == 0:
                    await interaction.followup.send(content=content_text, poll=poll_obj)
                else:
                    await interaction.channel.send(content=content_text, poll=poll_obj)
        except Exception as e:
            print(f"送信エラー: {e}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
