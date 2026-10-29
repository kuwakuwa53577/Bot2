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

# 🚨【設定項目】コマンドを制限したいID
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
def create_salmon_poll(question_text: str) -> discord.Poll:
    poll = discord.Poll(
        question=question_text,
        duration=timedelta(hours=1)
    )
    poll.add_answer(text="さーもん万歳！(1)", emoji="💩")
    poll.add_answer(text="さーもん万歳！(2)", emoji="🐟")
    return poll

# /m コマンド（エラー回避・外部アプリ完全最適化版）
@bot.tree.command(name="m", description="テキスト、埋め込み、画像、投票をエラーなしで安全に連続送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    # ⚙️ ブラックリストチェック
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 1. 最初に保留（これでシステム上のエラーを確実に防ぐ）
    await interaction.response.defer(thinking=True)

    # 📝 通常テキスト用の1ブロック文字列定義（太字装飾つき）
    single_block = "**さーもん万歳！いますぐさーもんの集いに参加！** https://netlify.app @everyone \n\n"
    
    # 💡 Discordの最大仕様（2000文字）を超えないように安全にテキストを構築
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
        color=discord.Color.from_rgb(255, 111, 97) # サーモンピンク
    )
    embed.set_author(name="さーもん公式プロモーター")
    embed.set_footer(text="さーもんの集い © 2026")

    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    # 画像リストの確認
    image_files = ["acc4d0a0.gif", "a62e0a5b.gif", "IMG_3948.png", "DSC_9262.png", "20260913_162130.png", "PXL_20261004_095516_336.png"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    # 2. 保留直後に1通目を送信（これで『考え中...』のぐるぐるが即座に消えます！）
    try:
        files_obj = [discord.File(f) for f in existing_files] if existing_files else []
        await interaction.followup.send(
            content=heavy_content,
            embed=embed,
            files=files_obj,
            allowed_mentions=mention_setting
        )
        print("✅ 1通目を送信完了（『考え中...』を解除しました）")
    except Exception as e:
        print(f"❌ 1通目の送信に失敗: {e}")
        return

    # 外部アプリのレートリミットを回避するため、安全に2回追加送信（合計3通のテキスト＆画像）
    target_followups = 2
    for i in range(target_followups):
        await asyncio.sleep(1.5) # 連投規制を避けるための安全な待機
        try:
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            await interaction.followup.send(
                content=heavy_content, 
                files=files_obj, 
                allowed_mentions=mention_setting
            )
            print(f"✅ 追加メッセージ送信完了 ({i+1}/{target_followups})")
        except discord.errors.HTTPException as http_err:
            print(f"❌ Discord APIエラー (追加 {i+1}回目): {http_err.text}")
        except Exception as e:
            print(f"❌ 送信エラー (追加 {i+1}回目): {e}")

    # 3. 最後に「投票」を確実に送信して綺麗に締めくくる
    await asyncio.sleep(1.5)
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
        print("✅ 最終投票の送信が完了しました！")
    except Exception as poll_err:
        print(f"❌ 最終投票の送信失敗: {poll_err}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
