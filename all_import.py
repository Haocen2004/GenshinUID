import re
import json
import base64
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, List, Tuple, Union
from time import strftime, strptime, localtime

from httpx import AsyncClient
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from nonebot.params import Depends, CommandArg, RegexGroup
from nonebot.exception import ActionFailed, FinishedException
from nonebot import (
    Bot,
    logger,
    get_bot,
    require,
    on_regex,
    get_driver,
    on_command,
)
from nonebot.adapters.onebot.v11 import (
    PRIVATE_FRIEND,
    Message,
    ActionFailed,
    MessageEvent,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from .utils.message.get_image_and_at import ImageAndAt
from .utils.message.error_reply import *  # noqa: F403,F401
from .utils.alias.alias_to_char_name import alias_to_char_name
from .utils.exception.handle_exception import handle_exception
from .utils.genshin_fonts.genshin_fonts import genshin_font_origin

priority = 2
