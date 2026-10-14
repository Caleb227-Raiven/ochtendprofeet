# De Ochtendprofeet

Een dagelijkse Nederlandstalige podcast (max. 20 minuten) over AI, marketing-technologie, data/CRM en softwareontwikkeling, gepresenteerd door Nina en Mirthe.

## Hoe het werkt

1. Elke werkdag om 07:22 doet een geplande Claude-taak research en zet het script in `episodes/JJJJ-MM-DD.md`.
2. De GitHub Action **Maak podcastaflevering** ziet het nieuwe script, maakt er met [edge-tts](https://github.com/rany2/edge-tts) een MP3 van (vaste stem per presentator) en zet die in `docs/audio/`.
3. `scripts/build_feed.py` werkt de podcastfeed `docs/feed.xml` bij (de laatste 30 afleveringen; oudere MP3's worden verwijderd).
4. GitHub Pages publiceert de map `docs/`, dus de feed staat op `https://<gebruiker>.github.io/<repo>/feed.xml`.

## Eenmalige instelling

1. Maak een **openbare** repository en zet deze bestanden erin.
2. Ga naar **Settings → Pages**. Kies onder *Build and deployment* bij *Source* voor **Deploy from a branch**, met branch `main` en map `/docs`.
3. Ga naar **Settings → Actions → General**. Zet *Workflow permissions* op **Read and write permissions**.
4. Voeg de feed-URL toe in je podcast-app:
   - Pocket Casts: *Zoeken → plak URL*
   - Apple Podcasts: *Bibliotheek → … → Volg een programma via URL*
   - Overcast: *+ → Add URL*

   Spotify ondersteunt geen eigen RSS-feeds.

## Stemmen aanpassen

Pas in `scripts/make_episode.py` het blok `VOICES` aan. Een lijst met beschikbare stemmen krijg je met `edge-tts --list-voices | grep nl-`.

## Handmatig testen

Ga naar **Actions → Maak podcastaflevering → Run workflow**. Dit maakt audio voor elk script dat nog geen MP3 heeft. Lokaal testen zonder echte spraak kan met `FAKE_TTS=1 python scripts/make_episode.py episodes/<datum>.md`.
