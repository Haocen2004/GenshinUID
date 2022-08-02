import asyncio
from pathlib import Path
from typing import List, Tuple, Optional

from nonebot.log import logger
from PIL import Image, ImageDraw

from ..utils.get_cookies.get_cookies import GetCookies
from ..utils.mhy_api.get_mhy_data import get_character
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_simple_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

# 确定路径
TEXT_PATH = Path(__file__).parent / 'texture2d'
RESOURCE_PATH = Path(__file__).parents[1] / 'resource'
CHAR_PATH = RESOURCE_PATH / 'chars'
WEAPON_PATH = RESOURCE_PATH / 'weapon'
CHAR_STAND_PATH = RESOURCE_PATH / 'char_stand'
REL_PATH = RESOURCE_PATH / 'reliquaries'
FETTER_PATH = RESOURCE_PATH / 'texture2d' / 'fetter'
TALENT_PATH = RESOURCE_PATH / 'texture2d' / 'talent'
WEAPON_BG_PATH = RESOURCE_PATH / 'texture2d' / 'weapon'
LEVEL_PATH = RESOURCE_PATH / 'texture2d' / 'level'

# 打开图片
char_card_bg4 = Image.open(TEXT_PATH / 'char_card_bg4.png')
char_card_bg5 = Image.open(TEXT_PATH / 'char_card_bg5.png')
char_card_fg = Image.open(TEXT_PATH / 'char_card_fg.png')
char_card_mask = Image.open(TEXT_PATH / 'char_card_mask.png')
role_info_fg = Image.open(TEXT_PATH / 'role_info_fg.png')

char_card8_bg4 = Image.open(TEXT_PATH / 'char_card8_bg4.png')
char_card8_bg5 = Image.open(TEXT_PATH / 'char_card8_bg5.png')
char_card8_fg = Image.open(TEXT_PATH / 'char_card8_fg.png')
char_card8_mask = Image.open(TEXT_PATH / 'char_card8_mask.png')


# 生成几个字号
gs_font_16 = genshin_font_origin(16)
gs_font_23 = genshin_font_origin(23)
gs_font_40 = genshin_font_origin(40)

# 文字颜色
text_color = (68, 66, 64)


async def get_fetter_pic(fetter: int) -> Image.Image:
    return Image.open(FETTER_PATH / f'fetter_{fetter}.png')


async def get_talent_pic(talent: int) -> Image.Image:
    return Image.open(TALENT_PATH / f'talent_{talent}.png')


async def get_weapon_pic(weapon_rarity: int) -> Image.Image:
    return Image.open(WEAPON_BG_PATH / f'weapon_bg{weapon_rarity}.png')


async def get_level_pic(level: int) -> Image.Image:
    return Image.open(LEVEL_PATH / f'level_{level}.png')


