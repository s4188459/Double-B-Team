import translations as tr

class FAQChatWidget:
    def _html(self, value):
        return (
            str(value if value is not None else "")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _build_faq_items_html(self, lang):
        t = lambda k: tr.get_translation(k, lang)
        pairs = [
            (t("faq_q1"), t("faq_a1")),
            (t("faq_q2"), t("faq_a2")),
            (t("faq_q3"), t("faq_a3")),
            (t("faq_q4"), t("faq_a4")),
            (t("faq_q5"), t("faq_a5")),
            (t("faq_q6"), t("faq_a6")),
        ]
        item_html = []
        for question, answer in pairs:
            item_html.append(
                '<details class="faq-item">'
                f'<summary>{self._html(question)}</summary>'
                f'<p>{self._html(answer)}</p>'
                '</details>'
            )
        return "".join(item_html)

    def render(self, lang="en"):
        t = lambda k: tr.get_translation(k, lang)
        return (
            f"""
    <div class="faq-chat-widget" aria-live="polite">
        <input type="checkbox" id="faq-chat-toggle" class="faq-chat-toggle">
        <label for="faq-chat-toggle" class="faq-chat-bubble" aria-label="Open FAQ helper">?</label>
        <div class="faq-chat-panel">
            <div class="faq-chat-header">
                <span>{t("faq_title")}</span>
                <label for="faq-chat-toggle" class="faq-chat-close" aria-label="Close FAQ helper">&times;</label>
            </div>
            <div class="faq-chat-messages" id="faqChatMessages">
                <div class="faq-chat-system">{t("faq_welcome")}</div>
                <div class="faq-list">
            """
            + self._build_faq_items_html(lang)
            + """
                </div>
            </div>
        </div>
    </div>
    """
        )
