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

# /m コマンド（コマンド実行時にロールやユーザーを選択可能）
@bot.tree.command(name="m", description="テキスト、埋め込み、投票をフリーズなしで最速・安全に送信します")
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

    # 1. 安全のために保留（考え中...を開始）
    await interaction.response.defer(thinking=True)

    # 📝 メンション文字列を自動生成（@everyone ＋ 選択されたロール ＋ 選択されたユーザー）
    mention_strs = ["@everyone"]
    if target_role:
        mention_strs.append(target_role.mention)
    if target_user:
        mention_strs.append(target_user.mention)
    
    all_mentions_text = " ".join(mention_strs)

    # 📝 通常テキスト用の1ブロック文字列定義
    single_block = f"**さーもん万歳！いますぐさーもんの集いに参加！** {all_mentions_text} https://sus5.netlify.app/#SamonAtumai \n\n"
    
    heavy_content = ""
    while len(heavy_content) + len(single_block) < 1950:
        heavy_content += single_block

    # 📈 埋め込み（Embed）の構築
    embed_block = "**さーもんの集いはあなたを歓迎します！**\n極上のさーもん体験を今すぐここで。逃す手はありません！\n\n"
    embed_description = ""
    while len(embed_description) + len(embed_block) < 2000:
        embed_description += embed_block

    embed = discord.Embed(
        title="🐟 【超重大】 さーもん万歳通知 🐟",
        description=embed_description,
        color=discord.Color.from_rgb(255, 111, 97)
    )
    embed.set_author(name="さーもん公式プロモーター")
    embed.set_footer(text="さーもんの集い © 2026")

    # 全てのメンション（everyone, roles, users）を有効化
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    # 2. 1通目（Embed＋長文テキスト）送信
    try:
        await interaction.followup.send(
            content=heavy_content,
            embed=embed,
            allowed_mentions=mention_setting
        )
        print("✅ 1通目を送信完了")
    except Exception as e:
        print(f"❌ 1通目の送信に失敗: {e}")
        return

    # 3. 追加送信（レートリミット対策で1.5秒空ける）
    target_followups = 2
    for i in range(target_followups):
        await asyncio.sleep(1.5)
        try:
            await interaction.followup.send(
                content=heavy_content, 
                allowed_mentions=mention_setting
            )
            print(f"✅ 追加メッセージ送信完了 ({i+1}/{target_followups})")
        except Exception as e:
            print(f"❌ 送信エラー (追加 {i+1}回目): {e}")

    # 4. 最後に投票を送信
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

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN が設定されていません！")
    bot.run(token)
