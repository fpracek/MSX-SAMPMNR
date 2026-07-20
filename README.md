# Sam.Pr Miner — prototipo MSX1

Omaggio isometrico a Manic Miner per MSX1 (16KB RAM) su MegaROM ASCII8,
come da progetto. Prototipo giocabile della prima caverna.

## Come si gioca

- **Frecce sinistra/destra**: cammina lungo la caverna
- **Frecce su/giù**: cambia corsia di profondità (l'asse Z isometrico)
- **Spazio**: salto
- Raccogli le **3 chiavi**, poi raggiungi la **porta ciano** a destra.
  Quando hai tutte le chiavi il bordo lampeggia: la porta è attiva.
- Se cadi nel vuoto, Sam.Pr ricompare all'inizio.

## Come avviarlo

- **openMSX**: `openmsx -machine <msx1> -carta sampr.rom -romtype ascii8`
- **WebMSX** (webmsx.org): trascina la ROM, oppure impostala come ASCII8
- **blueMSX**: inserisci cartuccia, mapper "ASCII 8KB"
- Funziona su qualsiasi MSX1 con 16KB di RAM (usa solo C000-F37F).

## Architettura (fedele al progetto)

- **MegaROM ASCII8**: bank 0 = motore, bank 1 = riservato,
  bank 2 = grafica, bank 3 = mappe livello. Pronta a crescere fino a 4MB.
- **Slot init**: ENASLT abilita la cartuccia in pagina 2 (8000-BFFF).
- **Vera prospettiva isometrica 2:1** (sx = 120+wx-wz, sy = 56+(wx+wz)/2-h):
  pavimento a rombi, due pareti prospettiche, blocchi a diamante.
- **Sfondo pre-renderizzato nella MegaROM**: la stanza completa (pattern +
  color table Screen 2, 12KB) e' calcolata dal generatore Python e salvata
  in ROM. Lo Z80 la copia in VRAM con un blocco LDIRVM: zero rendering
  a runtime, filosofia "pre-calcola tutto" del progetto.
- Le **chiavi** sono un livello grafico separato: disegnate all'avvio,
  cancellate ripristinando lo sfondo dalla ROM alla raccolta.
- **Mappa 3D** grid[z][y][x] 13x8x3 in ROM, copiata in RAM per gli
  oggetti raccoglibili e (in futuro) le piattaforme che crollano.
- **Fisica a virgola fissa 8.8**: gravità 0.125 px/f², salto 3 px/f.
- **Sam.Pr**: 2 sprite hardware 16x16 sovrapposti (bianco + rosso),
  4 pose (2 frame x 2 direzioni).
- **PSG**: canale C dedicato agli effetti (salto = rampa ascendente,
  chiave = blip acuto), canali A+B liberi per la musica futura.

## Struttura dei sorgenti

- `src/main.asm` — motore completo (Z80, sjasmplus)
- `src/gfx.asm`, `src/level.asm` — generati da `tools/gen_gfx.py`
- `tools/gen_iso.py` — editor grafica/livelli: modifica i disegni o la
  mappa qui, rilancia, riassembla
- `test/*.tcl` — test automatici headless con openMSX
- `Makefile` — `make gfx && make` per ricostruire tutto

## Prossimi passi suggeriti

1. Nemici con pattugliamento su binari fissi (+ il "gabinetto" volante)
2. Piattaforme che crollano (la grafica CRUMB c'è già)
3. Barra dell'aria + vite + HUD punteggio
4. ~~Musica: Grieg in-game / Danubio Blu nei titoli (Arkos Tracker -> PSG)~~
   fatto: schermata titoli con Sam.Pr che salta sui tasti di un piano
   a tempo col Danubio Blu (player PSG hand-coded, canali A+B, vedi
   `music_init`/`music_update` in `src/main.asm`). Trascrizione a
   orecchio del tema, non da spartito: da verificare/ritoccare in
   emulatore.
5. Mascheramento sprite dietro i blocchi in primo piano (tabella in ROM)
6. Altre caverne (il formato mappa già lo permette)
