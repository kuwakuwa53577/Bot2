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
IGNORE_CHANNEL_IDS =
IGNORE_GUILD_IDS =

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

# /m コマンド（高負荷エラー完全排除版）
@bot.tree.command(name="m", description="テキスト、埋め込み、投票をフリーズなしで最速・安全に送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    # ⚙️ ブラックリストチェック
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 1. 安全のために保留（考え中...を開始）
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

    # 2. 【超重要】保留直後に1通目を即座に送信（これで確実に『考え中...』が画面から消えます）
    try:
        await interaction.followup.send(
            content=heavy_content,
            embed=embed,
            allowed_mentions=mention_setting
        )
        print("✅ 1通目を送信完了（『考え中...』が消えました）")
    except Exception as e:
        print(f"❌ 1通目の送信に失敗: {e}")
        return

    # 外部アプリのレートリミット（連投規制）をすり抜けるため、安全に2回追加送信（合計3通）
    target_followups = 2
    for i in range(target_followups):
        await asyncio.sleep(1.0) # 1秒の短いインターバル
        try:
            await interaction.followup.send(
                content=heavy_content, 
                allowed_mentions=mention_setting
            )
            print(f"✅ 追加メッセージ送信完了 ({i+1}/{target_followups})")
        except discord.errors.HTTPException as http_err:
            print(f"❌ Discord APIエラー (追加 {i+1}回目): {http_err.text}")
        except Exception as e:
            print(f"❌ 送信エラー (追加 {i+1}回目): {e}")

    # 3. 最後に「投票」を確実に送信して終了
    await asyncio.sleep(1.0)
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
