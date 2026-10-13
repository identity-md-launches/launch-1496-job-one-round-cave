# Gathering 13 image prompt

Used the assignment's installed `mcp__image__generate_image` tool, once. It
returned a 1536×1024 PNG despite the requested 1024×1024 size; this was a pigment
insert, not the final wall. The insert was inspected and overwritten in place
with the 1254×1254 finished ancestral wall after confined compositing. No extra
image was retained. The final wall and JPEG were inspected visually.

Exact prompt:

> Use case: illustration-story. Create one isolated prehistoric cave pigment motif for compositing onto vacant rock of an ancestral cave painting. On a perfectly plain white background, draw an uneven charcoal oval loop enclosing four small irregular pebbles: one red ochre, one yellow ochre, one chalk white with a charcoal outline, one charcoal black. Two short ochre trails enter from the left and join at the enclosing loop. It represents separate evidence becoming one portable bundle. Use rough thumb-daubed earth pigments, sparse worn burnt-stick strokes, irregular handmade shapes, bare gaps, Lascaux or Chauvet cave painting feel. Compact horizontal motif centered with very wide blank white margins, no rock backdrop or shadows. No letters, numbers, symbols resembling writing, captions, signature, logo, watermark, frame, people, animals, hands or handprints. Only this small primitive loop, four pebbles and two joining trails. Opaque white background; keep all pigment comfortably inside the central half of image.

`finish_wall13.py` alpha-blended only the new pigment inside vacant rock at
(900,120,240,125). Outside that rectangle the ancestral pixels are identical.
Most chalk-white pigment was removed along with the white background; this is
recorded as a visual limitation. The existing Pepe and both five-digit hands
were preserved. `checks/round-13/image-preservation.json` records the review.
