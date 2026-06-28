# WebP Converter — Webapp + Landing Page
## Documento de Formalização da Ideia

---

## 1. Visão geral

Transformar o CLI **webp-converter** (já existente, Python/Pillow) em um **serviço web gratuito**, voltado a devs e freelancers que precisam converter assets de projetos (PNG/JPEG → WebP) em lote, com um fluxo de revisão antes da execução e um relatório pensado para colar direto em um assistente de IA (Claude, Cursor, Copilot) e atualizar automaticamente as referências no código.

O CLI continua existindo e sendo mantido como está — é o canal para quem já validou o serviço no navegador e quer automatizar em CI/build pipeline. O webapp é a porta de entrada e a vitrine do diferencial.

**Modelo de negócio:** gratuito, sustentado por doações (ex: Buy Me a Coffee / GitHub Sponsors) e possivelmente ads discretos no futuro.

**Público-alvo:** devs e freelancers otimizando assets de projetos web.

---

## 2. Por que webapp (não extensão)

| Critério | Webapp | Chrome Extension |
|---|---|---|
| Caso de uso | Pasta/projeto inteiro, lote | Imagem isolada numa página |
| Acesso a filesystem | Via upload (zip ou pasta) | Limitado/inexistente |
| Reuso do código Python | Direto (backend) ou portável para WASM | Exigiria reescrita completa em JS/WASM |
| Fluxo plano → execução | Natural, com tabela/UI de revisão | Difícil de encaixar numa popup pequena |
| Alinhamento com público (devs) | Alto — fluxo de projeto de código | Baixo — fluxo é mais de designer/marketeiro |

Decisão: **webapp**.

---

## 3. Diferencial competitivo

Concorrentes (Squoosh, TinyPNG, CloudConvert, ezgif) resolvem conversão solta de imagem por imagem. Squoosh não tem automação/batching real; TinyPNG limita lote gratuito a poucas imagens por vez. Nenhum oferece:

1. **Plano revisável antes de executar** — tabela com estimativas de economia, o usuário pode remover/ajustar itens antes de confirmar.
2. **Relatório "AI-ready"** — bloco de texto formatado para colar em um assistente de IA, que atualiza automaticamente as referências de imagem no código (`<img src="logo.png">` → `.webp`, imports, etc.). **Esse é o principal gancho de marketing.**
3. **Consciência de estrutura de projeto** — preserva hierarquia de pastas, ignora diretórios já otimizados (ex: `optimized/`).
4. **Processamento client-side (WASM)** — privacidade ("seus arquivos nunca saem do navegador") e custo zero de servidor para imagem pesada, viabilizando o modelo gratuito.

Mensagem de posicionamento sugerida:
> "Convert your project's images to WebP, then paste one block into your AI assistant and every reference in your codebase gets updated automatically."

---

## 4. Landing Page

**Objetivo:** comunicar o diferencial em poucos segundos e levar direto à ação (converter ou baixar o CLI).

**Estrutura sugerida (single page):**

1. **Hero**
   - Headline focada no diferencial AI-ready (ver mensagem acima)
   - Sub-headline: grátis, processamento local no navegador, sem upload pra servidor
   - CTA primário: "Convert your images" (rola até a zona de drag-n-drop)
   - CTA secundário: "Use the CLI instead" (rola até seção de download/instalação)

2. **Zona de drag-n-drop** (ver seção 5)
   - Componente embutido na própria landing page, sem precisar de página separada
   - Aceita pasta inteira ou .zip

3. **Como funciona (3 passos)**
   - Solte seus arquivos → Revise o plano → Baixe convertido + relatório

4. **Demonstração do relatório AI-ready**
   - Mostrar um exemplo real do bloco de texto gerado, com print ou bloco de código
   - Reforça visualmente o diferencial #2

5. **Comparativo rápido** (tabela pequena)
   - WebP Converter vs. "outros conversores" — colunas: lote ilimitado, plano revisável, relatório p/ IA, privacidade local

6. **Seção CLI**
   - Para quem quer automatizar: comando de instalação (`pipx install webpconverter`), link pro repositório GitHub
   - Frase de funil: "Validou no navegador? Automatize no seu pipeline."

7. **Footer**
   - Link de doação (Buy Me a Coffee / GitHub Sponsors)
   - Link GitHub, licença, contato

---

## 5. Fluxo do Webapp (drag-n-drop)

**Passo 1 — Upload**
- Drag-n-drop de pasta (via `<input webkitdirectory>` ou arraste de pasta do SO) ou de arquivo `.zip`
- Aceita também seleção manual de múltiplos arquivos como fallback

**Passo 2 — Scan + Plano**
- Reaproveita lógica do `scanner.py`/`estimator.py` (portada para WASM ou via backend leve)
- Exibe tabela: arquivo, tamanho atual, tamanho estimado em WebP, % de economia
- Usuário pode desmarcar itens antes de confirmar
- Ignora automaticamente diretórios já processados (ex: `optimized/`)

**Passo 3 — Execução**
- Conversão roda (idealmente client-side via WASM/libwebp, para privacidade e custo zero de servidor)
- Barra de progresso simples

**Passo 4 — Resultado**
- Download do `.zip` com arquivos convertidos, preservando estrutura de pastas original
- Exibição do **relatório AI-ready** em bloco de texto copiável (botão "Copy for AI assistant")
- Botão "Download CLI" para quem quer repetir esse processo localmente/em CI (ver seção 6)

---

## 6. Integração com o CLI (opção de download)

A landing page e o webapp devem sempre oferecer, em paralelo ao uso no navegador, o caminho para o CLI:

- **Botão/seção fixa**: "Prefer the command line? Install the CLI" com o comando `pipx install webpconverter` e link para o repositório
- **No resultado do webapp**: depois de converter no navegador, sugerir "Quer rodar isso automatizado no seu projeto ou CI? Use o CLI" — funция de funil, não force a escolha
- **Consistência de relatório**: o relatório AI-ready gerado pelo webapp deve ter o mesmo formato do gerado pelo CLI, para que a experiência (e o prompt que o usuário cola na IA) seja idêntica nos dois caminhos

---

## 7. Stack técnica sugerida

- **Frontend:** página única (HTML/JS, sem framework pesado necessário) ou React simples, com drag-n-drop nativo
- **Processamento de imagem:** prioridade para WASM (libwebp compilado para WASM) rodando 100% no navegador — sustenta o modelo gratuito sem custo de servidor pesado
- **Backend (se necessário):** leve, apenas para servir a página e, no início, possivelmente para a estimativa/plano caso a portagem WASM completa leve mais tempo — pode ser implementado depois como fallback enquanto WASM não está pronto
- **Hospedagem:** estática (Vercel/Netlify/Cloudflare Pages) é suficiente se o processamento for client-side, mantendo custo zero alinhado ao modelo gratuito

---

## 8. Próximos passos (a definir)

- [ ] Validar viabilidade de portar `converter.py`/`estimator.py` para WASM ou definir fallback de backend leve
- [ ] Definir wireframe da landing page e da zona de drag-n-drop
- [ ] Especificar formato exato do relatório AI-ready (mesmo entre webapp e CLI)
- [ ] Escolher provedor de hospedagem e domínio
- [ ] Configurar canal de doação (Buy Me a Coffee / GitHub Sponsors)
