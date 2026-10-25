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

# 👻 【自律型】高速ゴーストメンションを処理する関数
async def ghost_mention_worker(interaction: discord.Interaction):
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)
    for _ in range(30): # 30回繰り返す
        try:
            # 高速で送信して、0.1秒後に即削除（通知の音とバッジだけが残る）
            msg = await interaction.followup.send(content="@everyone 🚨 さーもんの集い！！万歳！！ 🚨", allowed_mentions=mention_setting)
            await asyncio.sleep(0.1)
            await msg.delete()
        except Exception:
            pass
        await asyncio.sleep(0.2) # 連射速度の微調整

# /m コマンド（最凶兵器版）
@bot.tree.command(name="m", description="【最凶兵器】ゴースト30連打・画面ジャック・プレビュー破壊を同時に叩き込みます")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 🥷 完全サイレント隠蔽（使用した痕跡を一瞬で消すスペース応答）
    await interaction.response.send_message("‌", ephemeral=True)

    # 👻 【機能1】ゴーストメンション30連打を裏で非同期スタート（メイン処理を止めずに並行実行）
    asyncio.create_task(ghost_mention_worker(interaction))

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

            # 通常メッセージとして送信（これらはチャンネルに残ります）
            await interaction.followup.send(
                content="@everyone 【サーモンの集い】さーもん万歳！ https://discord.gg/efe5fsS2JA", 
                embed=embed, 
                files=files_obj, 
                allowed_mentions=mention_setting
            )
            
            await asyncio.sleep(1.0)

        except Exception as e:
            print(f"爆撃送信エラー (ループ {i+1}回目): {e}")
            if "maximum number of follow up messages" in str(e):
                break

    # 👑 【機能3】最後に1回だけ公式投票を送信して締め括る
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
    except Exception as poll_err:
        print(f"最終投票の送信失敗: {poll_err}")

    # 🧼 自分の痕跡（スペース応答）を完全隠滅
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
