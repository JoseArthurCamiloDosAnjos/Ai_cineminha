import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = "http://localhost:8000/chat";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const history = [...messages, { role: "user", content: text }];
    setMessages([...history, { role: "assistant", content: "" }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });

      if (!res.ok || !res.body) throw new Error("Erro na resposta do servidor");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });

        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          copy[copy.length - 1] = { ...last, content: last.content + chunk };
          return copy;
        });
      }
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: "assistant",
          content: "⚠️ Não foi possível obter a resposta.",
        };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="chat">
      <header className="chat-header">Bora um cineminha?</header>

      <main className="chat-messages">
        {messages.length === 0 && (
          <p className="empty">Envie uma mensagem para começar.</p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.role === "assistant" ? (
              <ReactMarkdown>{m.content || "…"}</ReactMarkdown>
            ) : (
              m.content
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </main>

      <footer className="chat-input">
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua mensagem..."
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          {loading ? "..." : "Enviar"}
        </button>
      </footer>
    </div>
  );
}