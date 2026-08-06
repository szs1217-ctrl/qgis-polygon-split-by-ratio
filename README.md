# Polygon Split By Ratio (QGIS plugin)

Splits a selected polygon into any number of parts according to given
area ratios (e.g. `3,2,1`). The cut lines run parallel to a reference
line the user selects (e.g. a road, or a compartment boundary), which
makes this useful for forestry stand/compartment subdivision and
similar cadastral or planning tasks.

Magyarul: a kiválasztott poligont tetszőleges számú részre osztja a
megadott területarányok szerint (pl. `3,2,1`), a vágóvonalak egy
kiválasztott referenciavonallal (pl. út, tag-/részlethatár)
párhuzamosak. Hasznos erdészeti részlet-felosztáshoz és hasonló
kataszteri/tervezési feladatokhoz.

## Usage / Használat

1. Have a polygon layer (the shape to split) and a line layer
   (defines the cut direction) loaded in QGIS.
2. Open **Plugins → Polygon Split By Ratio**.
3. Select the polygon layer, the line layer, and enter the ratios
   (comma-separated, e.g. `3,2,1`).
4. Click OK — a new memory layer `felosztott_reszek` is created with
   the resulting parts (`resz_sorszam`, `arany`, `terulet` fields).

Ha egyik rétegen sincs kijelölés és a rétegnek pontosan egy eleme van,
azt használja a plugin automatikusan; egyébként pontosan egy elemet
kell kijelölni mindkét rétegen.

## License

GPL v2+ — see [LICENSE](LICENSE).
