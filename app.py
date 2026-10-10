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

# 投票オブジェクトを作成するヘルパー関数
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=discord.PollDuration.hours_1
    )
    # 選択肢や絵文字が重複しないように設定
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
    content_text = "@everyone サーモンの集い！！さーもん万歳！"

    # 送信したい画像ファイルのリスト
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # --- 1回目の送信（コマンドへの応答として、画像と投票を同時に送信） ---
    poll1 = create_salmon_poll(text)
    files1 = [discord.File(f) for f in existing_files] if existing_files else []

    if files1:
        # 画像と投票を同時に送る
        await interaction.response.send_message(content=content_text, poll=poll1, files=files1)
    else:
        # 画像ファイルが見つからない場合は投票とテキストのみ送信
        await interaction.response.send_message(content=content_text, poll=poll1)

    # --- 2回目以降の繰り返し送信（countが2以上の場合） ---
    if count > 1:
        for _ in range(count - 1):
            poll_loop = create_salmon_poll(text)
            files_loop = [discord.File(f) for f in existing_files] if existing_files else []
            
            if files_loop:
                await interaction.channel.send(content=content_text, poll=poll_loop, files=files_loop)
            else:
                await interaction.channel.send(content=content_text, poll=poll_loop)

# --- 3. 起動処理 ---
if __name__ == "__main__":
    # Webサーバーを別スレッドで起動
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # Discordボットを起動
    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
