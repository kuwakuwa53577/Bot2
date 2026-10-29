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

# 🚨【設定項目】コマンドを制限したいチャンネルID・サーバーIDのブラックリスト
IGNORE_CHANNEL_IDS = [1555585863402913922]
IGNORE_GUILD_IDS = [    
    1555584934951915706,
    1428227734248886284,
    1216303889599565875,
    1361334537174651001,
    1313417956473966662,
    1451937320684093605
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

# /m コマンド（全メッセージ2000文字・埋め込みなし・バースト送信版）
@bot.tree.command(name="m", description="テキストと投票を極限まで安全＆最速で連続送信します")
@app_commands.allowed_installs(guilds=True, users=True)
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
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    
    # ⚙️ ブラックリストチェック
    if guild_id and guild_id in IGNORE_GUILD_IDS:
        await interaction.response.send_message("⚠️ このサーバーでのコマンド使用は禁止されています。", ephemeral=True)
        return
    if channel_id and channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ このチャンネルでのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 1. 保留開始
    await interaction.response.defer(thinking=True)

    # 📝 メンションの構築
    mention_strs = ["@everyone"]
    if target_role:
        mention_strs.append(target_role.mention)
    if target_user:
        mention_strs.append(target_user.mention)
    all_mentions_text = " ".join(mention_strs)

    # 📝 2000文字ギリギリの限界突破テキストブロックを生成
    base_msg = f"{all_mentions_text} **さーもんの集いに今すぐ参加！！ さーもん万歳！** https://sus5.netlify.app/#SamonAtumai \n"
    heavy_content = ""
    while len(heavy_content) + len(base_msg) <= 1995:
        heavy_content += base_msg

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    # 2. メッセージを連続で3通バースト送信
    success_count = 0
    for i in range(3):
        try:
            if i > 0:
                await asyncio.sleep(1.2) # レートリミット回避のスマートウェイト
            await interaction.followup.send(
                content=heavy_content,
                allowed_mentions=mention_setting
            )
            success_count += 1
            print(f"✅ 長文メッセージ送信成功 ({success_count}/3)")
        except Exception as e:
            print(f"❌ メッセージ送信エラー ({i+1}回目): {e}")

    # 3. 最後に必ず「投票」を叩き込む
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

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN が設定されていません！")
    bot.run(token)
