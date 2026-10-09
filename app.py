import os
import discord
from discord.ext import commands
from discord import app_commands

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

# 送信用のヘルパー関数（Pollを作成する）
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=discord.PollDuration.hours_1
    )
    # 選択肢のテキストや絵文字は重複させないように変更
    poll.add_answer(text="さーもん万歳！", emoji="💩")
    poll.add_answer(text="ｻｰﾓﾝ万歳！", emoji="🐶")
    return poll


# /m コマンド（モード、回数、テキストを指定可能）
@bot.tree.command(name="m", description="       ")
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
    # 送信文面の設定（メンションなど）
    content_text = "@everyone サーモンの集い！！さーもん万歳！"

    # --- 📊 【投票モード】の場合 ---
    if mode == "poll":
        # 1回目の送信（コマンドへの返答）
        poll1 = create_salmon_poll(text)
        await interaction.response.send_message(content=content_text, poll=poll1)

        # 2回目以降の繰り返し送信
        if count > 1:
            for _ in range(count - 1):
                poll_loop = create_salmon_poll(text)
                await interaction.channel.send(content=content_text, poll=poll_loop)

    # --- 🖼️ 【画像モード】の場合 ---
    elif mode == "image":
        # 送信したい画像ファイル名のリスト
        image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]

        # 存在するファイルのみをフィルタリングして読み込む
        existing_files = [f for f in image_files if os.path.exists(f)]

        if not existing_files:
            await interaction.response.send_message(
                f"エラー: 画像ファイル ({', '.join(image_files)}) が見つかりません。ファイルを配置してください。", 
                ephemeral=True
            )
            return

        # 1回目の送信
        files1 = [discord.File(f) for f in existing_files]
        await interaction.response.send_message(content=text, files=files1)

        # 2回目以降の繰り返し送信
        if count > 1:
            for _ in range(count - 1):
                files_loop = [discord.File(f) for f in existing_files]
                await interaction.channel.send(content=text, files=files_loop)

# 環境変数からトークンを取得して起動
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
