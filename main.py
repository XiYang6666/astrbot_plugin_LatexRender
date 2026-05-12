import re
from io import BytesIO
from typing import Callable

import matplotlib.pyplot as plt
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import BaseMessageComponent, Image, Plain
from astrbot.api.star import Context, Star, register

INLINE_LATEX_PATTERN = re.compile(r"\$(?!\$)(.+?)(?<!\$)\$")
BLOCK_LATEX_PATTERN = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)


@register("astrbot_plugin_LatexRender", "XiYang6666", "渲染 LLM 输出的 Latex", "1.0.0")
class LatexRenderPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    def latex_to_image(self, formula: str):
        fig, ax = plt.subplots(figsize=(1, 1))
        ax.set_axis_off()
        t = ax.text(
            0.5,
            0.5,
            f"${formula}$",
            fontsize=10,
            ha="center",
            va="center",
            color="#666666",
            transform=fig.transFigure,
        )

        fig.canvas.draw()
        bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
        dpi = fig.dpi
        pad = 2
        w = (bbox.width + pad * 2) / dpi
        h = (bbox.height + pad * 2) / dpi
        fig.set_size_inches(w, h)

        buf = BytesIO()
        plt.savefig(
            buf,
            format="png",
            dpi=150,
            bbox_inches="tight",
            transparent=False,
            facecolor="none",
        )
        plt.close(fig)

        data = buf.getvalue()
        return data

    def process_chain(
        self,
        chain: list[BaseMessageComponent],
        pattern: re.Pattern,
        operation: Callable[[str], BaseMessageComponent],
    ) -> list[BaseMessageComponent]:
        new_chain = []

        for seg in chain:
            if not isinstance(seg, Plain):
                new_chain.append(seg)
                continue
            text = seg.text
            parts = re.split(pattern, text)

            for i, part in enumerate(parts):
                if i % 2 == 0 and part:
                    new_chain.append(Plain(part))
                elif i % 2 == 1:
                    new_chain.append(operation(part))

        return new_chain

    def render_inline(self, part):
        try:
            data = self.latex_to_image(part)
            return Image.fromBytes(data)
        except Exception as e:
            logger.warning(f"渲染失败: {part!r} -> {e}")
            return Plain(part)

    def render_block(self, part):
        try:
            data = self.latex_to_image(part.strip())
            return Image.fromBytes(data)
        except Exception as e:
            logger.warning(f"渲染失败: {part!r} -> {e}")
            return Plain(f"$${part}$$")

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        result = event.get_result()
        if result is None:
            return

        logger.debug(f"current platform -> {event.platform}")
        logger.debug(f"raw message -> {result.chain}")

        if (
            self.config["platform_filter"]
            and event.platform.id not in self.config["allowed_platform"]
        ):
            return

        result.chain = self.process_chain(
            result.chain, BLOCK_LATEX_PATTERN, self.render_block
        )
        result.chain = self.process_chain(
            result.chain, INLINE_LATEX_PATTERN, self.render_inline
        )
