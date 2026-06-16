import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { API_ENDPOINTS, ORIGIN } from "@/lib/aviation-config";
import { supabase } from "@/integrations/supabase/client";

interface AeronaveRow {
  id: string;
  modelo: string;
  imagem_url: string | null;
  custo_aquisicao: number;
  custo_manutencao: number;
  custo_combustivel_hora: number;
  autonomia_km: number;
  pax: number;
  carga_kg: number;
}

function mapRow(r: AeronaveRow): Aircraft {
  return {
    id: r.id,
    modelo: r.modelo,
    imagem: r.imagem_url ?? "",
    aquisicao: Number(r.custo_aquisicao),
    manutencao: Number(r.custo_manutencao),
    combustivel: Number(r.custo_combustivel_hora),
    autonomia: Number(r.autonomia_km),
    pax: Number(r.pax),
    carga: Number(r.carga_kg),
  };
}

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AeroVIKOR · Inteligência Logística de Aviação" },
      {
        name: "description",
        content:
          "Painel de decisão multicritério VIKOR para seleção de aeronaves a partir de Recife.",
      },
    ],
  }),
  component: Dashboard,
});

interface Aircraft {
  id: string;
  modelo: string;
  imagem: string;
  aquisicao: number;
  manutencao: number;
  combustivel: number;
  autonomia: number;
  pax: number;
  carga: number;
}

interface VikorResult {
  distancia_km: number;
  rejeitadas: { id: string; modelo: string; motivo: string }[];
  ranking: { id: string; modelo: string; imagem: string; Q: number; S: number; R: number }[];
}

interface DestinationOption {
  id: string;
  nome: string;
  uf: string;
  aeroporto: string;
  distancia_km: number;
}

const emptyForm = {
  modelo: "",
  imagem: "",
  aquisicao: "",
  manutencao: "",
  combustivel: "",
  autonomia: "",
  pax: "",
  carga: "",
};

