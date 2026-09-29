import json, sys, os
import discord
from discord.ext import commands
from core import Context
from utils.emoji import DENIED
import asyncio
from db.mongo import prefixes_col, blacklist_col, ignore_col, topcheck_col, guild_configs_col

async def is_topcheck_enabled(guild_id: int):
    try:
        doc = await topcheck_col.find_one({"guild_id": guild_id})
        return doc is not None and doc.get("enabled", False) is True
    except Exception:
        return False

def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"guilds": {}}

def write_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def get_or_create_guild_config(file_path, guild_id, default_config):
    data = read_json(file_path)
    if "guilds" not in data:
        data["guilds"] = {}

    guild_id_str = str(guild_id)
    if guild_id_str not in data["guilds"]:
        data["guilds"][guild_id_str] = default_config
        write_json(file_path, data)
    return data["guilds"][guild_id_str]

def update_guild_config(file_path, guild_id, new_data):
    data = read_json(file_path)
    if "guilds" not in data:
        data["guilds"] = {}

    data["guilds"][str(guild_id)] = new_data
    write_json(file_path, data)

def getIgnore(guild_id):
    default_config = {
        "channel": [],
        "role": None,
        "user": [],
        "bypassrole": None,
        "bypassuser": [],
        "commands": []
    }
    return get_or_create_guild_config("ignore.json", guild_id, default_config)

def updateignore(guild_id, data):
    update_guild_config("ignore.json", guild_id, data)

async def getConfig(guildID):
    try:
        doc = await prefixes_col.find_one({"guild_id": guildID})
        if doc and "prefix" in doc:
            return {"prefix": doc["prefix"]}
        else:
            defaultConfig = {"prefix": ">"}
            await updateConfig(guildID, defaultConfig)
            return defaultConfig
    except Exception:
        return {"prefix": ">"}

async def updateConfig(guildID, data):
    try:
        await prefixes_col.update_one(
            {"guild_id": guildID},
            {"$set": {"prefix": data.get("prefix", ">")}},
            upsert=True
        )
    except Exception as e:
        print(f"Error updating config in MongoDB: {e}")

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def blacklist_check():
    async def predicate(ctx):
        try:
            user_bl = await blacklist_col.find_one({"user_id": str(ctx.author.id)})
            if user_bl:
                return False

            if ctx.guild:
                guild_bl = await blacklist_col.find_one({"guild_id": str(ctx.guild.id)})
                if guild_bl:
                    return False
        except Exception:
            pass
        return True

    return commands.check(predicate)

async def get_ignore_data(guild_id: int) -> dict:
    try:
        doc = await ignore_col.find_one({"guild_id": guild_id})
        if doc:
            return {
                "channel": set(doc.get("channels", [])),
                "user": set(doc.get("users", [])),
                "command": set(doc.get("commands", [])),
                "bypassuser": set(doc.get("bypass_users", []))
            }
    except Exception:
        pass

    return {
        "channel": set(),
        "user": set(),
        "command": set(),
        "bypassuser": set(),
    }

def ignore_check():
    async def predicate(ctx):
        if not ctx.guild:
            return True
        data = await get_ignore_data(ctx.guild.id)
        ch = data["channel"]
        iuser = data["user"]
        cmd = data["command"]
        buser = data["bypassuser"]

        if str(ctx.author.id) in buser:
            return True
        if str(ctx.channel.id) in ch or str(ctx.author.id) in iuser:
            return False

        command_name = ctx.command.name.strip().lower()
        aliases = [alias.strip().lower() for alias in ctx.command.aliases]
        if command_name in cmd or any(alias in cmd for alias in aliases):
            return False

        return True

    return commands.check(predicate)

def top_check():
    async def predicate(ctx):
        if not ctx.guild:
            return True

        if getattr(ctx, "invoked_with", None) in ["help", "h"]:
            return True

        topcheck_enabled = await is_topcheck_enabled(ctx.guild.id)

        if not topcheck_enabled:
            return True

        if ctx.author != ctx.guild.owner and ctx.author.top_role.position <= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title=f"{DENIED} Access Denied",
                description="Your top role must be at a **higher** position than my top role.",
                color=0x000000
            )
            embed.set_footer(
                text=f"“{ctx.command.qualified_name}” command executed by {ctx.author}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            await ctx.send(embed=embed)
            return False

        return True

    return commands.check(predicate)