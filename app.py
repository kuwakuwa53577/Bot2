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

# 環境に合わせてIDを設定してください
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

def generate_heavy_urls(count: int) -> str:
    urls = []
    for _ in range(count):
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        urls.append(f"https://salmon-is-god-{rand_str}.com/chaos-preview-destruction")
    return "\n".join(urls)

# /m コマンド（シーケンス最適化版）
@bot.tree.command(name="m", description="順序を制御し、レートリミットを回避しながら各機能を実行します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 応答の保留
    await interaction.response.defer(thinking=True, ephemeral=True)

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 1. ゴーストメンション（回数を調整し、直列に実行）
    # レートリミットを考慮し、外部アプリでの現実的な回数（例: 5回）に調整して確実に実行します
    for _ in range(5):
        try:
            ghost_msg = await interaction.followup.send(content="@everyone 🚨 さーもんの集い！！万歳！！ 🚨", allowed_mentions=mention_setting)
            await asyncio.sleep(0.5)  # 削除前に少し待機してAPIの重複を避ける
            await ghost_msg.delete()
            await asyncio.sleep(1.0)  # 次の送信までのインターバル
        except discord.errors.HTTPException as e:
            print(f"ゴースト送信スキップ（制限回避）: {e}")
            await asyncio.sleep(2.0)
        except Exception:
            pass

    # 2. メイン爆撃（Embed + プレビュー破壊）
    # 外部アプリの制限内で確実に届くよう回数を調整
    for i in range(2):
        try:
            giant_markdown = "# 🚨 サーモンの集い 🚨 今すぐ参加！！ https://discord.gg \n" + "```\n\n\n\n\n\n\n\n\n\n```\n" * 2
            heavy_urls = generate_heavy_urls(10)  # URLの数を調整して負荷を軽減

            embed = discord.Embed(
                title="🚨 さーもん！ 🚨 さーもん万歳！！！", 
                description=f"{giant_markdown}\n\n{heavy_urls}", 
                color=0xFF0033 
            )
            
            files_obj = []
            if existing_files:
                chosen_image = existing_files[i % len(existing_files)]
                files_obj.append(discord.File(chosen_image, filename=chosen_image))
                embed.set_image(url=f"attachment://{chosen_image}")

            await interaction.followup.send(
                content="@everyone 【サーモンの集い】さーもん万歳！ https://discord.gg", 
                embed=embed, 
                files=files_obj, 
                allowed_mentions=mention_setting
            )
            await asyncio.sleep(2.0)  # レートリミット回避のための十分なインターバル

        except Exception as e:
            print(f"メイン爆撃エラー (ループ {i+1}回目): {e}")
            await asyncio.sleep(3.0)

    # 3. 最終投票
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
    except Exception as poll_err:
        print(f"最終投票の送信失敗: {poll_err}")

    # 保留メッセージの消去
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
