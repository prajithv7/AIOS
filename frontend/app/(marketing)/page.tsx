import Link from "next/link";
import { Badge, Button, Card, StepRow } from "@/components/ui";
import { IconPaperclip, IconSparkles } from "@tabler/icons-react";

const STEPS = [
  { title: "Connect your keys", description: "Securely add provider API keys. Encrypted at rest, masked after creation." },
  { title: "Ask anything", description: "Chat with any connected model and switch mid-thread without losing context." },
  { title: "Compare on demand", description: "Fan one prompt out to multiple models in parallel." },
  { title: "Get the judged winner", description: "A rubric-based judge scores each response and picks a winner." },
];

const PROVIDERS = ["OpenAI", "Anthropic", "Gemini", "DeepSeek", "NVIDIA NIM", "Ollama"];

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 font-sans">
      <header className="flex items-center justify-between py-6">
        <div className="flex items-center gap-2">
          <span className="inline-block h-4 w-4 rounded-full bg-accent" />
          <span className="text-xl font-bold text-primary tracking-tight">AIOS</span>
        </div>
        <nav className="flex items-center gap-6">
          <Link href="/login" className="text-sm font-medium text-primary hover:text-accent transition-colors">Log in</Link>
          <Link href="/signup">
            <Button className="font-semibold shadow-sm">Sign up</Button>
          </Link>
        </nav>
      </header>

      <section className="grid items-center gap-12 py-20 lg:grid-cols-2">
        <div className="pr-4">
          <p className="eyebrow text-accent font-bold tracking-widest text-xs uppercase mb-2">One workspace, every model</p>
          <h1 className="mt-3 text-5xl font-extrabold leading-tight text-primary md:text-6xl tracking-tight">
            Chat, compare, and judge every AI provider.
          </h1>
          <p className="mt-6 max-w-lg text-lg text-primary/80 font-medium leading-relaxed">
            Switch models mid-thread, fan a prompt out to many providers, and let a
            rubric-based judge pick the winner — all without leaving the conversation.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/signup">
              <Button className="text-base px-6 py-3 font-semibold shadow-md">Open workspace</Button>
            </Link>
            <a href="#how-it-works">
              <Button variant="secondary" className="text-base px-6 py-3 font-semibold bg-surface hover:bg-page">See the docs</Button>
            </a>
          </div>
        </div>
        
        {/* Realistic Dashboard Preview */}
        <div className="relative rounded-xl border border-border bg-surface shadow-2xl overflow-hidden flex h-[480px] w-full transform md:scale-105 origin-left">
          {/* Sidebar */}
          <div className="w-52 border-r border-border bg-page p-3 flex flex-col gap-3 hidden sm:flex">
            <div className="flex items-center gap-2 mb-2 p-1">
              <span className="w-3 h-3 rounded-full bg-accent"></span>
              <span className="font-bold text-sm text-primary tracking-tight">AIOS Workspace</span>
            </div>
            
            <div>
              <div className="text-[10px] font-bold text-muted uppercase tracking-wider px-2 mb-1">Projects</div>
              <div className="text-sm font-medium text-primary bg-accent-soft border border-accent/20 rounded px-3 py-1.5 shadow-sm">AI Platform</div>
            </div>
            
            <div className="mt-2">
              <div className="text-[10px] font-bold text-muted uppercase tracking-wider px-2 mb-1">Conversations</div>
              <div className="text-sm font-medium text-primary rounded px-3 py-1.5 hover:bg-surface transition-colors cursor-default">Auth implementation</div>
              <div className="text-sm font-medium text-primary bg-surface border border-border shadow-sm rounded px-3 py-1.5 mt-1 cursor-default">Routing Logic</div>
              <div className="text-sm font-medium text-primary/70 rounded px-3 py-1.5 hover:bg-surface transition-colors cursor-default mt-1">Landing page copy</div>
            </div>
          </div>

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col bg-surface overflow-hidden">
            <div className="border-b border-border p-3 flex justify-between items-center bg-page shadow-sm z-10">
              <div className="text-sm font-bold text-primary truncate max-w-[150px]">Routing Logic</div>
              <div className="flex items-center gap-2">
                <div className="text-xs font-medium border border-border rounded bg-surface px-2.5 py-1.5 shadow-sm text-primary flex items-center gap-1 cursor-default">
                  Claude 3.5 Sonnet
                </div>
                <div className="text-xs font-medium border border-accent/30 rounded bg-accent-soft text-accent px-2.5 py-1.5 shadow-sm flex items-center gap-1.5 cursor-default">
                  <IconSparkles size={14} /> Recommend
                </div>
              </div>
            </div>
            
            <div className="flex-1 p-5 overflow-hidden flex flex-col gap-4 bg-[url('/noise.png')] bg-repeat bg-opacity-5">
              <div className="flex justify-end">
                 <div className="bg-accent-soft border border-accent/20 rounded-xl rounded-tr-sm p-3 text-sm text-primary font-medium max-w-[85%] shadow-sm">
                   Could you help me design the routing logic for the new multi-model fan-out feature?
                 </div>
              </div>
              <div className="flex justify-start">
                 <div className="bg-surface border border-border rounded-xl rounded-tl-sm p-4 text-sm text-primary max-w-[90%] shadow-md leading-relaxed">
                   <p className="mb-2 font-medium">Certainly. A robust multi-model fan-out should involve:</p>
                   <ul className="list-disc pl-4 space-y-1 text-primary/90">
                     <li>An <strong className="font-semibold">AI Orchestrator</strong> that normalizes the prompt.</li>
                     <li>Concurrent requests to the selected models via <code className="bg-page px-1 rounded text-accent text-xs">asyncio.gather</code>.</li>
                     <li>A unified aggregator that collects latency and token metrics.</li>
                   </ul>
                   <div className="mt-3 flex items-center gap-2">
                      <span className="inline-block h-2 w-2 rounded-full bg-accent" />
                      <span className="font-mono text-[10px] text-muted font-semibold tracking-wider">claude-3-5-sonnet · anthropic</span>
                   </div>
                 </div>
              </div>
            </div>
            
            <div className="p-4 border-t border-border bg-page relative shadow-[0_-4px_15px_-5px_rgba(0,0,0,0.05)]">
               <div className="flex gap-2 items-end">
                 <button className="text-muted p-2.5 hover:text-primary hover:bg-surface rounded transition-colors" title="Attach files">
                   <IconPaperclip size={20} />
                 </button>
                 <textarea 
                   className="flex-1 text-sm bg-surface border border-border rounded-lg px-3 py-2.5 resize-none h-[42px] font-medium shadow-inner placeholder:text-muted" 
                   placeholder="Ask anything..." 
                   readOnly
                 />
                 <button className="bg-surface hover:bg-white border border-border text-primary text-sm rounded-lg px-4 py-2.5 font-bold shadow-sm transition-all">
                   Compare
                 </button>
                 <button className="bg-accent hover:bg-accent/90 text-white text-sm rounded-lg px-4 py-2.5 font-bold shadow-md transition-all">
                   Send
                 </button>
               </div>
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="pb-24 pt-8">
        <h2 className="text-2xl font-bold text-primary mb-8 tracking-tight">How it works</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <StepRow key={i} index={i} title={s.title} description={s.description} />
          ))}
        </div>
      </section>

      <footer className="border-t border-border py-12">
        <p className="eyebrow mb-6 text-sm font-bold tracking-widest text-muted uppercase">Supported providers</p>
        <div className="flex flex-wrap gap-3">
          {PROVIDERS.map((p) => (
            <Badge key={p}>{p}</Badge>
          ))}
        </div>
        <p className="mt-12 text-sm font-medium text-muted">AIOS — one workspace, every model.</p>
      </footer>
    </main>
  );
}
