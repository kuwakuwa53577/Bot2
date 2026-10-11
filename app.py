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

# /m コマンド
@bot.tree.command(name="m", description="最適なチャンネルを自動選択して画像と投票を150回送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルや画像と一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    # 最初のレスポンスを保留
    await interaction.response.defer(thinking=True)

    content_text = "@everyone サーモンの集い！！さーもん万歳！"
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    target_count = 150
    success_count = 0
    failed_count = 0
    last_error = None

    # 💡 コマンドが実行されたサーバー内のすべてのテキストチャンネルから、最適なチャンネルを自動検索
    target_channel = None
    if interaction.guild:
        for channel in interaction.guild.text_channels:
            perms = channel.permissions_for(interaction.guild.me)
            # 「メッセージ送信」と「@everyoneメンション」の両方の権限があるチャンネルを最優先
            if perms.send_messages and perms.mention_everyone:
                target_channel = channel
                break
        
        # もし両方満たすチャンネルがなければ、「メッセージ送信」ができるチャンネルを fallback
        if target_channel is None:
            for channel in interaction.guild.text_channels:
                perms = channel.permissions_for(interaction.guild.me)
                if perms.send_messages:
                    target_channel = channel
                    break

    # サーバー外（DMなど）で実行された場合は、現在のチャンネルをそのまま使用
    if target_channel is None:
        target_channel = interaction.channel
        if target_channel is None and interaction.channel_id:
            target_channel = bot.get_channel(interaction.channel_id)

    # チャンネルが1つも見つからなかった場合のガード
    if target_channel is None:
        await interaction.followup.send("送信可能なチャンネルが見つかりませんでした。")
        return

    print(f"送信先チャンネルを自動決定しました: #{target_channel.name}")

    # 💡 大量送信用のWebhookを自動確保・作成する（最大数エラーを確実に回避するため）
    webhook = None
    if isinstance(target_channel, discord.TextChannel):
        try:
            webhooks = await target_channel.webhooks()
            webhook = next((w for w in webhooks if w.name == "SalmonWebhook"), None)
            if not webhook:
                webhook = await target_channel.create_webhook(name="SalmonWebhook")
        except Exception as wh_err:
            print(f"Webhook作成スキップ (通常送信を行います): {wh_err}")

    # 1回目の送信（コマンドへの応答として必須の処理）
    try:
        files_obj = [discord.File(f) for f in existing_files] if existing_files else []
        if files_obj:
            await interaction.followup.send(content=f"送信を開始します！送信先: {target_channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send(content=f"送信を開始します！送信先: {target_channel.mention}", ephemeral=True)
    except Exception as first_err:
        print(f"最初の応答送信でエラー: {first_err}")

    # 150回の自動ループ処理
    for i in range(target_count):
        try:
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            poll_obj = create_salmon_poll(text)

            # パターンA: Webhookが使える場合（速度制限に最も強く、おすすめ）
            if webhook:
                if files_obj:
                    await webhook.send(content=content_text, files=files_obj, allowed_mentions=mention_setting, username="サーモンの集いBot")
                else:
                    await webhook.send(content=content_text, allowed_mentions=mention_setting, username="サーモンの集いBot")
                await webhook.send(poll=poll_obj, username="サーモンの集いBot")

            # パターンB: 通常のチャンネル直接送信
            else:
                if files_obj:
                    await target_channel.send(content=content_text, files=files_obj, allowed_mentions=mention_setting)
                else:
                    await target_channel.send(content=content_text, allowed_mentions=mention_setting)
                await target_channel.send(poll=poll_obj)

            success_count += 1
            
            # 連投によるDiscordからのペナルティ（制限）を回避するために、0.6秒待機
            await asyncio.sleep(0.6)

        except Exception as e:
            print(f"送信エラー (ループ {i+1}回目): {e}")
            failed_count += 1
            last_error = e
            
            # 速度制限（429）を検知した場合は少し長めにスリープ
            if "429 Too Many Requests" in str(e) or "rate limited" in str(e).lower():
                await asyncio.sleep(4.0)
            # 権限が途中で剥がされた場合はループを抜ける
            elif "403 Forbidden" in str(e):
                break

    # 完了報告
    print(f"処理終了。成功: {success_count}回, 失敗: {failed_count}回")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
