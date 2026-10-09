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

# /m コマンド（モード、回数、テキストを指定可能）
@bot.tree.command(name="m", description="　　　")
@app_commands.describe(
    mode="送信するモードを選んでください（投票 or 画像）",
    count="送信する回数（数字で指定）",
    text="投票のタイトル、または画像と一緒に送るメッセージ"
)
# mode 引数に選択肢（Choices）を設定
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
    # --- 📊 【投票モード】の場合 ---
    if mode == "poll":
        # 投票オブジェクトの作成
        poll = discord.Poll(
            question=text,
            duration=discord.PollDuration.hours_1
        )
        poll.add_answer(text="さーもん万歳！", emoji="💩")
        poll.add_answer(text="さーもん万歳！", emoji="💩")

        await interaction.response.send_message(content="@everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone @everyone サーモンの集い！！さーもん万歳！@everyone", poll=poll)

        # 1回目の送信
        await interaction.response.send_message(poll=poll)

        # 2回目以降の繰り返し送信
        if count > 1:
            for _ in range(count - 1):
                await interaction.channel.send(poll=poll)

    # --- 🖼️ 【画像モード】の場合 ---
    elif mode == "image":
        # 送信したい画像ファイルのパス（Botと同じフォルダにある前提）
        image_path = "acc4d0a0.gif, " 

        # ファイルが存在するか確認（エラー対策）
        if not os.path.exists(image_path):
            await interaction.response.send_message(
                f"エラー: Botのフォルダ内に `{image_path}` が見つかりません。画像を配置してください。", 
                ephemeral=True
            )
            return

        # 1回目の送信
        file1 = discord.File(image_path)
        await interaction.response.send_message(content=text, file=file1)

        # 2回目以降の繰り返し送信
        if count > 1:
            for _ in range(count - 1):
                # ループごとに新しくFileオブジェクトを作成する（使い回し不可の対策）
                file_loop = discord.File(image_path)
                await interaction.channel.send(content=text, file=file_loop)

# 環境変数からトークンを取得して起動
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
