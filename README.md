# Diktanalyse

En app for å automatisk annotere enderim, anaforer og bokstavrim i dikt eller andre tekster der linjeskiftet er meningsbærende.

## Installasjon

### Med Docker (anbefalt)

- [Docker](https://www.docker.com/get-started) og Docker Compose

### Lokal utvikling

- Installer [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) for å håndtere python-versjoner og tredjepartsavhengigheter.

1. Kjør `uv sync` i terminalen for å installere pakker som trengs for å kjøre diktanalyse-appen.

2. **Konfigurer miljøvariabler** (valgfritt):

   ```bash
   cp .env.example .env
   ```

   Endre miljøvariabler i `.env` for å sette Flask-innstillinger og Google Cloud Build-innstilllinger.

## Kjør appen

### Docker (anbefalt)

```bash
# Build the image
docker compose build

# Run the container
docker compose up

# Alternatively, run in detached mode (background)
docker compose up -d
```

Appen er tilgjengelig fra `http://localhost:5000`.

For å stoppe containeren:

```bash
# Stop the container
docker compose down
```

### Lokal utvikling (uv)

```bash
uv run python app.py
```

Appen blir tilgjengelig fra `http://localhost:5000`

## Bruk

1. Åpne nettleseren og gå til `http://localhost:5000`
2. Velg et dikt fra `NORN Dikt`-korpuset, eller fyll inn egen tekst
3. Klikk på "Annoter dikt"
4. Velg hvilke lyriske trekk du vil få markert i diktet.

## Publisere appen

```bash
gcloud builds submit --region=europe-north1 --config cloudbuild.yaml
```

## Hent `NORN dikt` fra GitHub

Prosjektet inkluderer et skript (`parse_poems.py`) for å hente og formatere data fra GitHub-repoet [norn-uio/norn-poems](https://github.com/norn-uio/norn-poems).

```bash
python parse_poems.py --github
```

**Med en maksgrense for antall dikt:**

```bash
python parse_poems.py --github --max-files=10
```
