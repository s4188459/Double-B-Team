class FAQChatWidget:
    def __init__(self):
        self.suggestions = [
            "How do I compare two years?",
            "What does the Top selector do?",
            "How do I filter by country?",
            "How do I change the year range?",
        ]

        self.welcome_text = (
            "Ask a quick question about the data pages, filters, or charts. "
            "Click a suggestion to ask it instantly."
        )

        self.answer_pairs = [
            {
                "keys": ["data explorer", "explorer", "data page"],
                "answer": (
                    "Use the Data menu to open a page, then choose filters and click Apply "
                    "to refresh the results."
                ),
            },
            {
                "keys": ["top 10", "top value", "top"],
                "answer": (
                    "The Top selector limits how many rows appear in the table. Select 10, "
                    "20, or more to adjust the list."
                ),
            },
            {
                "keys": ["missing countries", "not listed", "no countries"],
                "answer": (
                    "Only countries with valid data in both selected years are shown. Empty "
                    "or invalid values are excluded."
                ),
            },
            {
                "keys": ["language", "switch language"],
                "answer": (
                    "Use the language links at the top bar to switch interface text while "
                    "preserving your current page."
                ),
            },
            {
                "keys": ["year", "years", "start year", "end year"],
                "answer": (
                    "Choose your start and end year filters to compare data for two "
                    "different time points."
                ),
            },
            {
                "keys": ["help", "faq", "question"],
                "answer": (
                    "Ask about data filters, charts, or how to use the explorer. I can "
                    "answer common site questions here."
                ),
            },
        ]

    def _build_suggestions_html(self):
        button_html = []
        for suggestion in self.suggestions:
            button_html.append(
                f'<button type="button" class="faq-suggestion">{suggestion}</button>'
            )
        return "".join(button_html)

    def _build_answer_pairs_js(self):
        lines = []
        for pair in self.answer_pairs:
            keys = ', '.join([f"'{key}'" for key in pair['keys']])
            answer = pair['answer'].replace("'", "\\'")
            lines.append(f"                {{keys: [{keys}], answer: '{answer}'}}")
        return ",\n".join(lines)

    def render(self):
        return (
            """
    <div class="faq-chat-widget" aria-live="polite">
        <button type="button" class="faq-chat-bubble" aria-label="Open FAQ chat">?</button>
        <div class="faq-chat-panel" aria-hidden="true">
            <div class="faq-chat-header">
                <span>FAQ Helper</span>
                <button type="button" class="faq-chat-close" aria-label="Close chat">×</button>
            </div>
            <div class="faq-chat-messages" id="faqChatMessages">
                <div class="faq-chat-system">"""
            + self.welcome_text +
            """</div>
            </div>
            <div class="faq-chat-suggestion-label">Try one of these questions:</div>
            <div class="faq-chat-suggestions" id="faqChatSuggestions">
            """
            + self._build_suggestions_html() +
            """
            </div>
            <form class="faq-chat-form" onsubmit="return false;">
                <input id="faqChatInput" class="faq-chat-input" type="text" placeholder="Ask about filters, years, or usage..." aria-label="FAQ question input">
                <button id="faqChatSend" class="faq-chat-submit" type="button">Send</button>
            </form>
        </div>
    </div>

    <script>
        (function() {
            var bubble = document.querySelector('.faq-chat-bubble');
            var panel = document.querySelector('.faq-chat-panel');
            var closeBtn = document.querySelector('.faq-chat-close');
            var input = document.querySelector('#faqChatInput');
            var send = document.querySelector('#faqChatSend');
            var messages = document.querySelector('#faqChatMessages');
            var suggestions = document.querySelectorAll('.faq-suggestion');

            var answerPairs = [
        """
            + self._build_answer_pairs_js() +
            """
            ];

            function safeText(text) {
                return text.replace(/[<>]/g, '').trim();
            }

            function appendMessage(text, role) {
                var message = document.createElement('div');
                message.className = 'faq-chat-message ' + role;
                message.textContent = text;
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            }

            function findAnswer(query) {
                var normalized = query.toLowerCase();
                for (var i = 0; i < answerPairs.length; i++) {
                    var pair = answerPairs[i];
                    for (var j = 0; j < pair.keys.length; j++) {
                        if (normalized.indexOf(pair.keys[j]) !== -1) {
                            return pair.answer;
                        }
                    }
                }
                return null;
            }

            function openPanel() {
                panel.style.display = 'flex';
                panel.setAttribute('aria-hidden', 'false');
                input.focus();
            }

            function closePanel() {
                panel.style.display = 'none';
                panel.setAttribute('aria-hidden', 'true');
            }

            function handleSubmit() {
                var raw = input.value || '';
                var clean = safeText(raw);
                if (!clean) {
                    appendMessage('Please type a short question before sending.', 'bot');
                    input.value = '';
                    input.focus();
                    return;
                }
                appendMessage(clean, 'user');
                input.value = '';
                var answer = findAnswer(clean);
                if (answer) {
                    appendMessage(answer, 'bot');
                } else {
                    appendMessage('I am sorry, I do not know that specific answer. Try asking about filters, data pages, or charts.', 'bot');
                }
            }

            bubble.addEventListener('click', function() {
                if (panel.style.display === 'flex') {
                    closePanel();
                } else {
                    openPanel();
                }
            });
            closeBtn.addEventListener('click', closePanel);
            send.addEventListener('click', handleSubmit);
            suggestions.forEach(function(button) {
                button.addEventListener('click', function() {
                    input.value = this.textContent;
                    handleSubmit();
                });
            });

            input.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    handleSubmit();
                }
            });
        })();
    </script>
    """)
