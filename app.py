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
@bot.tree.command(name="m", description="画像と投票を同時に送信します")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="投票のタイトルや画像と一緒に送るメッセージ")
async def send_m(interaction: discord.Interaction, text: str = "さーもん万歳！"):
    # 最初のレスポンスを保留（通知のぐるぐるを表示）
    await interaction.response.defer(thinking=True)

    content_text = "@everyone サーモンの集い！！さーもん万歳！"
    mention_setting = discord.AllowedMentions(everyone=True, users=True, roles=True)

    image_files = ["acc4d0a0.gif", "a62e0a5b.gif"]
    existing_files = [f for f in image_files if os.path.exists(f)]

    target_count = 150
    success_count = 0
    failed_count = 0
    last_error = None

    # 💡 大量送信用のWebhookをチャンネル内から確保・作成する
    webhook = None
    try:
        channel = interaction.channel
        if channel is None and interaction.channel_id:
            channel = bot.get_channel(interaction.channel_id)

        # サーバーのテキストチャンネルである場合、Webhookを利用可能
        if channel and isinstance(channel, discord.TextChannel):
            webhooks = await channel.webhooks()
            # 既存のBot用Webhookがあれば再利用、なければ作成
            webhook = next((w for w in webhooks if w.name == "SalmonWebhook"), None)
            if not webhook:
                webhook = await channel.create_webhook(name="SalmonWebhook")
    except Exception as wh_err:
        print(f"Webhook取得/作成エラー (通常の送信に切り替えます): {wh_err}")

    # 1回目の送信（コマンドへの応答として必須の処理）
    try:
        files_obj = [discord.File(f) for f in existing_files] if existing_files else []
        if files_obj:
            await interaction.followup.send(content=content_text, files=files_obj, allowed_mentions=mention_setting)
        else:
            await interaction.followup.send(content=content_text, allowed_mentions=mention_setting)
        
        poll_obj = create_salmon_poll(text)
        await interaction.followup.send(poll=poll_obj)
        success_count += 1
    except Exception as first_err:
        print(f"最初のfollowup送信でエラー: {first_err}")
        return

    # 2回目以降のループ（WebhookまたはChannel直接送信を使い分け）
    for i in range(1, target_count):
        try:
            files_obj = [discord.File(f) for f in existing_files] if existing_files else []
            poll_obj = create_salmon_poll(text)

            # A. Webhookが使える場合（最も制限に強い）
            if webhook:
                if files_obj:
                    await webhook.send(content=content_text, files=files_obj, allowed_mentions=mention_setting, username="サーモンの集いBot")
                else:
                    await webhook.send(content=content_text, allowed_mentions=mention_setting, username="サーモンの集いBot")
                await webhook.send(poll=poll_obj, username="サーモンの集いBot")

            # B. Webhookが使えず、Botがチャンネルを取得できている場合（通常メッセージ送信）
            elif channel:
                if files_obj:
                    await channel.send(content=content_text, files=files_obj, allowed_mentions=mention_setting)
                else:
                    await channel.send(content=content_text, allowed_mentions=mention_setting)
                await channel.send(poll=poll_obj)

            # C. どちらもダメな場合のフォールバック（エラー上限までfollowupで粘る）
            else:
                if files_obj:
                    await interaction.followup.send(content=content_text, files=files_obj, allowed_mentions=mention_setting)
                else:
                    await interaction.followup.send(content=content_text, allowed_mentions=mention_setting)
                await interaction.followup.send(poll=poll_obj)

            success_count += 1
            
            # 🚨 150回もの連投でDiscordから規制（BAN）されないよう、適切な待機時間を挟む
            await asyncio.sleep(0.6)

        except Exception as e:
            print(f"送信エラー (ループ {i+1}回目): {e}")
            failed_count += 1
            last_error = e
            
            # レートリミット（速度制限）を検知した場合は少し長めに眠る
            if "429 Too Many Requests" in str(e) or "rate limited" in str(e).lower():
                await asyncio.sleep(3.0)
            # 致命的な拒否エラーはループを抜ける
            elif "403 Forbidden" in str(e):
                break

    # 最終的な結果を、最初のインタラクションのログとしてひっそり追加報告
    try:
        await interaction.followup.send(
            f"─── 送信処理終了 ───\n"
            f"・送信完了: {success_count}回\n"
            f"・スキップ/エラー: {failed_count}回"
        )
    except Exception as final_err:
        print(f"最終結果の送信失敗: {final_err}")

# --- 3. 起動処理 ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
