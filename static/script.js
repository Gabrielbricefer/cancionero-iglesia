// ============================================================
// ESCALAS MUSICALES COMPLETAS (12 semitonos)
// ============================================================
const latinScale = ['Do', 'Do#', 'Re', 'Re#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si'];
const americanScale = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

// ============================================================
// LISTA DE SUFIJOS DE ACORDES VÁLIDOS (ordenados por longitud para priorizar los más largos)
// ============================================================
const chordSuffixes = [
    // Los más largos primero para evitar conflictos
    'mMaj7', 'maj7', 'm7', 'm9', 'm6', 'add9', 'sus4', 'sus2',
    '7sus4', '6add9', 'Maj7♭5', 'Maj7b5', 'm7b5', 'dim7',
    'm', '7', 'aug', 'dim', 'sus', '5', '6', '9', '11', '13',
    'M7', 'maj', 'min', 'mM7', 'mM9'
];

// ============================================================
// FUNCIÓN PARA EXTRAER RAÍZ Y SUFIJO DE UN ACORDE
// ============================================================
function extractRootAndSuffix(chord) {
    if (!chord || chord.trim() === '') return null;
    
    // Limpiar espacios
    chord = chord.trim();
    
    // Intentar cada sufijo (de más largo a más corto)
    for (let suffix of chordSuffixes) {
        // Buscar el sufijo al final del acorde
        if (chord.endsWith(suffix)) {
            const root = chord.slice(0, -suffix.length);
            // Verificar que la raíz sea una nota válida
            if (root && root.length > 0) {
                // Verificar si la raíz es válida
                const normalizedRoot = normalizeNote(root);
                if (normalizedRoot) {
                    return { root: root, suffix: suffix };
                }
            }
        }
    }
    
    // Si no se encontró sufijo, todo es la raíz
    return { root: chord, suffix: '' };
}

// ============================================================
// MAPEO DE NOTAS (case insensitive)
// ============================================================
function normalizeNote(note) {
    if (!note) return null;
    
    // Mapeo de notas con posibles variantes
    const noteMap = {
        'do': 'Do', 'c': 'C',
        'do#': 'Do#', 'c#': 'C#', 'dob': 'Do#', 'cb': 'C#',
        're': 'Re', 'd': 'D',
        're#': 'Re#', 'd#': 'D#', 'reb': 'Re#', 'db': 'D#',
        'mi': 'Mi', 'e': 'E',
        'fa': 'Fa', 'f': 'F',
        'fa#': 'Fa#', 'f#': 'F#', 'fab': 'Fa#', 'fb': 'F#',
        'sol': 'Sol', 'g': 'G',
        'sol#': 'Sol#', 'g#': 'G#', 'solb': 'Sol#', 'gb': 'G#',
        'la': 'La', 'a': 'A',
        'la#': 'La#', 'a#': 'A#', 'lab': 'La#', 'ab': 'A#',
        'si': 'Si', 'b': 'B'
    };
    
    const normalized = note.toLowerCase();
    return noteMap[normalized] || null;
}

// ============================================================
// CONVERTIR NOTA A SEMITONO (0-11)
// ============================================================
function noteToSemitone(note, notation) {
    if (!note) return -1;
    
    const scale = notation === 'latino' ? latinScale : americanScale;
    const normalized = normalizeNote(note);
    
    if (!normalized) return -1;
    
    // Buscar en la escala correspondiente
    let idx = scale.indexOf(normalized);
    if (idx !== -1) return idx;
    
    // Si no se encuentra, intentar con la otra notación
    const otherScale = notation === 'latino' ? americanScale : latinScale;
    idx = otherScale.indexOf(normalized);
    if (idx !== -1) return idx;
    
    return -1; // No encontrado
}

// ============================================================
// CONVERTIR SEMITONO A NOTA
// ============================================================
function semitoneToNote(semitone, notation) {
    const scale = notation === 'latino' ? latinScale : americanScale;
    return scale[((semitone % 12) + 12) % 12];
}

