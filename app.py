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

# 禁止したいIDの設定
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

# 投票オブジェクトを作成するヘルパー関数
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=timedelta(hours=1)
    )
    poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
    poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
    return poll

# /m コマンド（外部アプリ最適化・堅牢版）
@bot.tree.command(name="m", description="指定されたテキスト、画像、投票をエラーなく確実に送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    
    # ⚙️ サーバーブラックリストチェック
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message(
            "⚠️ この場所でのコマンド使用は禁止されています。", 
            ephemeral=True
        )
        return

    # 応答を保留（外部アプリとして正常に処理を受け付けるための必須処理）
    await interaction.response.defer(thinking=True)

    # 送信する指定テキスト
    content_text = "サーモン万歳！いますぐさーもんの集いに参加！ https://discord.gg @everyone"
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    # 使用する画像リスト
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 外部アプリ制限内で最も安定して送りきれる上限回数
    target_count = 4 

    # 1. テキストと画像の送信ループ
    for i in range(target_count):
        try:
            # 毎回新しくdiscord.Fileオブジェクトを定義
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            
            if files_obj:
                await interaction.followup.send(content=content_text, files=files_obj, allowed_mentions=mention_setting)
            else:
                await interaction.followup.send(content=content_text, allowed_mentions=mention_setting)
            
            # APIエラーを完全に回避するための安定した待機インターバル
            await asyncio.sleep(1.5)

        except discord.errors.HTTPException as http_err:
            print(f"Discord API 制限検知 (ループ {i+1}回目): {http_err}")
            break
        except Exception as e:
            print(f"送信エラー (ループ {i+1}回目): {e}")

    # 2. 最後に公式投票を1回送信して締め括る
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
    except discord.errors.HTTPException as poll_err:
        print(f"最終投票の送信に失敗（制限超過）: {poll_err}")
    except Exception as e:
        print(f"投票送信エラー: {e}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
