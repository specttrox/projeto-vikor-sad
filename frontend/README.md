# Painel de Inteligência Logística de Aviação

Dashboard interativo para cadastro, filtragem e ranqueamento de aeronaves para missões logísticas usando o algoritmo VIKOR.

---

## Como rodar localmente

### Pré-requisitos

- [Node.js](https://nodejs.org/) 18+ (recomendado: 20+)
- [Bun](https://bun.sh/) (usado como gerenciador de pacotes e runtime)

### Passo a passo

1. **Clone o repositório e entre na pasta:**
   ```bash
   git clone <url-do-seu-repo>
   cd <nome-da-pasta>
   ```

2. **Instale as dependências:**
   ```bash
   bun install
   ```

   Se Bun nao estiver instalado, use npm:
   ```bash
   npm install --no-package-lock --legacy-peer-deps
   ```

3. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```
   Edite `.env` com as credenciais do Supabase e a URL do backend.

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   bun dev
   ```

   Com npm:
   ```bash
   npm run dev
   ```

5. **Abra no navegador:**
   Acesse `http://localhost:3000` (ou a porta indicada no terminal).

### Build para produção

```bash
bun run build
```

Com npm:
```bash
npm run build
```

O resultado do build fica em `.output/`.

---

## Publicar no Vercel

Sim, é possível publicar no **Vercel**, mas com uma ressalva importante:

Este projeto usa **TanStack Start**, que roda em runtime serverless (Worker). A Vercel suporta deployments com Edge/Serverless Functions, então o deploy funciona normalmente.

### Passos para deploy na Vercel

1. **Faça push do código** para o GitHub.

2. **Conecte o repositório** na Vercel:
   - Vá em [vercel.com/new](https://vercel.com/new)
   - Importe o repositório do GitHub

3. **Configure as variáveis de ambiente** no dashboard da Vercel:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_PUBLISHABLE_KEY`

4. **Deploy.** A Vercel detecta o `vite build` automaticamente.

### Alternativa sem custo: Lovable Cloud

Se você gerou esse projeto aqui na Lovable, a forma mais simples de deixá-lo online é usar o botão **"Publish"** na interface da Lovable — já está configurado para deploy automático.

---

## Tecnologias

- **Framework:** TanStack Start (React 19 + SSR)
- **Build tool:** Vite 7
- **Estilos:** Tailwind CSS v4
- **Banco de dados:** Supabase (PostgreSQL + PostgREST)
- **Gerenciador de pacotes:** Bun
