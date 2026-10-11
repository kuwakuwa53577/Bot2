import os
import threading
from datetime import timedelta
import asyncio
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

# 🚨【設定項目①】コマンドを禁止したい「チャンネルID」
IGNORE_CHANNEL_IDS = [
    1555585863402913922  # 禁止したいチャンネルのID
]

# 🚨【設定項目②】コマンドを禁止したい「サーバーID」
IGNORE_GUILD_IDS = [
    1555584934951915706  # 無効化したいサーバーのID
]

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

# /m コマンド（他人のサーバー用：外部アプリの限界火力版）
@bot.tree.command(name="m", description="画像と投票、大量のメンションと招待URLを限界まで送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルや画像と一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    # ⚙️ サーバーブラックリストチェック
    if interaction.guild_id in IGNORE_GUILD_IDS:
        await interaction.response.send_message(
            "⚠️ このサーバーでは `/m` コマンドの使用が禁止されています。", 
            ephemeral=True
        )
        return

    # ⚙️ チャンネルブラックリストチェック
    if interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message(
            "⚠️ このチャンネルでは `/m` コマンドの使用が禁止されています。", 
            ephemeral=True
        )
        return

    # 最初のレスポンスを保留
    await interaction.response.defer(thinking=True)

    # 招待URLを含んだ巨大テキスト
    single_block = "@everyone サーモンの集い！！さーもん万歳！ https://discord.gg/cnuTJgd3Jx \n\n"
    heavy_content = single_block * 24 

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    # あなたが追加してくれたお気に入りの画像リスト
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    
    # Render内に実際に存在するファイルだけをあらかじめ絞り込む
    existing_files = [f for f in image_files if os.path.exists(f)]

    target_count = 5 

    for i in range(target_count):
        try:
            # 💡 ループのたびに新しく discord.File オブジェクトを生成し直す（重要）
            # これにより、5回とも安定して全画像が送信されます
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            
            if files_obj:
                await interaction.followup.send(content=heavy_content, files=files_obj, allowed_mentions=mention_setting)
            else:
                await interaction.followup.send(content=heavy_content, allowed_mentions=mention_setting)
            
            # 画像が6枚と多いため、Discordに負荷をかけないよう待機時間を少し長め（1.2秒）に調整
            await asyncio.sleep(1.2)

        except Exception as e:
            print(f"爆撃送信エラー (ループ {i+1}回目): {e}")
            if "maximum number of follow up messages" in str(e):
                break

    # 最後に1回だけ投票を送信
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
    except Exception as poll_err:
        print(f"最終投票の送信失敗: {poll_err}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
