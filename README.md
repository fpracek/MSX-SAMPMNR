# Sam.Pr Miner — MSX1

Omaggio isometrico a *Manic Miner* per MSX1, MegaROM ASCII8 da 2MB.
20 caverne, una colonna sonora originale sulla schermata dei titoli e
un motore isometrico interamente pre-calcolato in fase di build.

## Come si gioca

- **Frecce sinistra/destra**: cammina lungo la caverna
- **Frecce su/giù**: cambia corsia di profondità (l'asse Z isometrico)
- **Spazio / fire del joystick**: salto
- Raccogli le **3 chiavi** di ogni stanza, poi raggiungi l'**uscita**.
  Quando hai tutte le chiavi il bordo lampeggia: l'uscita è attiva.
- Attenzione a nemici, pericoli e piattaforme che crollano — se muori,
  Sam.Pr riparte dall'inizio della stanza corrente.
- Ogni 5 stanze completate guadagni una vita extra, se sei sotto il
  massimo di 5.
- Completa tutte le 20 stanze per vedere la schermata finale.

## Le 20 caverne

1. Central Cavern
2. The Cold Room
3. The Menagerie
4. Abandoned Uranium Workings
5. Eugene's Lair
6. Processing Plant
7. The Vat
8. Kong Beast
9. Wacky Amoebatrons
10. The Endorian Forest
11. Mutant Telephones
12. Alien Kong Beast
13. Ore Refinery
14. Skylab Landing Bay
15. The Bank
16. The Sixteenth Cavern
17. The Warehouse
18. Amoebatrons' Revenge
19. Solar Power Generator
20. The Final Barrier

Ogni stanza ha un proprio tema grafico, un proprio meccanismo (nemici a
pattugliamento orizzontale/verticale/rettangolare, piattaforme che
crollano al tocco, montacarichi, nastri trasportatori, detriti che
cadono, leve che sbloccano l'uscita, nemici "hopper" che saltano da
piattaforma a piattaforma...) e un nome mostrato all'ingresso.

## Schermata dei titoli

- Musica originale: il valzer *Sul bel Danubio blu* di Strauss, con
  Sam.Pr che balla a tempo sui tasti di un piano disegnato a schermo.
- Dopo un giro completo del valzer senza input, parte una modalità
  "demo" che mostra in sequenza il layout di tutti i 20 livelli.
  Premendo fire o spazio si torna subito al menu.

## Come avviarlo

- **openMSX**: `openmsx -machine <msx1> -carta sampr.rom -romtype ascii8`
- **WebMSX** (webmsx.org): trascina la ROM, oppure impostala come ASCII8
- **blueMSX**: inserisci cartuccia, mapper "ASCII 8KB"
- Richiede un MSX1 con MegaROM ASCII8 (2MB) e almeno 16KB di RAM.

## Architettura

- **MegaROM ASCII8, 2MB (256 banchi da 8KB)**: bank 0-1 fissi (motore +
  tabelle piccole per stanza), bank 2-3 fissi (sfondo di Central
  Cavern), banchi successivi commutabili a coppie per lo sfondo di
  ogni altra stanza, oltre a banchi dedicati per maschere di
  occlusione, piattaforme che crollano e la grafica del titolo.
- **Architettura multi-stanza**: una tabella descrittore per stanza
  (`room_tab`, in ROM) viene copiata in una struttura RAM ad ogni
  ingresso in una stanza (`room_start`), da cui tutte le routine di
  gioco leggono mappa/chiavi/nemici/uscita/pericoli — aggiungere una
  stanza è un cambiamento di dati, non di codice.
- **Vera prospettiva isometrica 2:1** (sx = 120+wx-wz, sy = 56+(wx+wz)/2-h):
  pavimento a rombi, pareti prospettiche, blocchi a diamante.
- **Sfondo pre-renderizzato in ROM**: ogni stanza (pattern + color
  table Screen 2, 12KB) è calcolata da uno script Python in fase di
  build e salvata in ROM; lo Z80 la copia in VRAM con un blocco LDIRVM
  — zero rendering a runtime.
- **Fisica a virgola fissa 8.8**: gravità e velocità di salto tarate
  per un salto pari a un livello di altezza.
- **Sam.Pr**: sprite hardware compositi multi-colore, 14 pose (ciclo di
  cammino nelle 4 direzioni + 2 pose per il ballo finale).
- **PSG a 3 canali**: musica a 2 canali (titoli e in-game, entrambe
  trascritte a orecchio) + canale dedicato agli effetti sonori.

## Struttura dei sorgenti

- `src/main.asm` — motore completo (Z80, sjasmplus)
- `src/leveldata.asm`, `src/*.bin` — dati di livello generati da
  `tools/gen_iso.py`
- `tools/gen_iso.py` — generatore di grafica/livelli: ogni stanza è
  definita come uno "spec" Python (tema, piattaforme, nemici, pericoli,
  uscita); modifica qui, rilancia, riassembla
- `tools/sam_sprites.c`, `tools/gen_title_deco.py`, `tools/fonts.c` —
  altri asset generati (sprite di Sam.Pr, grafica del titolo, font)
- `test/*.tcl` — test automatici headless con openMSX
- `Makefile` — ricostruisce tutto

## Come ricompilare

```
python tools/gen_iso.py
sjasmplus src/main.asm
```

Produce `build/sampr.rom` (2.097.152 byte esatti).
