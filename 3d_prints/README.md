# Enlairats — 3D print guide

STL files and print notes for the physical edition of **Enlairats**.

Photos of a finished print will be added under `photos/` later.

All parts in this folder are designed for **PLA**, **no supports**, and (except the Chicago screws) print at **100% scale**.

---

## Full game — what to print

| Item | File(s) | Qty | Notes |
| ---- | ------- | --- | ----- |
| Board | `stl/board/board.stl` | 1 | Play surface (4×4) |
| Masia Freixa | `stl/buildings/Masia_Freixa.stl` | 4 | Height 1 — print four copies |
| Casa Amatller | `stl/buildings/Casa_Amatller.stl` | 4 | Height 2 — print four copies |
| Torre Galatea | `stl/buildings/Torre_Galatea.stl` | 4 | Height 3 — print four copies |
| Sagrada Família | `stl/buildings/Sagrada_Familia.stl` | 4 | Height 4 — print four copies |
| Clue tokens | `stl/clues/Clues_all.stl` | 1 plate | Full set of border clues |
| Box body | `stl/box/box_body.stl` | 1 | Remix — see [Box](#box-remix) |
| Box lid | `stl/box/box_lid.stl` | 1 | Remix — see [Box](#box-remix) |
| Box logo | `stl/box/box_logo.stl` | 1 | Glue onto the lid |
| Chicago screw (rules binding) | [MakerWorld model](https://makerworld.com/es/models/1420755-chicago-screws) | 1 | Print at **65%** scale — binds the paper rulebook |
| Magnets (box) | — (hardware) | 8 | 6×3 mm, for body and lid |

`Clues_nums_1234.stl` is available if you prefer to print clue pieces in smaller batches. `Clues_num_2.stl` is an optional **supplement**: the clue “2” is used more often, so you may want extras.

---

## Recommended print settings

| Part | Layer height | Infill | Other |
| ---- | ------------ | ------ | ----- |
| Buildings | 0.08 mm | 10% | One colour per building (single-extruder OK) |
| Clue tokens | 0.08 mm | 15% | Dual-colour look via filament swap (see below) |
| Board | 0.4 mm | 15% | |
| Box body & lid | 0.4 mm | 10% | Needs 8× magnets 6×3 mm |
| Box logo | 0.08 mm | 10% | Glue onto the lid after printing |
| Chicago screws | 0.16 mm | 15% | **65%** scale, 4 walls |

Entire project: **PLA**, **no supports**.

### Colour tips (single-extruder)

- Print each **building** type in a **different colour** so heights are easy to tell apart at the table.
- For **clue tokens**, start in one colour and **swap filament near the end of the print** so the top layers (the numbers) use a contrasting colour and stand out.

---

## Box (remix)

The box (`box_body.stl`, `box_lid.stl`) is a remix of:

[Magnetic Box (Parametric)](https://www.printables.com/model/643648-magnetic-box-parametric) by the original author on Printables.

That work is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Attribution to the original model is required when you share the remixed box.

The Enlairats **logo** insert (`box_logo.stl`) is original to this project; glue it onto the lid. Fit **8** magnets (**6×3 mm**) into the body and lid as designed.

---

## Chicago screws (rulebook)

To bind the printed paper rules (see `2d_prints/`), you can print Chicago screws from:

[Chicago screws on MakerWorld](https://makerworld.com/es/models/1420755-chicago-screws)

Recommended settings for Enlairats: **65%** scale, **0.16 mm** layer height, **4 walls**, **15%** infill. One screw set is enough for the rulebook.

---

## Folder layout

```text
3d_prints/
├── README.md          # this guide
├── photos/            # photos of a finished print (coming soon)
└── stl/
    ├── board/         # board.stl
    ├── buildings/     # one STL per building (print ×4 each)
    ├── clues/         # Clues_all + optional supplements
    └── box/           # body, lid, logo
```

---

## License

Unless noted above, files in this folder follow the repository license: **CC BY-NC 4.0** (see root `LICENSE` and `NOTICE`). Non-commercial use only; attribution required.

The remixed **box body and lid** additionally require compliance with the original model’s **CC BY 4.0** terms (credit the Printables source linked above).
