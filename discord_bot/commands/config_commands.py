import logging

import pytz
from discord import Interaction, Embed, Color
from pytz import UnknownTimeZoneError

from discord_bot.models.propaganda_config import save_settings_to_file
from discord_bot.propaganda_bot import PropagandaBot
from discord_bot.models.token_config import TokenConfig
from discord_bot.scheduler import setup_scheduler

logger = logging.getLogger(__name__)


def register_config_commands(bot: PropagandaBot, api_tokens: list[str]):
    config = bot.propaganda_config

    @bot.tree.command(
        name="set_channel",
        description="Set the current channel for propaganda posters")
    async def set_channel(interaction: Interaction):
        config.propaganda_scheduler.poster_output_channel_id = interaction.channel_id
        save_settings_to_file(config)
        await interaction.response.send_message(
            "Channel set for propaganda posters.")

    @bot.tree.command(
        name="set_voice_channel",
        description="Set the voice channel for music playback")
    async def set_voice_channel(interaction: Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(
                "You must be in a voice channel to set it!")
            return
        config.propaganda_scheduler.voice_channel_id = interaction.user.voice.channel.id
        save_settings_to_file(config)
        await interaction.response.send_message(
            f"Voice channel set to: {interaction.user.voice.channel.name}")

    @bot.tree.command(name="set_time",
                      description="Set the time for daily posts (HH:MM)")
    async def set_time(interaction: Interaction, time: str):
        try:
            hour, minute = map(int, time.split(':'))
            config.propaganda_scheduler.time.hour = hour
            config.propaganda_scheduler.time.minute = minute
            save_settings_to_file(config)
            setup_scheduler(bot, api_tokens)
            await interaction.response.send_message(
                f"Post time set to {time} & Restarted Scheduler")
        except ValueError:
            await interaction.response.send_message(
                "Invalid time format. Use HH:MM (e.g., 15:30)")

    @bot.tree.command(name="set_timezone", description="Set the timezone")
    async def set_timezone(interaction: Interaction,
                           timezone: str):
        try:
            pytz.timezone(timezone)
            config.propaganda_scheduler.timezone = timezone
            save_settings_to_file(config)
            setup_scheduler(bot, api_tokens)
            await interaction.response.send_message(
                f"Timezone set to: {timezone} & Restarted Scheduler")
        except UnknownTimeZoneError:
            await interaction.response.send_message(
                f"Invalid timezone: {timezone}. Example: US/Eastern, Europe/London.")
        except Exception:
            await interaction.response.send_message(
                f"Error in config file / scheduler.")

    @bot.tree.command(name="show_config",
                      description="Show current configuration")
    async def show_config(interaction: Interaction):
        channel_mention = f"<#{config.propaganda_scheduler.poster_output_channel_id}>" if config.propaganda_scheduler.poster_output_channel_id else "Not set"
        # Truncate text prompt if too long
        text_prompt = config.text_prompt
        if len(text_prompt) > 900:
            text_prompt = text_prompt[:897] + "..."

        embed = Embed(title="Propaganda Poster Configuration",
                      color=Color.orange())
        embed.add_field(name="Channel", value=channel_mention, inline=True)
        embed.add_field(
            name="Post Time",
            value=
            f"{config.propaganda_scheduler.time.hour:02d}:{config.propaganda_scheduler.time.minute:02d} {config.propaganda_scheduler.timezone}",
            inline=True)
        embed.add_field(name="Text Prompt",
                        value=text_prompt,
                        inline=False)

        await interaction.response.send_message(embed=embed)