// ============================================================
// TRANSPONER UN ACORDE (con todos los sufijos)
// ============================================================
function transposeChord(chord, semitones, notation) {
    if (!chord || chord.trim() === '') return chord;
    
    // Extraer raíz y sufijo
    const parsed = extractRootAndSuffix(chord.trim());
    if (!parsed) return chord;
    
    let { root, suffix } = parsed;
    
    // Normalizar la raíz
    const normalizedRoot = normalizeNote(root);
    if (!normalizedRoot) return chord;
    
    // Obtener semitono
    let semitone = noteToSemitone(normalizedRoot, notation);
    if (semitone === -1) return chord;
    
    // Transponer
    let newSemitone = semitone + semitones;
    let newRoot = semitoneToNote(newSemitone, notation);
    
    // Mantener el case original
    // Si el root original estaba en mayúsculas, mantener mayúsculas
    if (root === root.toUpperCase() && root.length <= 2) {
        newRoot = newRoot.toUpperCase();
    } else if (root === root.toLowerCase() && root.length <= 2) {
        newRoot = newRoot.toLowerCase();
    }
    
    return newRoot + suffix;
}

// ============================================================
// TRANSPONER TODA LA LETRA
// ============================================================
function transposeLyrics(text, semitones, notation = 'latino') {
    if (!text) return text;
    
    const chordPattern = /\[([^\]]+)\]/g;
    
    return text.replace(chordPattern, (match, chord) => {
        // Dividir acordes múltiples (separados por espacio)
        let chords = chord.split(/\s+/);
        let transposed = chords.map(c => {
            try {
                return transposeChord(c, semitones, notation);
            } catch (e) {
                return c;
            }
        }).join(' ');
        return `[${transposed}]`;
    });
}

// ============================================================
// CONVERTIR DE NOTACIÓN LATINA A AMERICANA
// ============================================================
function convertToAmerican(text) {
    if (!text) return text;
    
    // Mapeo de notas latinas a americanas
    const latinToAmerican = {
        'do': 'C', 'do#': 'C#', 'dob': 'C#',
        're': 'D', 're#': 'D#', 'reb': 'D#',
        'mi': 'E',
        'fa': 'F', 'fa#': 'F#', 'fab': 'F#',
        'sol': 'G', 'sol#': 'G#', 'solb': 'G#',
        'la': 'A', 'la#': 'A#', 'lab': 'A#',
        'si': 'B'
    };
    
    const chordPattern = /\[([^\]]+)\]/g;
    
    return text.replace(chordPattern, (match, chord) => {
        let chords = chord.split(/\s+/);
        let converted = chords.map(c => {
            // Extraer raíz y sufijo
            const parsed = extractRootAndSuffix(c);
            if (!parsed) return c;
            
            let { root, suffix } = parsed;
            
            // Normalizar raíz a minúsculas para buscar en el mapa
            const rootLower = root.toLowerCase();
            const americanRoot = latinToAmerican[rootLower];
            
            if (americanRoot) {
                // Mantener el case original
                if (root === root.toUpperCase() && root.length <= 2) {
                    return americanRoot.toUpperCase() + suffix;
                } else if (root === root.toLowerCase() && root.length <= 2) {
                    return americanRoot.toLowerCase() + suffix;
                }
                return americanRoot + suffix;
            }
            
            return c;
        }).join(' ');
        return `[${converted}]`;
    });
}

