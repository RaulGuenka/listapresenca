# Lista WhatsApp — Checklist de Kit por Equipe

App em Streamlit que reproduz a tabela de checkboxes das colunas **D:I** da
planilha `Batedores - Equipes` (aba **Lista WhatsApp**), com persistência dos
dados no Supabase.

Cada equipe tem uma tabela com um checkbox por batedor para cada item:

| Coluna | O que marca |
|---|---|
| Presença | Batedor confirmado/presente |
| Apito | Apito entregue |
| Lanterna | Lanterna entregue |
| Lanterna Sinalizadora | Lanterna sinalizadora entregue |
| Colete | Colete entregue |
| Caixinha | Contribuição da caixinha |
| Devolução | Item devolvido ao final |

---

## Estrutura dos arquivos

```
lista_whatsapp_app.py              # App Streamlit
supabase_schema.sql                # Cria a tabela do zero (ambiente novo)
supabase_seed.sql                  # Popula a tabela com as 15 equipes / 35 nomes da planilha
supabase_migration_add_columns.sql # Migração: adiciona Caixinha e Devolução numa tabela já existente
```

---

## 1. Configurar o banco (Supabase)

**Se é a primeira vez (tabela ainda não existe):**

1. Abra o seu projeto no [Supabase](https://supabase.com) → **SQL Editor**
2. Rode `supabase_schema.sql` — cria a tabela `kit_checklist` com todas as
   colunas, trigger de `updated_at` e as policies de RLS.
3. Rode `supabase_seed.sql` — insere as equipes e nomes extraídos da planilha
   original. É idempotente (pode rodar de novo sem duplicar).

**Se a tabela já existe e você só precisa adicionar Caixinha/Devolução:**

- Rode apenas `supabase_migration_add_columns.sql`. Não apaga dados já
  marcados.

### Pegando a URL e a chave

Em **Project Settings → API** no Supabase:
- `Project URL` → vai virar `SUPABASE_URL`
- `anon public key` → vai virar `SUPABASE_KEY`

> ⚠️ A policy de RLS criada no schema libera leitura/escrita para qualquer
> pessoa que tenha a `anon key` (uso interno, sem login). Se depois você
> quiser restringir por usuário, ajuste as policies em `supabase_schema.sql`.

---

## 2. Rodar localmente (via VSCode/terminal)

Não precisa subir pro GitHub para isso — só rodar na sua máquina:

```bash
pip install streamlit pandas supabase
```

Crie o arquivo `.streamlit/secrets.toml` na raiz do projeto:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "sua-anon-key"
```

Rode o app:

```bash
streamlit run lista_whatsapp_app.py
```

Abre automaticamente em `http://localhost:8501`.

---

## 3. Deploy no Streamlit Community Cloud (opcional)

Necessário só se outras pessoas (ex: líderes de equipe) forem marcar os
checkboxes remotamente, pelo celular etc.

1. Suba `lista_whatsapp_app.py` (e um `requirements.txt` com
   `streamlit`, `pandas`, `supabase`) para um repositório no GitHub.
2. **Não** suba o `.streamlit/secrets.toml` — adicione `.streamlit/` no
   `.gitignore`.
3. No painel do Streamlit Cloud, ao criar o app, vá em **Settings → Secrets**
   e cole:
   ```toml
   SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
   SUPABASE_KEY = "sua-anon-key"
   ```
4. Aponte o deploy para `lista_whatsapp_app.py`.

---

## Como o app funciona

- Ao abrir, busca todos os registros da tabela `kit_checklist` no Supabase,
  agrupados por equipe.
- Cada equipe aparece em um `expander` com uma tabela editável
  (`st.data_editor`), um checkbox por item de kit.
- Quando você marca/desmarca algo, o app compara com o valor anterior e grava
  só o que mudou de volta no Supabase (`update`).
- Botão **🔄 Recarregar do banco** força buscar os dados mais recentes (útil
  se mais de uma pessoa estiver usando ao mesmo tempo).
- Métricas no topo mostram o progresso geral (quantos já receberam cada item).
- Botão **⬇️ Baixar checklist (CSV)** exporta o estado atual.

---

## Adicionando novas colunas no futuro

1. Escreva um `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` (como em
   `supabase_migration_add_columns.sql`) e rode no SQL Editor do Supabase.
2. No `lista_whatsapp_app.py`, adicione a nova coluna no dicionário
   `KIT_COLS` (chave = nome da coluna no banco, valor = rótulo exibido na
   tela) e no `.select(...)` dentro de `fetch_checklist()`. O resto do app
   (métricas, tabelas, export) já se ajusta automaticamente.
