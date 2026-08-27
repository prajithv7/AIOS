import Link from "next/link";
import { Badge, Button, Card, CodePreview, StepRow } from "@/components/ui";

const STEPS = [
  { title: "Connect your keys", description: "Securely add provider API keys. Encrypted at rest, masked after creation." },
  { title: "Ask anything", description: "Chat with any connected model and switch mid-thread without losing context." },
  { title: "Compare on demand", description: "Fan one prompt out to multiple models in parallel." },
  { title: "Get the judged winner", description: "A rubric-based judge scores each response and picks a winner." },
];

const PROVIDERS = ["OpenAI", "Anthropic", "Gemini", "DeepSeek", "NVIDIA NIM", "Ollama"];

const SAMPLE_CODE = `POST /api/compare
{
  "conversationId": "conv_123",
  "content": "Review this React architecture",
  "modelIds": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet", "gemini/gemini-1.5-pro"]
}`;

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-5xl px-6">
      <header className="flex items-center justify-between py-6">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-accent" />
          <span className="text-lg font-medium text-primary">AIOS</span>
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-secondary hover:text-primary">Log in</Link>
          <Link href="/signup">
            <Button>Sign up</Button>
          </Link>
        </nav>
      </header>

      <section className="grid items-center gap-12 py-20 md:grid-cols-2">
        <div>
          <p className="eyebrow">One workspace, every model</p>
          <h1 className="mt-3 text-4xl leading-tight text-primary md:text-5xl">
            Chat, compare, and judge every AI provider from one conversation.
          </h1>
          <p className="mt-4 max-w-md">
            Switch models mid-thread, fan a prompt out to many providers, and let a
            rubric-based judge pick the winner — all without leaving the conversation.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/signup">
              <Button>Open workspace</Button>
            </Link>
            <a href="#how-it-works">
              <Button variant="secondary">See the docs</Button>
            </a>
          </div>
        </div>
        <div>
          <CodePreview filename="compare.request.json" code={SAMPLE_CODE} />
        </div>
      </section>

      <section id="how-it-works" className="pb-20">
        <p className="eyebrow">How it works</p>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          {STEPS.map((s, i) => (
            <StepRow key={i} index={i} title={s.title} description={s.description} />
          ))}
        </div>
      </section>

      <footer className="border-t border-border py-10">
        <p className="eyebrow mb-4">Supported providers</p>
        <div className="flex flex-wrap gap-3">
          {PROVIDERS.map((p) => (
            <Badge key={p}>{p}</Badge>
          ))}
        </div>
        <p className="mt-8 text-sm text-muted">AIOS — one workspace, every model.</p>
      </footer>
    </main>
  );
}
