# Gestionale Tattoo Beauty Saloon — Web v1

Applicazione web pronta per GitHub e Render.

## Contenuto
- Login protetto
- Dashboard
- 56 referenze / 106 pezzi già caricati
- Ricerca prodotti
- Carico e scarico magazzino
- Vendite con scarico automatico
- Storico movimenti
- Fornitori
- Esportazione CSV
- Database SQLite in locale o PostgreSQL online

## Prova locale
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
set ADMIN_PASSWORD=una-password-sicura   # Windows
export ADMIN_PASSWORD=una-password-sicura # Mac/Linux
python app.py
```
Apri `http://127.0.0.1:5000`.

## Pubblicazione Render
1. Crea un repository GitHub vuoto.
2. Carica tutti i file di questa cartella nella radice del repository.
3. In Render scegli **New > Blueprint**.
4. Collega il repository GitHub.
5. Render leggerà `render.yaml` e creerà Web Service + PostgreSQL.
6. Quando richiesto, imposta `ADMIN_PASSWORD` con una password lunga e unica.
7. Al termine apri l'indirizzo `.onrender.com` e accedi con utente `admin`.

## Sicurezza
- Cambia sempre `ADMIN_PASSWORD`.
- Non condividere la password.
- Attiva l'autenticazione a due fattori su GitHub, Render e Aruba.
- Per uso continuativo conviene poi valutare un piano con backup e disponibilità adeguati.
