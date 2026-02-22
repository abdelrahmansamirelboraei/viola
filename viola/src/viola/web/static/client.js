document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("chatForm");
    const input = document.getElementById("messageInput");
    const messages = document.getElementById("messages");

    function addMessage(text, cls) {
        const div = document.createElement("div");
        div.className = cls;
        div.innerText = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const text = input.value.trim();
        if (!text) return;

        addMessage("أنت: " + text, "user");
        input.value = "";

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text })
            });

            const data = await res.json();

            if (data.ok) {
                addMessage("🟣 Farida:\n" + data.response, "assistant");
            } else {
                addMessage("خطأ في السيرفر", "assistant");
            }

        } catch (err) {
            addMessage("تعذر الاتصال بالسيرفر", "assistant");
        }
    });

});

