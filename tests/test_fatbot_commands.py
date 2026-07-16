from unittest.mock import AsyncMock

import i18n
import pytest


@pytest.fixture()
def fatbot_module():
    locale = i18n.get('locale')
    import fatbot

    yield fatbot

    i18n.set('locale', locale)


def test_bot_command_panel_contains_user_commands(fatbot_module):
    assert [command.command for command in fatbot_module.BOT_COMMANDS] == [
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
async def test_register_bot_commands_sets_telegram_command_panel(fatbot_module):
    application = type('Application', (), {})()
    application.bot = type('Bot', (), {})()
    application.bot.set_my_commands = AsyncMock()

    await fatbot_module.register_bot_commands(application)

    application.bot.set_my_commands.assert_awaited_once_with(fatbot_module.BOT_COMMANDS)
