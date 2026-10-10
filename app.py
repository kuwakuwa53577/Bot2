import os
import threading
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
    # Renderが指定するポート（環境変数 PORT）またはデフォルトで8080を使用
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

# /m コマンド（投票・画像送信）
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=discord.PollDuration.hours_1
    )
    poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
    poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
    return poll

@bot.tree.command(name="m", description="メッセージや画像を送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    mode="送信するモードを選んでください（投票 or 画像）",
    count="送信する回数（数字で指定）",
    text="投票のタイトル、または画像と一緒に送るメッセージ"
)
@app_commands.choices(mode=[
    app_commands.Choice(name="📊 投票を送信する", value="poll"),
    app_commands.Choice(name="🖼️ 画像を送信する", value="image")
])
async def send_m(
    interaction: discord.Interaction, 
    mode: str,
    count: int = 1, 
    text: str = "デフォルトのメッセージ"
):
    content_text = "@everyone サーモンの集い！！さーもん万歳！"

    if mode == "poll":
        poll1 = create_salmon_poll(text)
        await interaction.response.send_message(content=content_text, poll=poll1)
        if count > 1:
            for _ in range(count - 1):
                poll_loop = create_salmon_poll(text)
                await interaction.channel.send(content=content_text, poll=poll_loop)

    elif mode == "image":
        image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
        existing_files = [f for f in image_files if os.path.exists(f)]

        if not existing_files:
            await interaction.response.send_message(
                f"エラー: 画像ファイルが見つかりません。", 
                ephemeral=True
            )
            return

        files1 = [discord.File(f) for f in existing_files]
        await interaction.response.send_message(content=text, files=files1)
        if count > 1:
            for _ in range(count - 1):
                files_loop = [discord.File(f) for f in existing_files]
                await interaction.channel.send(content=text, files=files_loop)

# --- 3. 起動処理（WebサーバーとDiscordボットを同時に動かす） ---
if __name__ == "__main__":
    # 別スレッドでWebサーバーを起動（これでRenderのポートスキャンをクリア）
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # Discordボットを起動
    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
