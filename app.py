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
# ★ 対策1: コマンドの実行を許可する「ロール名」
# この名前のロールをサーバー内で持っているユーザーなら実行可能になります
ALLOWED_ROLE_IDS = [
    1566113401028223248  # ← 許可したいロールのIDに書き換えてください
]
# ★ 対策2: コマンドの実行を「絶対に」許可するユーザーID（バックアップ用）
# ロールを持っていなくても、ここにIDがある人は常に実行できます
ALLOWED_USER_IDS = [
    1488072800278413500  # ← あなたのDiscordユーザーIDに書き換えてください
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

@bot.tree.command(name="m", description="長文メッセージと投票を大量かつ安全に連続送信します")
@app_commands.allowed_installs(guilds=True, users=True)  # 自衛用として他サーバーでも使うためTrueのまま
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    text="投票のタイトルと一緒に送るメッセージ",
    target_role="同時にメンションしたいロール（任意）",
    target_user="同時にメンションしたいユーザー（任意）"
)
async def send_m(
    interaction: discord.Interaction, 
    text: str = "さーもん万歳！",
    target_role: discord.Role = None,
    target_user: discord.Member = None
):
    # ----------------- ホワイトリスト検証（ID版） -----------------
    is_allowed = False

    # 1. ユーザーIDが直接許可されているかチェック
    if interaction.user.id in ALLOWED_USER_IDS:
        is_allowed = True

    # 2. 実行したユーザーが許可されたロールIDを持っているかチェック
    elif isinstance(interaction.user, discord.Member):
        # ユーザーが持っているロールのIDリストを取得
        user_role_ids = [role.id for role in interaction.user.roles]
        
        # ユーザーのロールIDと、許可されたロールIDに1つでも重なりがあるか判定
        if any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids):
            is_allowed = True

    # 許可されていない場合は即座に拒否
    if not is_allowed:
        await interaction.response.send_message(
            "⚠️ 権限エラー: 許可されたロールIDを所持していないため、このコマンドは実行できません。", 
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

    # 保留開始
    await interaction.response.defer(thinking=True)

    mention_strs = ["@everyone"]
    if target_role:
        mention_strs.append(target_role.mention)
    if target_user:
        mention_strs.append(target_user.mention)
    all_mentions_text = " ".join(mention_strs)

    base_msg = f"{all_mentions_text} **さーもんの集いに今すぐ参加！さーもん万歳！！** https://sus5.netlify.app/#SamonAtumai \n"
    heavy_content = ""
    while len(heavy_content) + len(base_msg) <= 1995:
        heavy_content += base_msg

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    TOTAL_MESSAGE_COUNT = 4 

    for i in range(TOTAL_MESSAGE_COUNT):
        try:
            if i > 0:
                await asyncio.sleep(1.2)
            await interaction.followup.send(
                content=heavy_content,
                allowed_mentions=mention_setting
            )
            print(f"✅ 長文メッセージ送信成功 ({i+1}/{TOTAL_MESSAGE_COUNT})")
        except Exception as e:
            print(f"❌ メッセージ送信エラー ({i+1}回目): {e}")

    # 最後に投票を送信
    await asyncio.sleep(1.2)
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
    bot.run(token)
