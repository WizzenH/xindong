"""Curated widget palettes. Colors are original UI adaptations of each style."""
from dataclasses import dataclass, fields
from typing import Dict


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    description: str
    background: str
    surface: str
    foreground: str
    muted: str
    money: str
    accent: str
    accent_foreground: str
    positive: str
    border: str
    track: str
    hover: str
    work_background: str
    work_foreground: str
    work_hover: str

    @property
    def colors(self) -> Dict[str, str]:
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name not in {"key", "name", "description"}
        }


THEMES = {
    theme.key: theme
    for theme in (
        Theme(
            key="night",
            name="夜航绿",
            description="石墨灰 × 荧光青柠",
            background="#171C26",
            surface="#242D3C",
            foreground="#E8ECF3",
            muted="#A4AFC0",
            money="#D5F9A8",
            accent="#BCF390",
            accent_foreground="#18251A",
            positive="#B4D89D",
            border="#394354",
            track="#303A46",
            hover="#35445B",
            work_background="#314639",
            work_foreground="#D5F9A8",
            work_hover="#435444",
        ),
        Theme(
            key="maillard",
            name="美拉德",
            description="浓咖啡 × 焦糖金",
            background="#2D211D",
            surface="#423029",
            foreground="#F7EBDD",
            muted="#C8AF9B",
            money="#F4C38A",
            accent="#E4A668",
            accent_foreground="#302018",
            positive="#E8BE98",
            border="#655044",
            track="#594034",
            hover="#624738",
            work_background="#65452D",
            work_foreground="#FFE3BC",
            work_hover="#795338",
        ),
        Theme(
            key="morandi",
            name="莫兰迪",
            description="雾灰紫 × 低饱和鼠尾草",
            background="#E8E3E7",
            surface="#DDD6DF",
            foreground="#403946",
            muted="#665C6D",
            money="#62506A",
            accent="#71657F",
            accent_foreground="#FFFFFF",
            positive="#4B655D",
            border="#BDB3C3",
            track="#CEC3D3",
            hover="#CEC4D3",
            work_background="#D0DDD6",
            work_foreground="#365649",
            work_hover="#B9CEC2",
        ),
        Theme(
            key="rose_dusk",
            name="玫瑰暮霭",
            description="雾玫粉 × 珍珠白 × 暮色棕",
            background="#F7F2EE",
            surface="#D8B4B6",
            foreground="#443237",
            muted="#735C60",
            money="#81545E",
            accent="#A78F88",
            accent_foreground="#2C2022",
            positive="#785B55",
            border="#D8B4B6",
            track="#D8B4B6",
            hover="#E8CDCE",
            work_background="#D8B4B6",
            work_foreground="#50363D",
            work_hover="#CFA6AA",
        ),
        Theme(
            key="ember",
            name="赤焰夜幕",
            description="迷雾黑 × 炽焰红",
            background="#0A090C",
            surface="#21171C",
            foreground="#F7F2EE",
            muted="#BBA8AC",
            money="#E61A23",
            accent="#E61A23",
            accent_foreground="#FFFFFF",
            positive="#F0999D",
            border="#4A2A33",
            track="#49252D",
            hover="#392029",
            work_background="#36181E",
            work_foreground="#F6CBCD",
            work_hover="#54232C",
        ),
        Theme(
            key="forest_linen",
            name="森雾亚麻",
            description="森雾青 × 亚麻米 × 苔灰绿",
            background="#E6DCC8",
            surface="#7FA69A",
            foreground="#21372D",
            muted="#526554",
            money="#344E45",
            accent="#7FA69A",
            accent_foreground="#172D25",
            positive="#425C3D",
            border="#7FA69A",
            track="#B5C180",
            hover="#B5C180",
            work_background="#B5C180",
            work_foreground="#273E24",
            work_hover="#A2B36D",
        ),
        Theme(
            key="matcha",
            name="奶油抹茶",
            description="奶油白 × 自然苔绿",
            background="#F4F1E6",
            surface="#E8ECD9",
            foreground="#303F32",
            muted="#5B6855",
            money="#3C6544",
            accent="#4E704D",
            accent_foreground="#FFFFFF",
            positive="#4D6F40",
            border="#C3CBB6",
            track="#D3DCC4",
            hover="#D8E0C8",
            work_background="#D7E5CA",
            work_foreground="#355632",
            work_hover="#C4D9B2",
        ),
        Theme(
            key="klein",
            name="克莱因蓝",
            description="浓郁群青 × 冰川青蓝",
            background="#102582",
            surface="#1C3598",
            foreground="#EFF3FF",
            muted="#BCCAF2",
            money="#C8F1FF",
            accent="#A0E8F2",
            accent_foreground="#12246A",
            positive="#B5E7F5",
            border="#4A62B1",
            track="#3A50A2",
            hover="#2E4BAF",
            work_background="#294C9E",
            work_foreground="#E2F5FF",
            work_hover="#3A60B7",
        ),
    )
}

DEFAULT_THEME = "night"
