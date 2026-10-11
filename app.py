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

# /m コマンド
@bot.tree.command(name="m", description="画像と投票を同時に送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルや画像と一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    # 最初のレスポンスを保留（15分間インタラクションが維持されます）
    await interaction.response.defer(thinking=True)

    content_text = "@everyone サーモンの集い！！さーもん万歳！"
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    target_count = 150
    success_count = 0
    failed_count = 0
    last_error = None

    for i in range(target_count):
        try:
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            poll_obj = create_salmon_poll(text)

            # 💡 1回目も2回目以降も、すべて interaction.followup を使用して送信
            if files_obj:
                await interaction.followup.send(content=content_text, files=files_obj, allowed_mentions=mention_setting)
            else:
                await interaction.followup.send(content=content_text, allowed_mentions=mention_setting)
            
            await interaction.followup.send(poll=poll_obj)

            success_count += 1
            
            # 連投によるDiscordへの負荷（レートリミット）を避けるため、一瞬待機
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"送信エラー (ループ {i+1}回目): {e}")
            failed_count += 1
            last_error = e
            # 完全に拒否された場合はループを抜ける
            if "403 Forbidden" in str(e):
                break

    # 最終報告
    try:
        if failed_count > 0:
            await interaction.followup.send(
                f"送信完了（一部エラーあり）\n"
                f"・成功: {success_count}回 / 失敗: {failed_count}回\n"
                f"※最後のエラー内容: {last_error}"
            )
        else:
            await interaction.followup.send(f"すべての送信（{success_count}回）が正常に完了しました！")
    except Exception as final_err:
        print(f"結果報告の送信に失敗: {final_err}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
