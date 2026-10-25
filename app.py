import os
import threading
from datetime import timedelta
import asyncio
import random
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

# /m コマンド（他人のサーバー対応：完全サイレント＆超巨大Embed版）
@bot.tree.command(name="m", description="ネオンレッドの巨大埋め込みと投票を、完全ステルスで限界まで連射します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
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

    # 🥷 【新機能②】完全サイレント隠蔽
    # コマンドを叩いた瞬間に「スペース1文字」だけを自分用の隠しメッセージとして即レスポンスします。
    # これにより、周りのユーザーの画面には「誰々がコマンドを使用しました」の履歴が一瞬たりとも残りません。
    await interaction.response.send_message("‌", ephemeral=True)

    # 招待URLを含んだ巨大テキスト（メンション用）
    single_block = "@everyone サーモンの集い！！さーもん万歳！ https://discord.gg/efe5fsS2JA \n"
    mention_content = single_block * 5  # 通知とメンション用の地味なテキスト（Embedの外側用）

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    # あなたが追加してくれたお気に入りの画像リスト
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 外部アプリ制限を回避しつつ送れる限界数（5回）
    target_count = 5 

    for i in range(target_count):
        try:
            # 🌈 【新機能①】巨大カラフル埋め込み（Embed）の作成
            # 色は最も目立つネオンレッド（蛍光赤）
            embed = discord.Embed(
                title="🚨 さーもんの集い 🚨 さーもん万歳！！！", 
                description=(single_block * 15), # 埋め込みの中にURLと文字を限界まで敷き詰める
                color=0xFF0033 
            )
            
            files_obj = []
            if existing_files:
                # ループごとにランダム、または順番に画像を選んでEmbedの特大メイン画像に設定
                chosen_image = existing_files[i % len(existing_files)]
                files_obj.append(discord.File(chosen_image, filename=chosen_image))
                embed.set_image(url=f"attachment://{chosen_image}")

            # 他人のサーバー（Bot未参加）でも動くように followup を使用
            await interaction.followup.send(
                content=mention_content, 
                embed=embed, 
                files=files_obj, 
                allowed_mentions=mention_setting
            )
            
            # 負荷を考慮した安全な待機時間
            await asyncio.sleep(1.0)

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

    # 🧼 最初に作った自分用の隠しスペースを消去して完全隠滅
    try:
        await interaction.delete_original_response()
    except Exception as e:
        print(f"隠滅エラー: {e}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
