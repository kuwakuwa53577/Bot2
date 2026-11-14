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

# =================【セキュリティ設定】=================
# コマンドの実行を許可する「ロールID」（Bot参加サーバー用）
ALLOWED_ROLE_IDS = [
    1566113401028223248
]

# コマンドの実行を「絶対に」許可するユーザーID（外部アプリ用）
ALLOWED_USER_IDS = [
    1465268901066838048
]
# =====================================================

# =================【添付ファイル設定】=================
# 一緒に送信したい画像やファイルのファイル名（最大10個・合計25MB以内）
ATTACH_FILES = [
    "acc4d0a0.gif",
    "a62e0a5b.gif",
    "IMG_3948.png",
    "DSC_9262.png",
    "20260913_162130.png",
    "PXL_20261004_095516_336.png"
]
# =====================================================

IGNORE_CHANNEL_IDS = []
IGNORE_GUILD_IDS = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

def create_salmon_poll(question_text: str):
    try:
        poll = discord.Poll(
            question=question_text,
            duration=timedelta(hours=1)
        )
        poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
        poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
        return poll
    except Exception:
        return None

@bot.tree.command(name="m", description="長文メッセージ・複数ファイル・投票を連続送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    text="投票のタイトルと一緒に送るメッセージ",
    target_user="同時にメンションしたいユーザー（任意）"
)
async def send_m(
    interaction: discord.Interaction, 
    text: str = "さーもん万歳！",
    target_user: discord.User = None
):
    # ----------------- ホワイトリスト検証 -----------------
    is_allowed = False

    if interaction.user.id in ALLOWED_USER_IDS:
        is_allowed = True
    elif isinstance(interaction.user, discord.Member):
        user_role_ids = [role.id for role in interaction.user.roles]
        if any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids):
            is_allowed = True

    if not is_allowed:
        await interaction.response.send_message(
            "⚠️ 権限エラー: 実行権限がないため、このコマンドは実行できません。", 
            ephemeral=True
        )
        return
    # ----------------------------------------------------

    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    
    if guild_id and guild_id in IGNORE_GUILD_IDS:
        await interaction.response.send_message("⚠️ このサーバーでのコマンド使用は禁止されています。", ephemeral=True)
        return
    if channel_id and channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ このチャンネルでのコマンド使用は禁止されています。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    mention_strs = ["@everyone"]
    if target_user:
        mention_strs.append(target_user.mention)
    all_mentions_text = " ".join(mention_strs)

    base_msg = f"{all_mentions_text} **さーもんの集いに今すぐ参加！さーもん万歳！！** https://netlify.app \n"
    heavy_content = ""
    while len(heavy_content) + len(base_msg) <= 1995:
        heavy_content += base_msg

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    existing_files = [f for f in ATTACH_FILES if os.path.exists(f)][:10]

    TOTAL_MESSAGE_COUNT = 4 

    for i in range(TOTAL_MESSAGE_COUNT):
        try:
            if i > 0:
                await asyncio.sleep(1.5)

            files_to_send = [discord.File(f) for f in existing_files]

            if files_to_send:
                await interaction.followup.send(
                    content=heavy_content,
                    files=files_to_send,
                    allowed_mentions=mention_setting
                )
            else:
                await interaction.followup.send(
                    content=heavy_content,
                    allowed_mentions=mention_setting
                )
            print(f"✅ メッセージ＆ファイル送信成功 ({i+1}/{TOTAL_MESSAGE_COUNT})")

        except discord.errors.HTTPException as http_err:
            print(f"❌ Discord制限超過またはファイル容量オーバー ({i+1}回目): {http_err}")
            break
        except Exception as e:
            print(f"❌ 送信エラー ({i+1}回目): {e}")

    await asyncio.sleep(1.5)
    try:
        poll_obj = create_salmon_poll(text)
        if poll_obj:
            await interaction.followup.send(poll=poll_obj)
        else:
            await interaction.followup.send(f"📊 **投票:** {text}")
        print("✅ 最終投票の送信が完了しました！")
    except Exception as poll_err:
        print(f"❌ 最終投票の送信失敗: {poll_err}")

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN が設定されていません！")
    else:
        bot.run(token)
