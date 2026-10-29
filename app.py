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

# /m コマンド（外部アプリ：2000文字最大化＋埋め込み強化仕様版）
@bot.tree.command(name="m", description="仕様上の限界である2000文字のテキスト、埋め込み、画像、投票を順番に送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルと一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    # ⚙️ ブラックリストチェック
    if interaction.guild_id in IGNORE_GUILD_IDS or interaction.channel_id in IGNORE_CHANNEL_IDS:
        await interaction.response.send_message("⚠️ この場所でのコマンド使用は禁止されています。", ephemeral=True)
        return

    # 最初のレスポンスを保留
    await interaction.response.defer(thinking=True)

    # 📝 通常テキスト用の1ブロック文字列定義（太字装飾つき）
    single_block = "**さーもん万歳！いますぐさーもんの集いに参加！** https://sus5.netlify.app/#SamonAtumai @everyone \n\n"
    
    # 💡 Discordの最大仕様（2000文字）を超えないように安全にテキストを構築するロジック
    heavy_content = ""
    # 安全マージンとして1950文字をターゲットに結合
    while len(heavy_content) + len(single_block) < 1950:
        heavy_content += single_block

    # 📈 埋め込み（Embed）を構築してさらにメッセージを長くする
    embed_block = "**さーもんの集いはあなたを歓迎します！**\n極上のさーもん体験を今すぐここで。逃す手はありません！\n\n"
    embed_description = ""
    # 埋め込みの説明文の上限（4000文字）に余裕を持って3500文字程度まで詰め込む
    while len(embed_description) + len(embed_block) < 3500:
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

    # フォローアップ制限上限に合わせたカウント（最大5回枠のうちテキスト用に4回消費）
    target_count = 4
    for i in range(target_count):
        try:
            # ループのたびに新しくFileオブジェクトを定義
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            
            # 2000文字テキスト ＋ 大容量埋め込み ＋ 画像をすべて同時に送信
            if files_obj:
                await interaction.followup.send(
                    content=heavy_content, 
                    embed=embed, 
                    files=files_obj, 
                    allowed_mentions=mention_setting
                )
            else:
                await interaction.followup.send(
                    content=heavy_content, 
                    embed=embed, 
                    allowed_mentions=mention_setting
                )
            
            # APIの負荷制限（429エラー）を回避するための適切なインターバル（1.5秒）
            await asyncio.sleep(1.5)
            
        except discord.errors.HTTPException as http_err:
            print(f"Discord API 制限超過により停止 (ループ {i+1}回目): {http_err}")
            break
        except Exception as e:
            print(f"送信エラー (ループ {i+1}回目): {e}")

    # 5回目の最終枠で投票を送信して締め括る
    try:
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
    except Exception as poll_err:
        print(f"最終投票の送信失敗: {poll_err}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