async def _draw_char_full_pic(img: Image.Image, char_data: dict, index: int):
    result = Image.new('RGBA', (250, 150), (0, 0, 0, 0))
    char_card_img = Image.new('RGBA', (250, 150), (0, 0, 0, 0))
    if char_data['rarity'] >= 5:
        char_card_img.paste(char_card_bg5, (0, 0))
    else:
        char_card_img.paste(char_card_bg4, (0, 0))
    weapon_pic = Image.open(
        WEAPON_PATH / f'{char_data["weapon"]["name"]}.png'
    ).convert('RGBA')
    weapon_pic_scale = weapon_pic.resize((50, 50))
    char_img = Image.open(CHAR_PATH / f'{char_data["id"]}.png').convert('RGBA')
    char_img_scale = char_img.resize((148, 148))
    char_card_img.paste(char_img_scale, (-20, 5), char_img_scale)
    char_card_img.paste(char_card_fg, (0, 0), char_card_fg)
    fetter_pic = await get_fetter_pic(char_data['fetter'])
    talent_pic = await get_talent_pic(char_data['actived_constellation_num'])
    weapon_bg_pic = await get_weapon_pic(char_data['weapon']['rarity'])
    char_card_img.paste(fetter_pic, (17, 110), fetter_pic)
    char_card_img.paste(talent_pic, (177, 24), talent_pic)
    char_card_img.paste(weapon_bg_pic, (105, 83), weapon_bg_pic)
    char_card_img.paste(weapon_pic_scale, (105, 83), weapon_pic_scale)
    char_draw = ImageDraw.Draw(char_card_img)
    char_draw.text(
        (114, 37),
        f'Lv{char_data["level"]}',
        text_color,
        gs_font_23,
        anchor='lm',
    )
    char_draw.text(
        (162, 96),
        f'Lv{char_data["weapon"]["level"]}',
        text_color,
        gs_font_23,
        anchor='lm',
    )
    char_draw.text(
        (162, 123),
        f'精炼{char_data["weapon"]["affix_level"]}',
        text_color,
        gs_font_23,
        anchor='lm',
    )
    result.paste(char_card_img, (0, 0), char_card_mask)
    img.paste(
        result,
        (15 + (index % 4) * 265, 1114 + (index // 4) * 160),
        result,
    )


async def _draw_text(
    text_draw: ImageDraw.ImageDraw, text: str, pos: Tuple[int, int]
):
    text_draw.text(
        pos,
        text,
        text_color,
        gs_font_40,
        anchor='lm',
    )


async def draw_pic(
    uid: str,
    mode: str = 'uid',
):
    # 获取Cookies
    data_def = GetCookies()
    retcode = await data_def.get_useable_cookies(uid, mode)
    if not retcode:
        return retcode
    use_cookies = data_def.useable_cookies
    raw_data = data_def.raw_data
    if data_def.uid:
        uid = data_def.uid

    # 记录数据
    if raw_data:
        raw_data = raw_data['data']
        char_data = raw_data['avatars']
    else:
        return '没有找到角色信息!'

    char_ids = []
    for i in char_data:
        char_ids.append(i['id'])

    char_rawdata = await get_character(uid, char_ids, use_cookies)
    char_datas = char_rawdata['data']['avatars']

    for index, i in enumerate(char_datas):
        if i['rarity'] > 5:
            char_datas[index]['rarity'] = 3
            break

    char_datas.sort(
        key=lambda x: (
            -x['rarity'],
            -x['fetter'],
            -x['actived_constellation_num'],
        )
    )

    # 确定角色占用行数
    char_num = len(char_datas)
    char_hang = (
        1 + (char_num - 1) // 4
        if char_num > 8
        else (char_num // 2) + (char_num % 2)
    )

    # 获取背景图片各项参数
    based_w = 1080
    if char_num > 8:
        based_h = 1080 + char_hang * 160 + 50
    else:
        based_h = 1080 + char_hang * 260 + 50
    img = await get_simple_bg(based_w, based_h)
    white_overlay = Image.new('RGBA', (based_w, based_h), (255, 251, 242, 211))
    img.paste(white_overlay, (0, 0), white_overlay)
    char_import = Image.open(
        CHAR_STAND_PATH / f'{char_datas[0]["id"]}.png'
    ).convert('RGBA')
    img.paste(char_import, (-529, -348), char_import)
    img.paste(role_info_fg, (0, 0), role_info_fg)

    # 绘制基础信息文字
    text_draw = ImageDraw.Draw(img)
    # text_draw.text(
    #    (382, 1045), f'UID{uid}', text_color, gs_font_40, anchor='lm'
    # )
    # 已获角色
    text_draw.text(
        (1024, 569),
        str(raw_data['stats']['avatar_number']),
        text_color,
        gs_font_40,
        anchor='rm',
    )
    # 活跃天数
    text_draw.text(
        (1024, 294),
        str(raw_data['stats']['active_day_number']),
        text_color,
        gs_font_40,
        anchor='rm',
    )
    # 成就数量
    text_draw.text(
        (1024, 386),
        str(raw_data['stats']['achievement_number']),
        text_color,
        gs_font_40,
        anchor='rm',
    )
    # 深渊
    text_draw.text(
        (1024, 477),
        raw_data['stats']['spiral_abyss'],
        text_color,
        gs_font_40,
        anchor='rm',
    )

    # 世界探索
    task = []
    for world in raw_data['world_explorations']:
        # 渊下宫
        if world['id'] == 5:
            # 探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (872, 886),
                )
            )
        # 层岩巨渊
        elif world['id'] == 6:
            # 地上探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (519, 886),
                )
            )
            world_level = await get_level_pic(world["offerings"][0]["level"])
            img.paste(world_level, (381, 890), world_level)
        # 地下矿区
        elif world['id'] == 7:
            # 地下探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (519, 921),
                )
            )
        # 稻妻
        elif world['id'] == 4:
            # 探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (872, 721),
                )
            )
            world_level = await get_level_pic(world["level"])
            img.paste(world_level, (734, 725), world_level)
            '''
            # 神樱
            task.append(
                _draw_text(
                    text_draw,
                    f'Lv.{world["offerings"][0]["level"]}',
                    (937, 702),
                )
            )
            '''
            '''
            # 雷神瞳
            task.append(
                _draw_text(
                    text_draw,
                    str(raw_data['stats']['electroculus_number']),
                    (960, 727),
                )
            )
            '''
        # 雪山
        elif world['id'] == 3:
            # 探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (166, 886),
                )
            )
            world_level = await get_level_pic(world["level"])
            img.paste(world_level, (28, 890), world_level)
        # 璃月
        elif world['id'] == 2:
            # 探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (519, 721),
                )
            )
            world_level = await get_level_pic(world["level"])
            img.paste(world_level, (381, 725), world_level)
            '''
            # 岩神瞳
            task.append(
                _draw_text(
                    text_draw,
                    str(raw_data['stats']['geoculus_number']),
                    (602, 735),
                )
            )
            '''
        # 蒙德
        elif world['id'] == 1:
            # 探索
            task.append(
                _draw_text(
                    text_draw,
                    f'{world["exploration_percentage"] / 10}%',
                    (166, 721),
                )
            )
            world_level = await get_level_pic(world["level"])
            img.paste(world_level, (28, 725), world_level)
            # 风神瞳
            '''
            task.append(
                _draw_text(
                    text_draw,
                    str(raw_data['stats']['anemoculus_number']),
                    (253, 735),
                )
            )
            '''
    await asyncio.gather(*task)

    tasks = []
    if char_num > 8:
        for index, char in enumerate(char_datas):
            tasks.append(
                _draw_char_full_pic(
                    img,
                    char,
                    index,
                )
            )
    else:
        for index, char in enumerate(char_datas):
            tasks.append(
                _draw_char_8_pic(
                    img,
                    char,
                    index,
                )
            )
    await asyncio.gather(*tasks)

    res = await convert_img(img)
    logger.info('[查询角色信息]绘图已完成,等待发送!')
    return res