// ============================================================
// CONVERTIR DE NOTACIÓN AMERICANA A LATINA
// ============================================================
function convertToLatin(text) {
    if (!text) return text;
    
    // Mapeo de notas americanas a latinas
    const americanToLatin = {
        'c': 'Do', 'c#': 'Do#', 'cb': 'Do#',
        'd': 'Re', 'd#': 'Re#', 'db': 'Re#',
        'e': 'Mi',
        'f': 'Fa', 'f#': 'Fa#', 'fb': 'Fa#',
        'g': 'Sol', 'g#': 'Sol#', 'gb': 'Sol#',
        'a': 'La', 'a#': 'La#', 'ab': 'La#',
        'b': 'Si'
    };
    
    const chordPattern = /\[([^\]]+)\]/g;
    
    return text.replace(chordPattern, (match, chord) => {
        let chords = chord.split(/\s+/);
        let converted = chords.map(c => {
            // Extraer raíz y sufijo
            const parsed = extractRootAndSuffix(c);
            if (!parsed) return c;
            
            let { root, suffix } = parsed;
            
            // Normalizar raíz a minúsculas para buscar en el mapa
            const rootLower = root.toLowerCase();
            const latinRoot = americanToLatin[rootLower];
            
            if (latinRoot) {
                // Mantener el case original
                if (root === root.toUpperCase() && root.length <= 2) {
                    return latinRoot.toUpperCase() + suffix;
                } else if (root === root.toLowerCase() && root.length <= 2) {
                    return latinRoot.toLowerCase() + suffix;
                }
                return latinRoot + suffix;
            }
            
            return c;
        }).join(' ');
        return `[${converted}]`;
    });
}

// ============================================================
// DETECTAR NOTACIÓN AUTOMÁTICAMENTE
// ============================================================
function detectNotation(text) {
    if (!text) return 'latino';
    
    const chordPattern = /\[([^\]]+)\]/g;
    let match;
    let latinCount = 0;
    let americanCount = 0;
    
    while ((match = chordPattern.exec(text)) !== null) {
        const chord = match[1];
        const chords = chord.split(/\s+/);
        
        chords.forEach(c => {
            const parsed = extractRootAndSuffix(c);
            if (parsed) {
                const root = parsed.root.toLowerCase();
                // Verificar si es latina
                if (['do', 're', 'mi', 'fa', 'sol', 'la', 'si'].includes(root) ||
                    ['do#', 're#', 'fa#', 'sol#', 'la#'].includes(root)) {
                    latinCount++;
                }
                // Verificar si es americana
                if (['c', 'd', 'e', 'f', 'g', 'a', 'b'].includes(root) ||
                    ['c#', 'd#', 'f#', 'g#', 'a#'].includes(root)) {
                    americanCount++;
                }
            }
        });
    }
    
    return americanCount > latinCount ? 'americano' : 'latino';
}

// ============================================================
// FUNCIÓN PRINCIPAL PARA RENDERIZAR
// ============================================================
function renderSongWithAutoDetect(lyrics, transposition = 0, notation = null) {
    if (!lyrics) return '';
    
    if (!notation) {
        notation = detectNotation(lyrics);
    }
    
    let processed = lyrics;
    
    if (notation === 'americano') {
        processed = convertToAmerican(processed);
    } else {
        processed = convertToLatin(processed);
    }
    
    if (transposition !== 0) {
        processed = transposeLyrics(processed, transposition, notation);
    }
    
    processed = processed.replace(/\[([^\]]+)\]/g, '<span class="chord">[$1]</span>');
    
    return processed;
}

// ============================================================
// MOSTRAR/OCULTAR CONTRASEÑA (Toggle Password)
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input[type="password"], input[type="text"]');
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    this.innerHTML = '<i class="bi bi-eye-slash"></i>';
                } else {
                    input.type = 'password';
                    this.innerHTML = '<i class="bi bi-eye"></i>';
                }
            }
        });
    });
});

// ============================================================
// EXPORTAR FUNCIONES GLOBALES
// ============================================================
window.transposeChord = transposeChord;
window.transposeLyrics = transposeLyrics;
window.convertToAmerican = convertToAmerican;
window.convertToLatin = convertToLatin;
window.detectNotation = detectNotation;
window.renderSongWithAutoDetect = renderSongWithAutoDetect;
window.noteToSemitone = noteToSemitone;
window.semitoneToNote = semitoneToNote;
window.normalizeNote = normalizeNote;
window.extractRootAndSuffix = extractRootAndSuffix;