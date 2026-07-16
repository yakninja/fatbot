from unittest.mock import AsyncMock

import pytest

from fatbot import BOT_COMMANDS, register_bot_commands


def test_bot_command_panel_contains_user_commands():
    assert [command.command for command in BOT_COMMANDS] == [
        'start',
        'help',
        'today',
        'weight',
        'label',
        'unlabel',
        'cancel',
        'settings',
    ]


@pytest.mark.asyncio
async def test_register_bot_commands_sets_telegram_command_panel():
    application = type('Application', (), {})()
    application.bot = type('Bot', (), {})()
    application.bot.set_my_commands = AsyncMock()

    await register_bot_commands(application)

    application.bot.set_my_commands.assert_awaited_once_with(BOT_COMMANDS)
