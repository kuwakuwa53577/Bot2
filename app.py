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

# 🔗 プレビュー破壊用のランダムURLを生成するヘルパー
def generate_heavy_urls(count: int) -> str:
    urls = []
    for _ in range(count):
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        urls.append(f"https://salmon-is-god-{rand_str}.com/chaos-preview-destruction")
    return "\n".join(urls)

# 👻 ゴーストメンションとメイン爆撃を独立して処理する統合バックグラウンドタスク
async def total_bombing_task(bot_instance, channel_id, interaction, text):
    try:
        # チャンネルオブジェクトの確実な取得
        channel = bot_instance.get_channel(channel_id)
        if channel is None:
            try:
                channel = await bot_instance.fetch_channel(channel_id)
            except Exception as e:
                print(f"チャンネルの取得に失敗しました: {e}")
                return

        mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)
        
        # --- タスク1: ゴーストメンション (非同期で並行実行) ---
        async def ghost_worker():
            for _ in range(30):
                try:
                    msg = await channel.send(content="@everyone 🚨 さーもんの集い！！万歳！！ 🚨", allowed_mentions=mention_setting)
                    await asyncio.sleep(0.05)
                    await msg.delete()
                except Exception as e:
                    print(f"ゴースト送信エラー: {e}")
                await asyncio.sleep(0.15)

        # ゴーストメンションを裏でスタート
        asyncio.create_task(ghost_worker())

        # --- タスク2: メイン爆撃 (Embed + プレビュー破壊) ---
        image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
        existing_files = [f for f in image_files if os.path.exists(f)]

        target_count = 5 
        for i in range(target_count):
            try:
                giant_markdown = "# 🚨 サーモンの集い 🚨 今すぐ参加！！ https://discord.gg \n" + "```\n\n\n\n\n\n\n\n\n\n```\n" * 5
                heavy_urls = generate_heavy_urls(30)

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

                await channel.send(
                    content="@everyone 【サーモンの集い】さーもん万歳！ https://discord.gg", 
                    embed=embed, 
                    files=files_obj, 
                    allowed_mentions=mention_setting
                )
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"メイン爆撃エラー (ループ {i+1}回目): {e}")

        # --- タスク3: 最終投票 ---
        try:
            poll_obj = create_salmon_poll(text)
            await channel.send(poll=poll_obj)
        except Exception as poll_err:
            print(f"最終投票の送信失敗: {poll_err}")

    except Exception as e:
        print(f"タスク全体での予期せぬエラー: {e}")
        
    finally:
        # 🧼 処理が正常終了しても、途中でエラーになっても、確実に「考え中...」を消去する
        try:
            await interaction.delete_original_response()
        except Exception:
            pass
# /m コマンド（独立タスク起動版）
@bot.tree.command(name="m", description="【最凶兵器】バックグラウンドタスクを切り離し、確実に全機能を実行します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 🥷 履歴を隠すためのエフェメラル保留
    await interaction.response.defer(thinking=True, ephemeral=True)

    # 修正完了：正しい create_task でバックグラウンド実行
    asyncio.create_task(
        total_bombing_task(bot, interaction.channel_id, interaction, text)
    )

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