async def _draw_char_8_pic(img: Image.Image, char_data: dict, index: int):
    """
    绘制8人角色图片
    """
    result = Image.new('RGBA', (510, 225), (0, 0, 0, 0))
    char_card_img = Image.new('RGBA', (510, 225), (0, 0, 0, 0))
    if char_data['rarity'] >= 5:
        char_card_img.paste(char_card8_bg5, (0, 0))
    else:
        char_card_img.paste(char_card8_bg4, (0, 0))
    weapon_pic = Image.open(
        WEAPON_PATH / f'{char_data["weapon"]["name"]}.png'
    ).convert('RGBA')
    weapon_pic_scale = weapon_pic.resize((50, 50))
    char_img = Image.open(CHAR_PATH / f'{char_data["id"]}.png').convert('RGBA')
    char_stand_img = Image.open(
        CHAR_STAND_PATH / f'{char_data["id"]}.png'
    ).convert('RGBA')
    char_stand_img.putalpha(
        char_stand_img.getchannel('A').point(
            lambda x: round(x * 0.4) if x > 0 else 0
        )
    )
    char_card_img.paste(char_stand_img, (-912, -313), char_stand_img)
    char_card_img.paste(char_img, (-14, -28), char_img)
    char_card_img.paste(char_card8_fg, (0, 0), char_card8_fg)
    fetter_pic = await get_fetter_pic(char_data['fetter'])
    talent_pic = await get_talent_pic(char_data['actived_constellation_num'])
    weapon_bg_pic = await get_weapon_pic(char_data['weapon']['rarity'])
    char_card_img.paste(fetter_pic, (355, 27), fetter_pic)
    char_card_img.paste(talent_pic, (440, 27), talent_pic)
    char_card_img.paste(weapon_bg_pic, (21, 158), weapon_bg_pic)
    char_card_img.paste(weapon_pic_scale, (21, 158), weapon_pic_scale)
    for equip_index, equip in enumerate(char_data['reliquaries']):
        equip_bg = await get_weapon_pic(equip['rarity'])
        equip_pic = (
            Image.open(REL_PATH / f'{equip["name"]}.png')
            .convert('RGBA')
            .resize((50, 50))
        )
        char_card_img.paste(equip_bg, (242 + equip_index * 50, 170), equip_bg)
        char_card_img.paste(
            equip_pic, (242 + equip_index * 50, 170), equip_pic
        )
    char_draw = ImageDraw.Draw(char_card_img)
    char_draw.text(
        (254, 36),
        f'Lv{char_data["level"]}',
        text_color,
        gs_font_40,
        anchor='lm',
    )
    char_draw.text(
        (81, 196),
        f'Lv{char_data["weapon"]["level"]}',
        text_color,
        gs_font_23,
        anchor='lm',
    )
    char_draw.text(
        (81, 168),
        f'{char_data["weapon"]["name"]}',
        text_color,
        gs_font_23,
        anchor='lm',
    )
    char_draw.text(
        (138, 196),
        f'精炼{char_data["weapon"]["affix_level"]}',
        text_color,
        gs_font_23,
        anchor='lm',
    )
    result.paste(char_card_img, (0, 0), char_card8_mask)
    img.paste(
        result,
        (15 + (index % 2) * 520, 1114 + (index // 2) * 250),
        result,
    )
