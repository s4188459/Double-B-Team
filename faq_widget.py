class FAQChatWidget:
    def __init__(self):
        self.welcome_text = (
            "Ask a quick question about the data pages, filters, or charts. "
            "Open one of the fixed questions below for a quick answer."
        )

        self.faq_items = [
            {
                "question": "How do I use a data page?",
                "answer": (
                    "Use the Data menu to open a page, then choose filters and click Apply "
                    "to refresh the results."
                ),
            },
            {
                "question": "What does the Top selector do?",
                "answer": (
                    "The Top selector limits how many rows appear in the table. Select 10, "
                    "20, or more to adjust the list."
                ),
            },
            {
                "question": "Why are some countries missing?",
                "answer": (
                    "Only countries with valid data in both selected years are shown. Empty "
                    "or invalid values are excluded."
                ),
            },
            {
                "question": "How do I switch language?",
                "answer": (
                    "Use the language links at the top bar to switch interface text while "
                    "preserving your current page."
                ),
            },
            {
                "question": "How do I compare or change years?",
                "answer": (
                    "Choose your start and end year filters to compare data for two "
                    "different time points."
                ),
            },
            {
                "question": "What questions can this FAQ answer?",
                "answer": (
                    "This FAQ covers common site questions about data filters, charts, "
                    "language switching, missing countries, and how to use the explorer."
                ),
            },
        ]

    def _html(self, value):
        return (
            str(value if value is not None else "")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _build_faq_items_html(self):
        item_html = []
        for item in self.faq_items:
            item_html.append(
                '<details class="faq-item">'
                f'<summary>{self._html(item["question"])}</summary>'
                f'<p>{self._html(item["answer"])}</p>'
                '</details>'
            )
        return "".join(item_html)

    def render(self):
        return (
            """
    <div class="faq-chat-widget" aria-live="polite">
        <input type="checkbox" id="faq-chat-toggle" class="faq-chat-toggle">
        <label for="faq-chat-toggle" class="faq-chat-bubble" aria-label="Open FAQ helper">?</label>
        <div class="faq-chat-panel">
            <div class="faq-chat-header">
                <span>FAQ Helper</span>
                <label for="faq-chat-toggle" class="faq-chat-close" aria-label="Close FAQ helper">&times;</label>
            </div>
            <div class="faq-chat-messages" id="faqChatMessages">
                <div class="faq-chat-system">"""
            + self.welcome_text
            + """</div>
                <div class="faq-list">
            """
            + self._build_faq_items_html()
            + """
                </div>
            </div>
        </div>
    </div>
    """
        )
