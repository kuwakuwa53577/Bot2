import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
import discord
from discord import app_commands
from discord.ext import commands
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. 開発環境・設定（環境変数）
# ==========================================
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
MEMBER_ROLE_ID = int(os.environ.get("MEMBER_ROLE_ID", "0"))
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS")

# ==========================================
# 2. Firebase Admin SDK の初期化
# ==========================================
if FIREBASE_CREDENTIALS:
    cred_dict = json.loads(FIREBASE_CREDENTIALS)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK の初期化に成功しました")
else:
    print("❌ FIREBASE_CREDENTIALS が設定されていません")

db = firestore.client()

# ==========================================
# 3. Flask アプリケーションの設定
# ==========================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot status: Running"

@app.route("/ping")
def ping():
    # 204 No Content を返してデータ量をゼロにし、Cronなどの出力オーバーエラーを防ぐ
    return "", 204

@app.route("/verify", methods=["POST"])
def verify():
    """Web認証等から呼ばれてロール付与＆FirestoreへIP保存するエンドポイント"""
    data = request.json or {}
    user_id = data.get("user_id")
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    username = data.get("username", "Unknown")
    roles = data.get("roles", [])

    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    # Firestore の verifications コレクションに書き込み
    jst = timezone(timedelta(hours=9))
    now_str = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    doc_ref = db.collection("verifications").document(str(user_id))
    doc_ref.set({
        "ip": user_ip,
        "username": username,
        "roles": roles,
        "updated_at": now_str
    }, merge=True)

    # Discord 側のロール付与処理（非同期タスクとしてバックグラウンド実行）
    if discord_bot.is_ready() and MEMBER_ROLE_ID != 0:
        asyncio.run_coroutine_threadsafe(
            add_role_to_member(int(user_id)),
            discord_bot.loop
        )

    return jsonify({"status": "success", "ip": user_ip}), 200

# ==========================================
# 4. Discord Bot の設定
# ==========================================
intents = discord.Intents.default()
intents.members = True  # PRIVILEGED GATEWAY INTENTS (Developer PortalでON必須)

discord_bot = commands.Bot(command_prefix="!", intents=intents)

async def add_role_to_member(user_id: int):
    """指定ユーザーに指定のロールを付与するヘルパー関数"""
    for guild in discord_bot.guilds:
        member = guild.get_member(user_id)
        if member:
            role = guild.get_role(MEMBER_ROLE_ID)
            if role:
                try:
                    await member.add_roles(role)
                    print(f"✅ {member.display_name} にロールを付与しました")
                except Exception as e:
                    print(f"❌ ロール付与エラー: {e}")

@discord_bot.event
async def on_ready():
    print(f"🤖 Botがログインしました: {discord_bot.user.name}")
    try:
        # スラッシュコマンドの同期
        synced = await discord_bot.tree.sync()
        print(f"🔁 {len(synced)} 個のスラッシュコマンドを同期しました")
    except Exception as e:
        print(f"❌ コマンド同期エラー: {e}")

# ==========================================
# 5. スラッシュコマンド（BAN＆IP公開）
# ==========================================
@discord_bot.tree.command(name="ban_user", description="ユーザーをBANし、登録済みのIPアドレスを表示します")
@app_commands.checks.has_permissions(ban_members=True) # BAN権限を持つ管理者のみ実行可能
async def ban_user(interaction: discord.Interaction, member: discord.Member, reason: str = "規約違反"):
    await interaction.response.defer()

    # 1. Firestore から IP アドレスを取得
    user_doc = db.collection("verifications").document(str(member.id)).get()
    
    if user_doc.exists:
        ip_address = user_doc.to_dict().get("ip", "IP未記録")
    else:
        ip_address = "データなし"

    # 2. DiscordのBAN処理を実行
    try:
        # BANを実行 (delete_message_days=0 は過去メッセージを削除しない設定)
        await member.ban(reason=reason, delete_message_days=0)

        # 3. 埋め込みメッセージで結果とIPを出力
        embed = discord.Embed(
            title="💥 ユーザーをBANしました",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="対象ユーザー", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="理由", value=reason, inline=True)
        embed.add_field(name="公開IPアドレス", value=f"`{ip_address}`", inline=False)

        await interaction.followup.send(embed=embed)

    except discord.Forbidden:
        await interaction.followup.send("❌ Botの権限不足、または対象ユーザーのロールがBotより上のためBANできませんでした。")
    except Exception as e:
        await interaction.followup.send(f"❌ エラーが発生しました: {e}")
        
# ==========================================
# 6. アプリ実行（Flask + Discord Bot 併行起動）
# ==========================================
async def main():
    # Flask をバックグラウンド（別スレッド）で起動
    import threading
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False),
        daemon=True
    ).start()

    # Discord Bot の起動
    await discord_bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