function Dashboard() {
  const [aircrafts, setAircrafts] = useState<Aircraft[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [destino, setDestino] = useState("");
  const [destinations, setDestinations] = useState<DestinationOption[]>([]);
  const [weights, setWeights] = useState({
    aquisicao: 20,
    manutencao: 20,
    combustivel: 20,
    pax: 20,
    carga: 20,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VikorResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    supabase
      .from("aeronaves")
      .select("*")
      .order("created_at", { ascending: true })
      .then(({ data, error }) => {
        if (!error && data) setAircrafts((data as AeronaveRow[]).map(mapRow));
      });
  }, []);

  useEffect(() => {
    fetch(API_ENDPOINTS.destinations)
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then((data: DestinationOption[]) => setDestinations(data))
      .catch(() => {
        setDestinations([]);
      });
  }, []);

  const totalWeight = useMemo(
    () => Object.values(weights).reduce((a, b) => a + b, 0),
    [weights],
  );

  // Ajusta um peso e redistribui os demais proporcionalmente para a soma ficar sempre 100.
  function setWeight(key: keyof typeof weights, value: number) {
    setWeights((prev) => {
      const v = Math.max(0, Math.min(100, Math.round(value)));
      const others = (Object.keys(prev) as (keyof typeof weights)[]).filter((k) => k !== key);
      const remaining = 100 - v;
      const othersTotal = others.reduce((sum, k) => sum + prev[k], 0);
      const next = { ...prev, [key]: v };

      if (othersTotal === 0) {
        // Todos os outros estão em 0: distribui igualmente.
        const base = Math.floor(remaining / others.length);
        let leftover = remaining - base * others.length;
        others.forEach((k) => {
          next[k] = base + (leftover-- > 0 ? 1 : 0);
        });
      } else {
        // Distribui proporcionalmente ao valor atual de cada peso.
        const raw = others.map((k) => ({ k, exact: (prev[k] / othersTotal) * remaining }));
        let allocated = 0;
        raw.forEach((r) => {
          next[r.k] = Math.floor(r.exact);
          allocated += next[r.k];
        });
        // Sobra do arredondamento vai para os maiores restos fracionários.
        let leftover = remaining - allocated;
        raw
          .sort((a, b) => (b.exact - Math.floor(b.exact)) - (a.exact - Math.floor(a.exact)))
          .forEach((r) => {
            if (leftover > 0) {
              next[r.k] += 1;
              leftover--;
            }
          });
      }
      return next;
    });
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      modelo: form.modelo,
      imagem_url: form.imagem,
      custo_aquisicao: Number(form.aquisicao),
      custo_manutencao: Number(form.manutencao),
      custo_combustivel_hora: Number(form.combustivel),
      autonomia_km: Number(form.autonomia),
      pax: Number(form.pax),
      carga_kg: Number(form.carga),
    };
    const { data, error } = await supabase
      .from("aeronaves")
      .insert(payload)
      .select()
      .single();
    if (error || !data) {
      setError(`Erro ao salvar aeronave: ${error?.message ?? "desconhecido"}`);
      return;
    }
    setAircrafts((prev) => [...prev, mapRow(data as AeronaveRow)]);
    setForm(emptyForm);
  }

  async function handleVikor() {
    if (!destino.trim() || selected.size === 0) {
      setError("Informe destino e selecione ao menos uma aeronave.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.vikor, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destino,
          pesos: weights,
          aeronaves_ids: Array.from(selected),
        }),
      });
      if (!res.ok) throw new Error("Erro ao gerar matriz VIKOR");
      setResult(await res.json());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) => {
      if (prev.size === aircrafts.length && aircrafts.length > 0) {
        return new Set();
      }
      return new Set(aircrafts.map((a) => a.id));
    });
  }

  return (
    <main className="mx-auto max-w-[1600px] px-6 py-8">
      <header className="mb-8 flex items-end justify-between border-b border-border pb-6">
        <div>
          <div className="mb-1 text-xs font-medium uppercase tracking-[0.2em] text-accent">
            Inteligência Logística · VIKOR
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            AeroVIKOR <span className="text-primary">Decision Hub</span>
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Seleção multicritério de aeronaves para operações partindo de {ORIGIN}.
          </p>
        </div>
        <div className="hidden rounded-lg border border-border bg-card px-4 py-2 text-right text-xs text-muted-foreground md:block">
          <div>Frota cadastrada: <span className="font-semibold text-foreground">{aircrafts.length}</span></div>
          <div>Selecionadas: <span className="font-semibold text-primary">{selected.size}</span></div>
        </div>
      </header>

      {/* Seção 1 */}
      <Section number="01" title="Frota & Banco de Dados" subtitle="Cadastre e selecione as aeronaves disponíveis para a missão">
        <div className="grid gap-6 lg:grid-cols-[400px_1fr]">
          <form
            onSubmit={handleAdd}
            className="rounded-2xl border border-border bg-card p-6 shadow-sm"
          >
            <h3 className="mb-4 text-lg font-semibold">Nova Aeronave</h3>
            <div className="space-y-3">
              <Field label="Modelo" value={form.modelo} onChange={(v) => setForm({ ...form, modelo: v })} placeholder="Pelican 500 BR" required />
              <Field label="URL da Imagem" value={form.imagem} onChange={(v) => setForm({ ...form, imagem: v })} placeholder="https://..." required />
              <div className="grid grid-cols-2 gap-3">
                <Field label="Custo Aquisição (US$)" type="number" value={form.aquisicao} onChange={(v) => setForm({ ...form, aquisicao: v })} required />
                <Field label="Manutenção/mês (US$)" type="number" value={form.manutencao} onChange={(v) => setForm({ ...form, manutencao: v })} required />
                <Field label="Combustível (L/h)" type="number" value={form.combustivel} onChange={(v) => setForm({ ...form, combustivel: v })} required />
                <Field label="Autonomia (KM)" type="number" value={form.autonomia} onChange={(v) => setForm({ ...form, autonomia: v })} required />
                <Field label="PAX" type="number" value={form.pax} onChange={(v) => setForm({ ...form, pax: v })} required />
                <Field label="Carga (KG)" type="number" value={form.carga} onChange={(v) => setForm({ ...form, carga: v })} required />
              </div>
              <button
                type="submit"
                className="mt-2 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                + Adicionar Aeronave
              </button>
            </div>
          </form>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Frota Disponível</h3>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={toggleAll}
                  className="rounded-md border border-border bg-muted px-3 py-1.5 text-xs font-semibold text-foreground transition hover:bg-secondary"
                >
                  {selected.size === aircrafts.length && aircrafts.length > 0 ? "Desmarcar todas" : "Selecionar todas"}
                </button>
                <span className="text-xs text-muted-foreground">{selected.size} selecionada(s)</span>
              </div>
            </div>
            <div className="grid max-h-[520px] gap-4 overflow-y-auto pr-2 sm:grid-cols-2 xl:grid-cols-3">
              {aircrafts.length === 0 && (
                <div className="col-span-full rounded-lg border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
                  Nenhuma aeronave cadastrada ainda.
                </div>
              )}
              {aircrafts.map((a) => {
                const isSel = selected.has(a.id);
                return (
                  <div
                    key={a.id}
                    className={`group overflow-hidden rounded-xl border-2 bg-background transition ${
                      isSel ? "border-primary shadow-md shadow-primary/10" : "border-border"
                    }`}
                  >
                    <div className="aspect-video w-full overflow-hidden bg-muted">
                      <img src={a.imagem} alt={a.modelo} className="h-full w-full object-cover" />
                    </div>
                    <div className="p-3">
                      <div className="mb-2 font-semibold leading-tight">{a.modelo}</div>
                      <div className="mb-3 grid grid-cols-2 gap-1 text-[11px] text-muted-foreground">
                        <span>✈ {a.autonomia} km</span>
                        <span>👥 {a.pax} pax</span>
                        <span>📦 {a.carga} kg</span>
                        <span>⛽ {a.combustivel} L/h</span>
                      </div>
                      <label className={`flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold transition ${
                        isSel ? "bg-primary text-primary-foreground" : "bg-muted text-foreground hover:bg-secondary"
                      }`}>
                        <span>{isSel ? "✓ Selecionada" : "Selecionar p/ Missão"}</span>
                        <input
                          type="checkbox"
                          checked={isSel}
                          onChange={() => toggleSelect(a.id)}
                          className="h-4 w-4 accent-white"
                        />
                      </label>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Section>

      {/* Seção 2 */}
      <Section number="02" title="Planejamento da Rota" subtitle="Defina destino e a importância de cada critério na decisão">
        <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
          <div className="space-y-4">
            <div className="rounded-2xl border border-border bg-gradient-to-br from-primary/5 to-accent/10 p-6">
              <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Origem fixa</div>
              <div className="mt-1 flex items-center gap-2 text-2xl font-bold">
                <span>📍</span>
                <span>{ORIGIN}</span>
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-card p-6">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Destino</label>
              <input
                list="destinos-disponiveis"
                value={destino}
                onChange={(e) => setDestino(e.target.value)}
                placeholder="Selecione ou digite um destino disponivel"
                className="mt-2 w-full rounded-lg border border-input bg-background px-4 py-3 text-lg font-medium outline-none ring-primary/40 focus:ring-2"
              />
              <datalist id="destinos-disponiveis">
                {destinations.map((destination) => (
                  <option
                    key={destination.id}
                    value={`${destination.nome}, ${destination.uf}`}
                  >
                    {destination.aeroporto} - {destination.distancia_km} km
                  </option>
                ))}
              </datalist>
              {destinations.length > 0 && (
                <div className="mt-2 text-xs text-muted-foreground">
                  {destinations.length} destinos pre-carregados a partir de {ORIGIN}.
                </div>
              )}
            </div>
            <button
              onClick={handleVikor}
              disabled={loading}
              className="w-full rounded-2xl bg-gradient-to-r from-primary to-accent px-6 py-5 text-lg font-bold text-primary-foreground shadow-lg shadow-primary/20 transition hover:shadow-xl disabled:opacity-60"
            >
              {loading ? "⏳ Processando matriz..." : "⚡ Gerar Matriz VIKOR"}
            </button>
            {error && <div className="rounded-lg bg-destructive/10 px-4 py-2 text-sm text-destructive">{error}</div>}
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-4 flex items-baseline justify-between">
              <h3 className="text-lg font-semibold">Pesos dos Critérios</h3>
              <span className="text-xs text-muted-foreground">Soma: <b className="text-foreground">{totalWeight}</b></span>
            </div>
            <div className="space-y-4">
              <Slider label="💰 Custo de Aquisição" value={weights.aquisicao} onChange={(v) => setWeight("aquisicao", v)} color="primary" />
              <Slider label="🔧 Manutenção" value={weights.manutencao} onChange={(v) => setWeight("manutencao", v)} color="primary" />
              <Slider label="⛽ Combustível" value={weights.combustivel} onChange={(v) => setWeight("combustivel", v)} color="primary" />
              <div className="my-2 border-t border-dashed border-border" />
              <Slider label="👥 Capacidade PAX" value={weights.pax} onChange={(v) => setWeight("pax", v)} color="accent" />
              <Slider label="📦 Capacidade de Carga" value={weights.carga} onChange={(v) => setWeight("carga", v)} color="accent" />
            </div>
          </div>
        </div>
      </Section>

      {/* Seção 3 */}
      {result && (
        <Section number="03" title="Resultados VIKOR" subtitle="Ranqueamento de aeronaves aprovadas para a missão">
          <div className="space-y-6">
            <div className="rounded-2xl border-l-4 border-accent bg-accent/5 p-5">
              <div className="text-sm font-semibold text-accent">📏 Distância calculada</div>
              <div className="mt-1 text-2xl font-bold">
                {ORIGIN} → {destino}: <span className="text-accent">{result.distancia_km} km</span>
              </div>
            </div>

            {result.rejeitadas?.length > 0 && (
              <div className="rounded-2xl border-l-4 border-warning bg-warning/10 p-5">
                <div className="mb-2 text-sm font-bold text-warning-foreground">⚠ Aeronaves reprovadas no filtro de autonomia</div>
                <ul className="space-y-1 text-sm text-warning-foreground/80">
                  {result.rejeitadas.map((r) => (
                    <li key={r.id}>• <b>{r.modelo}</b> — {r.motivo}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-3">
              {result.ranking.map((r, i) => {
                const isWinner = i === 0;
                return (
                  <div
                    key={r.id}
                    className={`relative overflow-hidden rounded-2xl bg-card shadow-sm transition ${
                      isWinner
                        ? "border-2 border-success shadow-lg shadow-success/20 md:scale-105"
                        : "border border-border"
                    }`}
                  >
                    {isWinner && (
                      <div className="absolute right-3 top-3 z-10 rounded-full bg-success px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-success-foreground shadow">
                        ★ Melhor Compromisso VIKOR
                      </div>
                    )}
                    <div className="absolute left-3 top-3 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background shadow">
                      {i + 1}º
                    </div>
                    <div className="aspect-video w-full overflow-hidden bg-muted">
                      <img src={r.imagem} alt={r.modelo} className="h-full w-full object-cover" />
                    </div>
                    <div className="p-5">
                      <div className="text-xl font-bold">{r.modelo}</div>
                      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                        <Metric label="Q" value={r.Q} highlight={isWinner} />
                        <Metric label="S" value={r.S} />
                        <Metric label="R" value={r.R} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Section>
      )}

      <div className="no-print mt-12 flex justify-end">
        <button
          onClick={() => window.print()}
          className="rounded-lg border border-border bg-card px-5 py-3 text-sm font-semibold shadow-sm transition hover:bg-secondary"
        >
          🖨 Exportar Relatório PDF
        </button>
      </div>
    </main>
  );
}

function Section({ number, title, subtitle, children }: { number: string; title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section className="mb-12">
      <div className="mb-5 flex items-baseline gap-4">
        <span className="font-display text-3xl font-bold text-primary/30">{number}</span>
        <div>
          <h2 className="text-2xl font-bold">{title}</h2>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function Field({ label, value, onChange, type = "text", placeholder, required }: { label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string; required?: boolean }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-muted-foreground">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none ring-primary/40 focus:ring-2"
      />
    </div>
  );
}

function Slider({ label, value, onChange, color }: { label: string; value: number; onChange: (v: number) => void; color: "primary" | "accent" }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className={`rounded-md px-2 py-0.5 text-xs font-bold ${color === "primary" ? "bg-primary/10 text-primary" : "bg-accent/10 text-accent"}`}>
          peso {value}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className={`h-2 w-full cursor-pointer appearance-none rounded-full bg-muted ${color === "primary" ? "accent-primary" : "accent-accent"}`}
        style={{ accentColor: color === "primary" ? "var(--primary)" : "var(--accent)" }}
      />
    </div>
  );
}

function Metric({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className={`rounded-lg p-2 ${highlight ? "bg-success/10" : "bg-muted"}`}>
      <div className="text-[10px] font-semibold uppercase text-muted-foreground">{label}</div>
      <div className={`font-display text-lg font-bold ${highlight ? "text-success" : "text-foreground"}`}>
        {typeof value === "number" ? value.toFixed(3) : value}
      </div>
    </div>
  );
}
