# Assets générés pour la correction visuelle

Outil intégré `image_gen` utilisé en génération, sans cible à modifier. Les
quatre captures utilisateur sont des références de conception ; aucune capture
complète ou image commerciale n’est intégrée au skin comme interface.

## Photo de salon

Fichier source : `assets/source/lounge-reference-generated.png`.
Copie runtime : `skins/MetrixNEOAdvanced/assets/lounge-reference.png`.

Prompt exact :

> Use case: photorealistic-natural. Create ONLY an original decorative photograph asset for the left panel of an Enigma2 television skin. No UI, NO text, no logos, no borders, no clock. Portrait 4:5 composition, perfectly straight-on view of a premium small living room at dusk: large dark flat-screen TV centered over low walnut media console, tall panoramic window directly behind/above the TV showing distant city lights and warm sunset fading into deep blue sky, dark gray curtains, small warm amber floor lamp at left, leafy small plant on right, quiet sofa edge foreground. Warm golden lighting in the left half and deep navy shadows, elegant restrained realistic interior. Match the little living room photograph seen on the left of a navy TV receiver dashboard, without recreating any interface. Frame tightly so the TV, lamp, and window are readable when scaled to a 420 by 480 pixel panel. This will be an independent image asset embedded in a real coded skin. No people, no brands, no interface controls, no lettering.

## Ancienne interprétation de la ville — retirée du runtime

Fichier source : `assets/source/scenic-reference-generated.png`.
Copie runtime supprimée après clarification : cette scène représente un exemple
de contenu, pas un papier peint. Le choix final est un fond bleu nuit uni.
Le fichier source est conservé pour la traçabilité de la génération précédente.
Après la demande de vidéo en cours autour du menu contextuel, il sert aussi à
illustrer cette vidéo dans la simulation locale, avec un marquage explicite.
Il ne devient jamais un fond du skin et reste absent des IPK.

Prompt exact :

> Use case: photorealistic-natural. Asset type: pre-blurred decorative 16:9 navy city backdrop for an Enigma2 TV skin, no UI. A dusk city viewed from a rooftop or window, intentionally very strongly defocused. Deep midnight blue sky, vague dark architecture and a few soft warm amber window bokeh circles concentrated toward the left and right edges. A distant stone tower with softly lit windows at the extreme right edge. Central 75 percent must be extremely dark navy and visually quiet so native television channel text panels can overlay it. Restrained colors, photographic real lens bokeh, not abstract illustration. Very dark, no readable signs, no logos, no people, no television controls, no text, no frames. Landscape 1920 by 1080, pre-blurred image, no runtime blur needed.

## Illustration de programme fictif, aperçu uniquement

Fichier : `previews/fixtures/programme-demo-generated.png`.
Ce fichier n’est pas sous skins/ et n’est pas inclus dans les IPK. Les images
programmes au runtime exigent une correspondance d’événement et un catalogue autorisé.

Prompt exact :

> Create one original cinematic still used ONLY as a clearly-labelled demo fixture in a television skin preview, never as actual EPG artwork. Wide panoramic 21:9 composition. Fictional older silver-haired man in his late fifties, dark jacket, medium close-up, holding a mobile phone to his right ear, worried attentive expression, at night in a rain-slick city with blurry dark blue-gray lights behind him. Man on the left half and moody defocused blue-black urban lights on the right. Cinematic photographic realism, cold midnight blue color grading, realistic skin, restrained contrast. Not an identifiable actor, not a recreation of a film, no movie title, no text, no logos, no border, no graphic UI, no watermarks. The composition should remain readable when shown in a 600 by 270 pixel event-artwork area on a dark navy receiver screen.
