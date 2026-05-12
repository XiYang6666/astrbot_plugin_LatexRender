import re
from io import BytesIO

import matplotlib.pyplot as plt
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star, register

LATEX_PATTERN = re.compile(r"\$(?!\$)(.+?)(?<!\$)\$")


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
        chain = result.chain
        new_chain = []

        for seg in chain:
            if not isinstance(seg, Plain):
                new_chain.append(seg)
                continue
            text = seg.text
            parts = re.split(LATEX_PATTERN, text)

            for i, part in enumerate(parts):
                if i % 2 == 0 and part:
                    new_chain.append(Plain(part))
                elif i % 2 == 1:
                    try:
                        data = self.latex_to_image(part)
                        new_chain.append(Image.fromBytes(data))
                    except Exception as e:
                        logger.warning(f"渲染失败: {part!r} -> {e}")
                        new_chain.append(Plain(part))
        result.chain = new_chain
