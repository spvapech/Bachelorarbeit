/**
 * WorkPulse · Analytics Report PDF Export — v2 (Redesign)
 *
 * Vier Seiten im Dashboard-Stil (A4 Portrait, light theme):
 *   01 Cover           — Brand-Bar, zentrierter Hero (Firmenname + Datum), Meta-Band, Inhalt
 *   02 Kennzahlen + Timeline — 4 KPI-Karten (tonal) + Timeline-Card mit Filter-Pills & Stats-Footer
 *   03 Topics im Detail      — Multi-Line-Chart-Card mit Legende & Stats-Footer
 *   04 Topic-Übersicht       — Card mit Stats-Strip, Sentiment-Filter-Tabs, Tabelle (Sort-Chevrons)
 *
 * Chart-Extraktion: html2canvas (Container inkl. Legende) → SVG-Fallback.
 *
 * Hauptexport: exportKPIsAsPDF(kpiData)
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

// ═══════════════════════════════════════════════════════════════════════════
// COLORS — gleiche Tokens wie das Frontend (colors_and_type.css)
// ═══════════════════════════════════════════════════════════════════════════
const C = {
    // Slate (Neutralskala)
    s0:   [255, 255, 255],
    s50:  [248, 250, 252],
    s100: [241, 245, 249],
    s150: [233, 238, 244],
    s200: [226, 232, 240],
    s300: [203, 213, 225],
    s400: [148, 163, 184],
    s500: [100, 116, 139],
    s600: [71, 85, 105],
    s700: [51, 65, 85],
    s800: [30, 41, 59],
    s900: [15, 23, 42],

    // Navy (Brand)
    navy: [11, 31, 54],

    // Sentiment / Tone
    emerald50:  [236, 253, 245],
    emerald300: [110, 231, 183],
    emerald500: [16, 185, 129],
    emerald600: [5, 150, 105],
    emerald700: [4, 120, 87],
    rose50:     [255, 241, 242],
    rose300:    [253, 164, 175],
    rose500:    [244, 63, 94],
    rose600:    [225, 29, 72],
    rose700:    [190, 18, 60],
    amber50:    [255, 251, 235],
    amber300:   [253, 230, 138],
    amber500:   [245, 158, 11],
    amber600:   [217, 119, 6],
    amber700:   [180, 83, 9],
    blue50:     [239, 246, 255],
    blue200:    [191, 219, 254],
    blue500:    [59, 130, 246],
    blue600:    [37, 99, 235],
    blue700:    [29, 78, 216],
    orange500:  [249, 115, 22],
    orange600:  [234, 88, 12],
};

// Tonale Paletten — KPI-Karten & Stats-Zellen
const TONE = {
    good:    { bg: C.emerald50, border: C.emerald300, accent: C.emerald500, text: C.emerald700, value: C.emerald600 },
    bad:     { bg: C.rose50,    border: C.rose300,    accent: C.rose500,    text: C.rose700,    value: C.rose600    },
    warn:    { bg: C.amber50,   border: C.amber300,   accent: C.amber500,   text: C.amber700,   value: C.amber600   },
    info:    { bg: C.blue50,    border: C.blue200,    accent: C.blue500,    text: C.blue700,    value: C.blue600    },
    neutral: { bg: C.s0,        border: C.s200,       accent: C.s300,       text: C.s600,       value: C.s900       },
};

const scoreTone = (s) => {
    const n = Number(s);
    if (!Number.isFinite(n)) return 'neutral';
    if (n >= 3.5) return 'good';
    if (n >= 2.5) return 'warn';
    return 'bad';
};

// ═══════════════════════════════════════════════════════════════════════════
// LAYOUT — A4 (mm)
// ═══════════════════════════════════════════════════════════════════════════
const PAGE = {
    w: 210,
    h: 297,
    mx: 16,    // horizontaler Rand
    my: 18,    // vertikaler Rand
    get cw() { return this.w - 2 * this.mx; },
    get cl() { return this.mx; },
    get cr() { return this.w - this.mx; },
};

// ═══════════════════════════════════════════════════════════════════════════
// CHART-EXTRAKTION
// ═══════════════════════════════════════════════════════════════════════════

const sanitizeOklch = (el) => {
    if (!el) return;
    try {
        const cs = getComputedStyle(el);
        ['color', 'backgroundColor', 'borderColor', 'fill', 'stroke'].forEach((p) => {
            const v = cs.getPropertyValue(p);
            if (v && v.includes('oklch')) el.style.setProperty(p, 'transparent', 'important');
        });
        if (el.style?.cssText?.includes('oklch')) {
            el.style.cssText = el.style.cssText.replace(/oklch\([^)]*\)/gi, 'transparent');
        }
    } catch { /* skip */ }
    [...(el.children || [])].forEach(sanitizeOklch);
};

const extractChartViaHtml2Canvas = async (el, targetW = 2400) => {
    if (!el) return null;
    const w = el.offsetWidth || el.scrollWidth || 600;
    const h = el.offsetHeight || el.scrollHeight || 300;
    const canvas = await html2canvas(el, {
        scale: Math.max(3, targetW / w),
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
        allowTaint: true,
        foreignObjectRendering: false,
        imageTimeout: 20000,
        width: w, height: h,
        windowWidth: el.scrollWidth, windowHeight: el.scrollHeight,
        scrollX: 0, scrollY: 0,
        onclone: (clonedDoc) => {
            const cl = el.id ? clonedDoc.getElementById(el.id) : clonedDoc.body;
            if (cl) {
                cl.style.visibility = 'visible';
                cl.style.opacity = '1';
                cl.style.overflow = 'visible';
                sanitizeOklch(cl);
            }
            [...clonedDoc.getElementsByTagName('style')].forEach((s) => {
                if (s.textContent?.includes('oklch')) {
                    s.textContent = s.textContent.replace(/oklch\([^)]*\)/gi, 'transparent');
                }
            });
        },
    });
    return { dataUrl: canvas.toDataURL('image/png', 1.0), w, h };
};

const svgToPng = (svg, targetW = 1200) =>
    new Promise((resolve, reject) => {
        try {
            if (!svg) return reject(new Error('no svg'));
            const clone = svg.cloneNode(true);
            const bbox = svg.getBoundingClientRect();
            const sw = bbox.width || 600, sh = bbox.height || 300;
            clone.setAttribute('width', sw);
            clone.setAttribute('height', sh);
            clone.setAttribute('viewBox', `0 0 ${sw} ${sh}`);
            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            const STYLE_PROPS = [
                'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-linecap',
                'stroke-linejoin', 'opacity', 'fill-opacity', 'stroke-opacity',
                'font-size', 'font-family', 'font-weight', 'text-anchor',
                'dominant-baseline', 'letter-spacing', 'visibility', 'display',
            ];
            const apply = (a, b) => {
                try {
                    const cs = getComputedStyle(a);
                    STYLE_PROPS.forEach((p) => {
                        const v = cs.getPropertyValue(p);
                        if (v && v !== 'none' && !v.includes('oklch')) b.style.setProperty(p, v);
                    });
                } catch { /* skip */ }
                [...(a.children || [])].forEach((c, i) => b.children[i] && apply(c, b.children[i]));
            };
            apply(svg, clone);
            clone.querySelectorAll('.recharts-tooltip-wrapper, .recharts-active-dot').forEach(el => el.remove());
            let str = new XMLSerializer().serializeToString(clone);
            str = str.replace(/oklch\([^)]*\)/gi, '#64748b');
            const url = URL.createObjectURL(new Blob([str], { type: 'image/svg+xml;charset=utf-8' }));
            const img = new Image();
            img.onload = () => {
                const cv = document.createElement('canvas');
                const s = targetW / sw;
                cv.width = Math.round(sw * s); cv.height = Math.round(sh * s);
                const ctx = cv.getContext('2d');
                ctx.imageSmoothingEnabled = true;
                ctx.imageSmoothingQuality = 'high';
                ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, cv.width, cv.height);
                ctx.drawImage(img, 0, 0, cv.width, cv.height);
                URL.revokeObjectURL(url);
                resolve({ dataUrl: cv.toDataURL('image/png', 1.0), w: sw, h: sh });
            };
            img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('img err')); };
            img.src = url;
        } catch (e) { reject(e); }
    });

const extractChart = async (container, targetW = 2400) => {
    if (!container) return null;
    try {
        const r = await extractChartViaHtml2Canvas(container, targetW);
        if (r?.dataUrl?.length > 1000) return r;
    } catch (e) { console.warn('html2canvas fail:', e.message); }
    try {
        const svg = container.querySelector('svg.recharts-surface') || container.querySelector('svg');
        return svg ? await svgToPng(svg, targetW) : null;
    } catch (e) { console.warn('svg fallback fail:', e.message); }
    return null;
};

const prettifyTopic = (key) => {
    if (!key) return '';
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

const extractChartSvgFirst = async (container, targetW = 3000) => {
    if (!container) return null;
    try {
        const svg = container.querySelector('svg.recharts-surface') || container.querySelector('svg');
        if (svg) {
            const r = await svgToPng(svg, targetW);
            if (r?.dataUrl?.length > 1000) return r;
        }
    } catch (e) { console.warn('svg extract fail:', e.message); }
    try {
        const r = await extractChartViaHtml2Canvas(container, targetW);
        if (r?.dataUrl?.length > 1000) return r;
    } catch (e) { console.warn('html2canvas fallback fail:', e.message); }
    return null;
};

// ═══════════════════════════════════════════════════════════════════════════
// PDF-PRIMITIVES
// ═══════════════════════════════════════════════════════════════════════════

// Truncate text to fit width with ellipsis
const fitText = (doc, text, maxW) => {
    if (doc.getTextWidth(text) <= maxW) return text;
    let t = text;
    while (t.length > 1 && doc.getTextWidth(t + '…') > maxW) t = t.slice(0, -1);
    return t + '…';
};

// WorkPulse logo (speech bubble + pulse line). Width in mm. Height ≈ 0.78×w.
const drawLogo = (doc, x, y, w, bubble = C.navy, pulse = C.s0) => {
    const s = w / 44;
    doc.setFillColor(...bubble);
    doc.roundedRect(x, y, 44 * s, 32 * s, 8 * s, 8 * s, 'F');
    doc.triangle(x + 10 * s, y + 30 * s, x + 5 * s, y + 43 * s, x + 17 * s, y + 30 * s, 'F');
    doc.setDrawColor(...pulse);
    doc.setLineWidth(2.5 * s);
    doc.setLineCap('round'); doc.setLineJoin('round');
    const pts = [[5, 16], [11, 16], [15, 7], [19, 24], [23, 12], [27, 16], [39, 16]];
    for (let i = 0; i < pts.length - 1; i++) {
        doc.line(x + pts[i][0] * s, y + pts[i][1] * s, x + pts[i + 1][0] * s, y + pts[i + 1][1] * s);
    }
    doc.setFillColor(...pulse);
    doc.circle(x + 39 * s, y + 16 * s, 2.5 * s, 'F');
    doc.setLineCap('butt'); doc.setLineJoin('miter');
};

// Brand-Bar (Top der Cover-Seite)
const drawCoverBrandBar = (doc, y, reportLabel = 'Analytics Report') => {
    drawLogo(doc, PAGE.mx, y - 0.5, 7);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(...C.s900);
    doc.text('WorkPulse', PAGE.mx + 9, y + 4.2);

    doc.setFont('courier', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(...C.s500);
    doc.text(String(reportLabel).toUpperCase(), PAGE.cr, y + 4.2, { align: 'right' });

    doc.setDrawColor(...C.s900);
    doc.setLineWidth(0.4);
    doc.line(PAGE.mx, y + 8, PAGE.cr, y + 8);
};

// Page-Header für Inhaltsseiten (Seite 2+)
const drawPageHeader = (doc, title, dateStr) => {
    drawLogo(doc, PAGE.mx, 14, 5.5);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(...C.s700);
    doc.text(fitText(doc, String(title), PAGE.cw - 50), PAGE.mx + 7, 17.2);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(...C.s400);
    doc.text(String(dateStr), PAGE.cr, 17.2, { align: 'right' });

    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.2);
    doc.line(PAGE.mx, 21, PAGE.cr, 21);
};

// Footer auf allen Seiten
const drawPageFooter = (doc, leftLabel, centerLabel, rightLabel) => {
    const y = PAGE.h - 11;
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.2);
    doc.line(PAGE.mx, y - 4, PAGE.cr, y - 4);

    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.s500);
    doc.text(String(leftLabel), PAGE.mx, y);
    doc.text(String(rightLabel), PAGE.cr, y, { align: 'right' });

    doc.setFont('courier', 'bold');
    doc.text(String(centerLabel), PAGE.w / 2, y, { align: 'center' });
};

// Section-Titel (Eyebrow-Num + h1 + Tag rechts)
const drawSectionTitle = (doc, y, num, title, tag) => {
    doc.setFont('courier', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...C.s400);
    doc.text(String(num).padStart(2, '0'), PAGE.mx, y);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...C.s900);
    doc.text(title, PAGE.mx + 7, y);

    if (tag) {
        doc.setFont('courier', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s500);
        doc.text(String(tag).toUpperCase(), PAGE.cr, y, { align: 'right' });
    }

    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.2);
    doc.line(PAGE.mx, y + 2.5, PAGE.cr, y + 2.5);

    return y + 8;
};

// ═══════════════════════════════════════════════════════════════════════════
// COVER-SEITE
// ═══════════════════════════════════════════════════════════════════════════

const drawCoverPage = (doc, opts) => {
    const {
        companyName = 'Unbekannte Firma',
        subtitle = 'Übersicht aller Bewertungen, Topics und Trends.',
        dateStr,
        timeStr,
        meta = [],          // [{label, value, sub}]  z.B. {label: 'Zeitraum', value: 'Jan 2018 – Okt 2026', sub: '...'}
        toc = [],           // [{title, page, meta}]
    } = opts;

    // Brand-Bar (oben)
    drawCoverBrandBar(doc, PAGE.my);

    // === Vertikale Mitte für Hero + Meta-Band berechnen ===
    const heroCenterY = 132;

    // === Hero ===
    doc.setFont('courier', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...C.s500);
    doc.text('FIRMENANALYSE · BEWERTUNGEN, TOPICS & TRENDS', PAGE.w / 2, heroCenterY - 30, { align: 'center' });

    // Firmenname (groß, fett, gekürzt falls zu lang)
    doc.setFont('helvetica', 'bold');
    let fs = 44;
    doc.setFontSize(fs);
    while (fs > 14 && doc.getTextWidth(companyName) > PAGE.cw - 20) {
        fs -= 2;
        doc.setFontSize(fs);
    }
    doc.setTextColor(...C.s900);
    doc.text(companyName, PAGE.w / 2, heroCenterY - 14, { align: 'center' });

    // Subtitle
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(...C.s600);
    const subLines = doc.splitTextToSize(subtitle, 130);
    subLines.slice(0, 3).forEach((line, i) => {
        doc.text(line, PAGE.w / 2, heroCenterY - 4 + i * 5, { align: 'center' });
    });

    // Divider (kurzer Strich)
    doc.setDrawColor(...C.s300);
    doc.setLineWidth(0.4);
    doc.line(PAGE.w / 2 - 8, heroCenterY + 8, PAGE.w / 2 + 8, heroCenterY + 8);

    // Datum
    doc.setFont('courier', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(...C.s500);
    doc.text('ERSTELLT AM', PAGE.w / 2, heroCenterY + 14, { align: 'center' });

    doc.setFont('courier', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(...C.s900);
    const datetime = timeStr ? `${dateStr} · ${timeStr}` : dateStr;
    doc.text(datetime, PAGE.w / 2, heroCenterY + 19, { align: 'center' });

    // === Meta-Band (4 Zellen, horizontal getrennt) ===
    const metaY = heroCenterY + 28;
    const metaH = 22;
    const cellW = PAGE.cw / 4;

    // Top + Bottom Linie
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(PAGE.mx, metaY, PAGE.cr, metaY);
    doc.line(PAGE.mx, metaY + metaH, PAGE.cr, metaY + metaH);

    // Vertikale Trenner
    for (let i = 1; i < 4; i++) {
        doc.setDrawColor(...C.s200);
        doc.setLineWidth(0.3);
        doc.line(PAGE.mx + i * cellW, metaY + 3, PAGE.mx + i * cellW, metaY + metaH - 3);
    }

    meta.slice(0, 4).forEach((m, i) => {
        const cx = PAGE.mx + i * cellW + cellW / 2;

        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(String(m.label).toUpperCase(), cx, metaY + 7, { align: 'center' });

        doc.setFont('helvetica', 'bold');
        const valStr = String(m.value);
        let vfs = doc.getTextWidth(valStr) > cellW - 6 ? 11 : 16;
        if (vfs === 11) doc.setFontSize(11);
        else doc.setFontSize(16);
        doc.setTextColor(...C.s900);
        doc.text(fitText(doc, valStr, cellW - 4), cx, metaY + 14, { align: 'center' });

        if (m.sub) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7.5);
            doc.setTextColor(...C.s500);
            doc.text(fitText(doc, String(m.sub), cellW - 4), cx, metaY + metaH - 4, { align: 'center' });
        }
    });

    // === TOC am Fuß ===
    const tocY = metaY + metaH + 22;
    doc.setFont('courier', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(...C.s500);
    doc.text('INHALT', PAGE.mx, tocY);

    let curY = tocY + 8;
    toc.forEach((item, i) => {
        // Num
        doc.setFont('courier', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...C.s400);
        doc.text(String(i + 1).padStart(2, '0'), PAGE.mx, curY);

        // Titel
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(...C.s800);
        const titleW = doc.getTextWidth(item.title);
        doc.text(item.title, PAGE.mx + 8, curY);

        // Meta (heller, kleiner) — direkt hinter dem Titel
        let metaW = 0;
        if (item.meta) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8);
            doc.setTextColor(...C.s400);
            doc.text('· ' + item.meta, PAGE.mx + 8 + titleW + 2, curY);
            metaW = doc.getTextWidth('· ' + item.meta) + 2;
        }

        // Gepunktete Linie
        doc.setDrawColor(...C.s300);
        doc.setLineWidth(0.2);
        doc.setLineDashPattern([0.6, 1.6], 0);
        doc.line(PAGE.mx + 8 + titleW + metaW + 3, curY - 1, PAGE.cr - 10, curY - 1);
        doc.setLineDashPattern([], 0);

        // Seitenzahl
        doc.setFont('courier', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(...C.s600);
        doc.text(String(item.page).padStart(2, '0'), PAGE.cr, curY, { align: 'right' });

        curY += 7;
    });

    // Footer
    drawPageFooter(doc, 'WorkPulse · Analytics Report', companyName, '01 / ' + (toc.length + 1));
};

// ═══════════════════════════════════════════════════════════════════════════
// KPI-CARD (tonaler Akzentbalken + tonaler Hintergrund)
// ═══════════════════════════════════════════════════════════════════════════

const drawKPICard = (doc, x, y, w, h, opts) => {
    const { label, value, badge, footer, tone = 'neutral' } = opts;
    const t = TONE[tone] || TONE.neutral;
    const ix = x + 5;        // inner-left (nach dem 2mm Akzentbalken + 3mm Padding)
    const innerW = w - 8;    // innere Breite

    // Karten-Hintergrund (tonal)
    doc.setFillColor(...t.bg);
    doc.setDrawColor(...t.border);
    doc.setLineWidth(0.3);
    doc.roundedRect(x, y, w, h, 2.5, 2.5, 'FD');

    // Akzentbalken links (2mm breit)
    doc.setFillColor(...t.accent);
    doc.rect(x, y, 1.5, h, 'F');

    // Label (oben links, semibold, tonal)
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...t.text);
    doc.text(fitText(doc, String(label), innerW), ix, y + 6);

    // Value (groß, fett) — Text vs. Zahl unterschiedlich behandeln
    const valStr = String(value);
    const isLongText = valStr.length > 8 || /[a-zäöüß]/i.test(valStr.replace(/\s/g, ''));

    if (isLongText) {
        // Text-Value: Schriftgröße reduzieren bis alles auf eine Zeile passt
        doc.setFont('helvetica', 'bold');
        let vfs = 13;
        doc.setFontSize(vfs);
        while (vfs > 7.5 && doc.getTextWidth(valStr) > innerW) {
            vfs -= 0.5;
            doc.setFontSize(vfs);
        }
        doc.setTextColor(...t.value);
        doc.text(fitText(doc, valStr, innerW), ix, y + 16);
    } else {
        // Numerischer/kurzer Value: groß
        doc.setFont('helvetica', 'bold');
        let vfs = 20;
        doc.setFontSize(vfs);
        while (vfs > 11 && doc.getTextWidth(valStr) > innerW) { vfs -= 1; doc.setFontSize(vfs); }
        doc.setTextColor(...t.value);
        doc.text(valStr, ix, y + 17);
    }

    // Badge (pill, unter dem Value)
    if (badge) {
        const badgeY = y + h - 11;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7);
        const bText = fitText(doc, String(badge), innerW - 4);
        const bW = doc.getTextWidth(bText) + 5;
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(...t.accent);
        doc.setLineWidth(0.3);
        doc.roundedRect(ix, badgeY, bW, 4.4, 2.2, 2.2, 'FD');
        doc.setTextColor(...t.text);
        doc.text(bText, ix + bW / 2, badgeY + 3.1, { align: 'center' });
    }

    // Footer (klein, slate-500, unten links)
    if (footer) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(fitText(doc, String(footer), innerW), ix, y + h - 4);
    }
};

// 4 KPI-Karten in einer Reihe rendern
const drawKPIRow = (doc, y, cards, opts = {}) => {
    const { gap = 2.5, height = 32 } = opts;
    const n = cards.length;
    const cardW = (PAGE.cw - (n - 1) * gap) / n;
    cards.forEach((c, i) => {
        drawKPICard(doc, PAGE.mx + i * (cardW + gap), y, cardW, height, c);
    });
    return y + height;
};

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD-CARD (Chart-Container im Dashboard-Stil)
// ═══════════════════════════════════════════════════════════════════════════

const drawCardHeader = (doc, y, opts) => {
    const { eyebrow, title, subtitle, iconTone = 'info', controlsText } = opts;
    const t = TONE[iconTone] || TONE.info;
    const x = PAGE.mx;

    // Icon-Square (9×9mm, tonal bg + drei aufsteigende Balken als Chart-Symbol)
    const ix = x + 4, iy = y + 4, is = 9;
    doc.setFillColor(...t.bg);
    doc.roundedRect(ix, iy, is, is, 2, 2, 'F');
    doc.setFillColor(...t.accent);
    const bw = 1.9, bx0 = ix + 1.6, bBase = iy + is - 1.6;
    doc.roundedRect(bx0,                bBase - 2.2, bw, 2.2, 0.5, 0.5, 'F');
    doc.roundedRect(bx0 + bw + 0.8,     bBase - 4.0, bw, 4.0, 0.5, 0.5, 'F');
    doc.roundedRect(bx0 + 2*(bw + 0.8), bBase - 6.0, bw, 6.0, 0.5, 0.5, 'F');

    // Text-Block
    const tx = x + 16;
    if (eyebrow) {
        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(String(eyebrow).toUpperCase(), tx, y + 5);
    }
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...C.s900);
    doc.text(title, tx, y + 10);

    if (subtitle) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor(...C.s500);
        doc.text(subtitle, tx, y + 14.5);
    }

    // Filter-Pill rechts (z.B. "Mitarbeiter · Ø Score")
    if (controlsText) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        const tw = doc.getTextWidth(controlsText) + 7;
        const px = PAGE.cr - tw - 2;
        doc.setFillColor(...C.s50);
        doc.setDrawColor(...C.s200);
        doc.setLineWidth(0.3);
        doc.roundedRect(px, y + 6, tw, 5.5, 2.75, 2.75, 'FD');
        doc.setTextColor(...C.s700);
        doc.text(controlsText, px + tw / 2, y + 9.6, { align: 'center' });
    }
};

const drawCardChart = (doc, x, y, w, h, imgResult) => {
    if (!imgResult?.dataUrl) {
        doc.setFillColor(...C.s50);
        doc.roundedRect(x, y, w, h, 1, 1, 'F');
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...C.s400);
        doc.text('Chart nicht verfügbar', x + w / 2, y + h / 2, { align: 'center' });
        return;
    }
    const aspect = imgResult.w / imgResult.h;
    let iw = w, ih = w / aspect;
    if (ih > h) { ih = h; iw = h * aspect; }
    const ix = x + (w - iw) / 2;
    const iy = y + (h - ih) / 2;
    doc.addImage(imgResult.dataUrl, 'PNG', ix, iy, iw, ih);
};

// Stats-Footer-Grid (4 Zellen, jede mit optionalem Tone)
const drawStatsFooter = (doc, x, y, w, cells) => {
    const h = 16;
    const cellW = w / cells.length;

    cells.forEach((cell, i) => {
        const cx = x + i * cellW;
        const t = cell.tone ? (TONE[cell.tone] || TONE.neutral) : TONE.neutral;

        // Hintergrund (tonal oder weiß)
        if (cell.tone && cell.tone !== 'neutral') {
            doc.setFillColor(...t.bg);
            doc.rect(cx, y, cellW, h, 'F');
        }

        // Rechte Trennlinie (zwischen Zellen)
        if (i < cells.length - 1) {
            doc.setDrawColor(...C.s100);
            doc.setLineWidth(0.2);
            doc.line(cx + cellW, y + 2, cx + cellW, y + h - 2);
        }

        // Label
        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(String(cell.label).toUpperCase(), cx + 4, y + 5);

        // Value
        const valStr = String(cell.value);
        const isText = valStr.length > 6 || /[a-zäöü]/i.test(valStr.replace(/\s/g, ''));
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(isText ? 10 : 14);
        doc.setTextColor(...(cell.tone ? t.value : C.s900));
        doc.text(fitText(doc, valStr, cellW - 6), cx + 4, y + 11);

        // Sub
        if (cell.sub) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7);
            doc.setTextColor(...C.s500);
            doc.text(fitText(doc, String(cell.sub), cellW - 6), cx + 4, y + h - 3);
        }
    });

    // Top-Trennlinie zur Card
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.3);
    doc.line(x, y, x + w, y);

    return y + h;
};

// Eine komplette Dashboard-Card rendern. Gibt das untere Y zurück.
// opts: { header: {eyebrow, title, subtitle, iconTone, controlsText},
//         chart: imgResult, chartH: mm,
//         legend: [{label, color, dashed, sourceNote}], stats: [{label, value, sub, tone}],
//         caption: string }
const drawDashboardCard = (doc, y, opts) => {
    const { header, chart, chartH = 70, legend = [], stats = [], caption } = opts;
    const cardX = PAGE.mx;
    const cardW = PAGE.cw;

    // Berechne Card-Höhe: header (18mm) + chart + legend (8 wenn vorhanden) + stats (16)
    const headerH = 18;
    const legendH = legend.length ? 8 : 0;
    const statsH = stats.length ? 16 : 0;
    const cardH = headerH + chartH + legendH + statsH;

    // Karten-Rahmen
    doc.setFillColor(...C.s0);
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.roundedRect(cardX, y, cardW, cardH, 2.5, 2.5, 'FD');

    // Header
    drawCardHeader(doc, y, header);

    // Header → Chart Trennlinie
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.2);
    doc.line(cardX + 2, y + headerH, cardX + cardW - 2, y + headerH);

    // Chart
    drawCardChart(doc, cardX + 4, y + headerH + 2, cardW - 8, chartH - 4, chart);

    let curY = y + headerH + chartH;

    // Legend — reguläre Items links, sourceNote rechts-ausgerichtet italic
    if (legend.length) {
        const noteItem = legend.find(i => i.sourceNote);
        const legendItems = legend.filter(i => !i.sourceNote);

        // Platz für Quellenangabe vorberechnen
        let noteW = 0;
        if (noteItem) {
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(7);
            noteW = doc.getTextWidth(String(noteItem.label)) + 6;
        }
        const maxLx = cardX + cardW - noteW - 4; // rechte Grenze für reguläre Items

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        let lx = cardX + 6;
        const ly = curY + 5;
        legendItems.forEach((item) => {
            const lw = doc.getTextWidth(item.label);
            if (lx + 5.5 + lw > maxLx) return; // überspringen falls kein Platz
            // Swatch
            const swatchY = ly - 1.5;
            if (item.dashed) {
                doc.setDrawColor(...item.color);
                doc.setLineWidth(0.8);
                doc.setLineDashPattern([1, 0.8], 0);
                doc.line(lx, swatchY + 0.5, lx + 4, swatchY + 0.5);
                doc.setLineDashPattern([], 0);
            } else {
                doc.setFillColor(...item.color);
                doc.roundedRect(lx, swatchY, 4, 1.2, 0.6, 0.6, 'F');
            }
            doc.setTextColor(...C.s600);
            doc.text(item.label, lx + 5.5, ly + 1);
            lx += 5.5 + lw + 6;
        });
        // Quellenangabe rechts-ausgerichtet, italic (überschreibt nichts mehr)
        if (noteItem) {
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(7);
            doc.setTextColor(...C.s400);
            doc.text(String(noteItem.label), cardX + cardW - 5, ly + 1, { align: 'right' });
        }
        curY += legendH;
    }

    // Stats
    if (stats.length) {
        drawStatsFooter(doc, cardX, curY, cardW, stats);
    }

    // Caption (optional — italic Unterschrift unterhalb der Card)
    if (caption) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s400);
        doc.text(String(caption), PAGE.w / 2, y + cardH + 5, { align: 'center' });
        return y + cardH + 8;
    }

    return y + cardH;
};

// ═══════════════════════════════════════════════════════════════════════════
// TOPIC-TABELLE
// ═══════════════════════════════════════════════════════════════════════════

const drawSortChevrons = (doc, x, y, active = 'none') => {
    // active: 'up' | 'down' | 'none'
    doc.setLineWidth(0.4);
    doc.setLineCap('round'); doc.setLineJoin('round');

    // Up chevron
    doc.setDrawColor(...(active === 'up' ? C.s700 : C.s400));
    doc.lines([[0.8, -0.7], [0.8, 0.7]], x, y - 0.4);

    // Down chevron
    doc.setDrawColor(...(active === 'down' ? C.s700 : C.s400));
    doc.lines([[0.8, 0.7], [0.8, -0.7]], x, y + 1.4);

    doc.setLineCap('butt'); doc.setLineJoin('miter');
};

// Sentiment-Tone Lookup
const sentimentStyle = (sentiment) => {
    const s = String(sentiment || 'Neutral').trim();
    if (s === 'Positiv') return { bg: C.emerald50, text: C.emerald700, dot: C.emerald500 };
    if (s === 'Negativ') return { bg: C.rose50,    text: C.rose700,    dot: C.rose500    };
    if (s === 'Gemischt') return { bg: C.amber50,  text: C.amber700,   dot: C.amber500   };
    return { bg: C.s100, text: C.s600, dot: C.s400 };
};

// Datenqualität-Tone Lookup
const qualityStyle = (risk) => {
    switch (risk) {
        case 'solid':       return { label: 'Solide',       bg: C.emerald50, text: C.emerald700 };
        case 'acceptable':  return { label: 'Akzeptabel',   bg: C.amber50,   text: C.amber700   };
        case 'constrained': return { label: 'Eingeschränkt', bg: C.amber50,  text: C.amber700   };
        case 'limited':     return { label: 'Begrenzt',     bg: C.rose50,    text: C.rose700    };
        default:            return { label: '–',            bg: null,        text: C.s500       };
    }
};

const ratingTone = (r) => {
    const n = Number(r);
    if (!Number.isFinite(n)) return C.s400;
    if (n >= 3.5) return C.emerald500;
    if (n >= 2.5) return C.amber500;
    return C.rose500;
};

// Tabelle: Topic | Erw. | Ø Rating | Sentiment | Datenqualität
const drawTopicTable = (doc, x, y, w, topics) => {
    const rowH = 7;
    const padL = 4;
    // Spalten-Verhältnisse (Summe = 1.0)
    const ratios = [0.36, 0.12, 0.22, 0.15, 0.15];
    const colX = [];
    let acc = padL;
    ratios.forEach((r) => { colX.push(x + acc); acc += r * (w - padL * 2); });
    const cols = {
        topic:     colX[0],
        ment:      colX[1] + ratios[1] * (w - padL * 2) - 8,        // rechtsbündig
        rating:    colX[2],
        sentiment: colX[3],
        quality:   colX[4],
    };

    // === Header ===
    doc.setFillColor(...C.s50);
    doc.rect(x, y - 4.5, w, rowH + 1, 'F');
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(x, y + rowH - 3.5, x + w, y + rowH - 3.5);

    doc.setFont('courier', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(...C.s600);
    doc.text('TOPIC', cols.topic, y);
    drawSortChevrons(doc, cols.topic + doc.getTextWidth('TOPIC') + 1, y, 'none');

    doc.text('ERWÄHNUNGEN', cols.ment, y, { align: 'right' });
    drawSortChevrons(doc, cols.ment + 1.5, y, 'down');

    doc.text('Ø RATING', cols.rating, y);
    drawSortChevrons(doc, cols.rating + doc.getTextWidth('Ø RATING') + 1, y, 'none');

    doc.text('SENTIMENT', cols.sentiment, y);
    doc.text('DATENQUALITÄT', cols.quality, y);

    let curY = y + rowH + 2;

    // === Rows ===
    topics.forEach((topic, idx) => {
        // Alternierender Background
        if (idx % 2 === 1) {
            doc.setFillColor(...C.s50);
            doc.rect(x, curY - 4.5, w, rowH, 'F');
        }
        // Untere Linie
        doc.setDrawColor(...C.s100);
        doc.setLineWidth(0.15);
        doc.line(x, curY + rowH - 4.5, x + w, curY + rowH - 4.5);

        // Topic-Name
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(...C.s900);
        const topicW = ratios[0] * (w - padL * 2) - 4;
        doc.text(fitText(doc, prettifyTopic(topic.topic), topicW), cols.topic, curY);

        // Erwähnungen (rechtsbündig)
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...C.s700);
        doc.text(String(topic.frequency || 0), cols.ment, curY, { align: 'right' });

        // Ø Rating: Mini-Bar + Wert
        const rating = topic.avgRating;
        if (Number.isFinite(rating)) {
            const barX = cols.rating;
            const barY = curY - 1.5;
            const barW = 16;
            const barH = 1.4;
            // Hintergrund
            doc.setFillColor(...C.s100);
            doc.roundedRect(barX, barY, barW, barH, 0.7, 0.7, 'F');
            // Fill
            const pct = Math.min(1, Math.max(0, rating / 5));
            doc.setFillColor(...ratingTone(rating));
            doc.roundedRect(barX, barY, barW * pct, barH, 0.7, 0.7, 'F');
            // Wert
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(8);
            doc.setTextColor(...C.s900);
            doc.text(rating.toFixed(1).replace('.', ','), barX + barW + 2.5, curY);
        } else {
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(...C.s400);
            doc.text('–', cols.rating, curY);
        }

        // Sentiment-Pill
        const ss = sentimentStyle(topic.sentiment);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7);
        const sLabel = String(topic.sentiment || 'Neutral');
        const sW = doc.getTextWidth(sLabel) + 7;
        doc.setFillColor(...ss.bg);
        doc.roundedRect(cols.sentiment, curY - 3.2, sW, 4.4, 2.2, 2.2, 'F');
        doc.setFillColor(...ss.dot);
        doc.circle(cols.sentiment + 2.4, curY - 0.9, 0.7, 'F');
        doc.setTextColor(...ss.text);
        doc.text(sLabel, cols.sentiment + 4.2, curY - 0.1);

        // Datenqualität-Pill
        const q = qualityStyle(topic.statistical_meta?.risk_level);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7);
        const qW = doc.getTextWidth(q.label) + 5;
        if (q.bg) {
            doc.setFillColor(...q.bg);
            doc.roundedRect(cols.quality, curY - 3.2, qW, 4.4, 2.2, 2.2, 'F');
        }
        doc.setTextColor(...q.text);
        doc.text(q.label, cols.quality + 2.5, curY - 0.1);

        curY += rowH;
    });

    return curY;
};

// Sentiment-Filter-Tabs (Alle / Positiv / Neutral / Negativ)
const drawSentimentTabs = (doc, x, y, w, counts) => {
    // counts: { total, pos, neu, neg }
    const items = [
        { label: 'Alle',    count: counts.total, dotColor: null,           active: true },
        { label: 'Positiv', count: counts.pos,   dotColor: C.emerald500, active: false },
        { label: 'Neutral', count: counts.neu,   dotColor: C.s400,         active: false },
        { label: 'Negativ', count: counts.neg,   dotColor: C.rose500,    active: false },
    ];

    const h = 10;
    // Background-Strip
    doc.setFillColor(...C.s50);
    doc.rect(x, y, w, h, 'F');
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.2);
    doc.line(x, y, x + w, y);
    doc.line(x, y + h, x + w, y + h);

    let cx = x + 6;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);

    items.forEach((it) => {
        const labelW = doc.getTextWidth(it.label);
        const cntStr = String(it.count);
        doc.setFont('courier', 'bold');
        const cntW = doc.getTextWidth(cntStr);
        const pillW = (it.dotColor ? 4 : 0) + labelW + 3 + cntW + 8;
        const pillY = y + 1.8;

        if (it.active) {
            doc.setFillColor(...C.s0);
            doc.setDrawColor(...C.s200);
            doc.setLineWidth(0.3);
            doc.roundedRect(cx, pillY, pillW, 6, 3, 3, 'FD');
        }
        let tx = cx + 4;
        if (it.dotColor) {
            doc.setFillColor(...it.dotColor);
            doc.circle(tx, pillY + 3.1, 0.9, 'F');
            tx += 2.5;
        }
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(...(it.active ? C.s900 : C.s600));
        doc.text(it.label, tx, pillY + 4);
        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(cntStr, tx + labelW + 2.5, pillY + 4);

        cx += pillW + 2;
    });

    // "sortiert nach Erwähnungen" rechts
    doc.setFont('courier', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(...C.s400);
    doc.text('SORTIERT NACH ERWÄHNUNGEN', x + w - 4, y + 6.5, { align: 'right' });

    return y + h;
};

// ═══════════════════════════════════════════════════════════════════════════
// HAUPT-EXPORT
// ═══════════════════════════════════════════════════════════════════════════

export const exportKPIsAsPDF = async (kpiData) => {
    const {
        companyName = 'Unbekannte Firma',
        avgScore = '-',
        trend = null,
        mostCritical = null,
        negativeTopic = '-',
        timelineChartElement = null,
        timelineFilters = null,
        topicRatingChartElement = null,
        topicRatingFilters = null,
        topicOverviewData = null,
    } = kpiData;

    // Charts extrahieren
    console.log('📸 Extrahiere Charts…');
    let timelineImg = null, topicRatingImg = null;
    try { timelineImg = await extractChartSvgFirst(timelineChartElement); }
    catch (e) { console.warn('Timeline-Chart:', e); }
    try { topicRatingImg = await extractChartSvgFirst(topicRatingChartElement); }
    catch (e) { console.warn('Topic-Rating-Chart:', e); }

    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const now = new Date();
    const dateStr = now.toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' });
    const timeStr = now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
    const dateShort = now.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });

    const totalPages = 1 + 1 + (topicRatingImg ? 1 : 0) + (topicOverviewData?.topics?.length ? 1 : 0);
    const headerLabel = `WorkPulse · ${companyName} — Analytics Report`;
    const footerLeft  = `WorkPulse · ${companyName}`;

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 1 — COVER
    // ───────────────────────────────────────────────────────────────────────
    const tocItems = [];
    let page = 2;
    tocItems.push({ title: 'Kennzahlen & Timeline', page: page++, meta: 'Ø Score, Trend + Bewertungsverlauf' });
    if (topicRatingImg) tocItems.push({ title: 'Topics im Detail', page: page++, meta: 'Bewertungen pro Topic-Cluster' });
    if (topicOverviewData?.topics?.length) tocItems.push({ title: 'Topic-Übersicht', page: page++, meta: 'Tabelle aller Topics' });

    drawCoverPage(doc, {
        companyName,
        subtitle: 'Übersicht aller Bewertungen, Topics und Trends. Mitarbeiter- und Bewerberperspektive, aggregiert und über Zeit verglichen.',
        dateStr,
        timeStr,
        meta: [
            {
                label: 'Zeitraum',
                value: timelineFilters?.stats?.dateRange || 'gesamter Zeitraum',
                sub:   timelineFilters?.stats?.dateRangeSub || 'Historie + Prognose',
            },
            {
                label: 'Datenpunkte',
                value: String(timelineFilters?.stats?.dataPoints || '–'),
                sub:   'aggregiert',
            },
            {
                label: 'Topics',
                value: String(topicOverviewData?.topics?.length || topicOverviewData?.stats?.totalTopics || '–'),
                sub:   'Topic-Cluster',
            },
            {
                label: 'Erwähnungen',
                value: String(topicOverviewData?.stats?.totalMentions || '–'),
                sub:   'über alle Topics',
            },
        ],
        toc: tocItems,
    });

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 2 — KENNZAHLEN + TIMELINE
    // ───────────────────────────────────────────────────────────────────────
    doc.addPage();
    drawPageHeader(doc, headerLabel, dateShort);

    let y = 30;
    y = drawSectionTitle(doc, y, 1, 'Kennzahlen', 'Executive Summary · Skala 1 – 5');

    // KPI-Reihe
    const scoreNum = avgScore !== '-' ? Number(avgScore) : NaN;
    const kpis = [
        {
            label: 'Ø Score',
            value: avgScore !== '-' ? String(avgScore).replace('.', ',') : '–',
            badge: '/ 5',
            footer: 'alle Quellen',
            tone: Number.isFinite(scoreNum) ? scoreTone(scoreNum) : 'neutral',
        },
        (() => {
            if (!trend?.avgDelta) return { label: 'Trend 12M', value: '–', footer: 'vs. Vorperiode', tone: 'neutral' };
            const tv = parseFloat(trend.avgDelta);
            return {
                label: 'Trend 12M',
                value: `${tv > 0 ? '+' : ''}${String(trend.avgDelta).replace('.', ',')}`,
                badge: tv > 0.05 ? 'steigend' : tv < -0.05 ? 'sinkend' : 'stabil',
                footer: 'vs. Vorperiode',
                tone: tv > 0.05 ? 'good' : tv < -0.05 ? 'bad' : 'neutral',
            };
        })(),
        {
            label: 'Most Critical',
            value: mostCritical?.topicName && mostCritical.topicName !== '-' ? mostCritical.topicName : '–',
            badge: mostCritical?.score ? `${String(mostCritical.score).replace('.', ',')} / 5` : null,
            footer: 'niedrigster Topic-Score',
            tone: mostCritical ? (Number(mostCritical.score) >= 3.5 ? 'good' : Number(mostCritical.score) >= 2.5 ? 'warn' : 'bad') : 'neutral',
        },
        {
            label: 'Negative Topic',
            value: (negativeTopic && negativeTopic !== '-') ? negativeTopic : '–',
            badge: 'höchste Negativrate',
            footer: 'aus 22 Topics',
            tone: (negativeTopic && negativeTopic !== '-') ? 'bad' : 'neutral',
        },
    ];
    y = drawKPIRow(doc, y, kpis, { height: 30 });

    y += 8;
    y = drawSectionTitle(doc, y, 2, 'Timeline', 'Zeitreihe · Historie & Prognose');

    // Timeline-Card
    const source = timelineFilters?.source === 'employee' ? 'Mitarbeiter'
                 : timelineFilters?.source === 'candidates' ? 'Bewerber' : 'Alle Quellen';

    const tlStats = [];
    if (timelineFilters?.stats?.dataPoints != null) {
        tlStats.push({ label: 'Datenpunkte', value: String(timelineFilters.stats.dataPoints), sub: 'aggregiert' });
    }
    if (timelineFilters?.stats?.avgHistorical) {
        tlStats.push({ label: 'Ø Historisch', value: String(timelineFilters.stats.avgHistorical).replace('.', ','), sub: timelineFilters.stats.dateRange || 'gesamte Historie', tone: 'info' });
    }
    if (timelineFilters?.stats?.avgForecast) {
        tlStats.push({ label: 'Ø Prognose', value: String(timelineFilters.stats.avgForecast).replace('.', ','), sub: timelineFilters.stats.forecastRange || 'kommende Monate', tone: 'warn' });
    }
    if (timelineFilters?.stats?.avgTrend) {
        const at = parseFloat(timelineFilters.stats.avgTrend);
        tlStats.push({
            label: 'Trend',
            value: at > 0 ? '↑ Steigend' : at < 0 ? '↓ Fallend' : '→ Stabil',
            sub: `${at >= 0 ? '+' : ''}${String(timelineFilters.stats.avgTrend).replace('.', ',')}`,
            tone: at > 0 ? 'good' : at < 0 ? 'bad' : 'neutral',
        });
    } else if (timelineFilters?.stats?.avgHistorical && timelineFilters?.stats?.avgForecast) {
        const diff = parseFloat(timelineFilters.stats.avgForecast) - parseFloat(timelineFilters.stats.avgHistorical);
        tlStats.push({
            label: 'Trend',
            value: diff > 0.05 ? '↑ Steigend' : diff < -0.05 ? '↓ Fallend' : '→ Stabil',
            sub: `${diff >= 0 ? '+' : ''}${diff.toFixed(2).replace('.', ',')} vs. Historie`,
            tone: diff > 0.05 ? 'good' : diff < -0.05 ? 'bad' : 'neutral',
        });
    }

    const tlLegend = [
        { label: 'Historisch', color: C.blue600 },
    ];
    if (timelineFilters?.hasInterpolation) tlLegend.push({ label: 'Interpoliert', color: C.s400, dashed: true });
    if (timelineFilters?.hasForecast)      tlLegend.push({ label: 'Prognose',     color: C.orange500, dashed: true });
    if (timelineFilters?.stats?.dataPoints != null) {
        tlLegend.push({ label: `Quelle: ${source} · n = ${timelineFilters.stats.dataPoints} Datenpunkte`, sourceNote: true });
    }

    drawDashboardCard(doc, y, {
        header: {
            eyebrow: 'Zeitreihe · Historie & Prognose',
            title: 'Timeline',
            subtitle: `${source} · ${timelineFilters?.metric || 'Ø Score'}`,
            iconTone: 'info',
            controlsText: source,
        },
        chart: timelineImg,
        chartH: 90,
        legend: tlLegend,
        stats: tlStats,
        caption: 'Abb. 1 · Bewertungsverlauf mit Prognose · gestrichelte Linien = interpolierte bzw. prognostizierte Werte',
    });

    drawPageFooter(doc, footerLeft, '02 / ' + (totalPages || 4), dateShort);

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 3 — TOPICS IM DETAIL
    // ───────────────────────────────────────────────────────────────────────
    if (topicRatingImg) {
        doc.addPage();
        drawPageHeader(doc, headerLabel, dateShort);

        let y3 = 30;
        y3 = drawSectionTitle(doc, y3, 3, 'Topics im Detail', 'Topic-Bewertungen · Detailansicht');

        const trSource = topicRatingFilters?.source === 'employee' ? 'Mitarbeiter'
                       : topicRatingFilters?.source === 'candidates' ? 'Bewerber' : 'Alle Quellen';

        const trStats = [];
        const trGran = topicRatingFilters?.granularity === 'year' ? 'jährlich aggregiert' : 'aggregiert';
        const trTopicCount = (topicRatingFilters?.visibleTopics || []).length;
        if (topicRatingFilters?.stats?.dataPoints != null) {
            trStats.push({ label: 'Datenpunkte', value: String(topicRatingFilters.stats.dataPoints), sub: trGran });
        }
        if (topicRatingFilters?.stats?.avgScore) {
            trStats.push({ label: 'Ø Score', value: String(topicRatingFilters.stats.avgScore).replace('.', ','), sub: `über alle ${trTopicCount} Topics`, tone: 'good' });
        }
        if (topicRatingFilters?.stats?.bestTopic) {
            trStats.push({ label: 'Bestes Topic', value: topicRatingFilters.stats.bestTopic.name, sub: `Ø ${String(topicRatingFilters.stats.bestTopic.score).replace('.', ',')}`, tone: 'good' });
        }
        if (topicRatingFilters?.stats?.worstTopic) {
            trStats.push({ label: 'Schlechtestes', value: topicRatingFilters.stats.worstTopic.name, sub: `Ø ${String(topicRatingFilters.stats.worstTopic.score).replace('.', ',')}`, tone: 'bad' });
        }

        const trLegend = (topicRatingFilters?.visibleTopics || []).slice(0, 6).map((topic, i) => ({
            label: prettifyTopic(topic),
            color: [C.blue500, C.orange500, C.emerald500, [168, 85, 247], C.rose500, [20, 184, 166]][i % 6],
        }));
        if (topicRatingFilters?.stats?.dataPoints != null) {
            trLegend.push({ label: `Quelle: ${trSource} · LDA Topic Modeling`, sourceNote: true });
        }

        drawDashboardCard(doc, y3, {
            header: {
                eyebrow: 'Topic-Bewertungen · Detailansicht',
                title: 'Topics im Detail',
                subtitle: `${trSource} · ${(topicRatingFilters?.visibleTopics || []).length}/${(topicRatingFilters?.allTopics || []).length || '?'} Topics · gesamter Zeitraum`,
                iconTone: 'warn',
                controlsText: trSource,
            },
            chart: topicRatingImg,
            chartH: 95,
            legend: trLegend,
            stats: trStats,
            caption: `Abb. 2 · Durchschnittliche Bewertung pro Topic-Cluster über Zeit · Quelle: ${trSource} · LDA Topic Modeling`,
        });

        drawPageFooter(doc, footerLeft, '03 / ' + totalPages, dateShort);
    }

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 4 — TOPIC-ÜBERSICHT
    // ───────────────────────────────────────────────────────────────────────
    if (topicOverviewData?.topics?.length > 0) {
        doc.addPage();
        drawPageHeader(doc, headerLabel, dateShort);

        let y4 = 30;
        y4 = drawSectionTitle(doc, y4, 4, 'Topic-Übersicht', 'Topic-Cluster · Tabellenansicht');

        const ovSource = topicOverviewData.sourceFilter === 'employee' ? 'Mitarbeiter'
                       : topicOverviewData.sourceFilter === 'candidates' ? 'Bewerber' : 'Alle Quellen';
        const st = topicOverviewData.stats || {};
        const sentCounts = {
            total: topicOverviewData.topics.length,
            pos: topicOverviewData.topics.filter(t => t.sentiment === 'Positiv').length,
            neu: topicOverviewData.topics.filter(t => t.sentiment === 'Neutral' || !t.sentiment).length,
            neg: topicOverviewData.topics.filter(t => t.sentiment === 'Negativ').length,
        };

        // Card-Rahmen vorbereiten
        const cardX = PAGE.mx;
        const cardW = PAGE.cw;
        const headerH = 18;
        const statsH = 16;
        const tabsH = 10;
        const rowH = 7;
        const tableHeadH = 9;

        const maxRows = topicOverviewData.topics.length;
        const cardH = headerH + statsH + tabsH + tableHeadH + maxRows * rowH + 4;

        doc.setFillColor(...C.s0);
        doc.setDrawColor(...C.s200);
        doc.setLineWidth(0.3);
        doc.roundedRect(cardX, y4, cardW, Math.min(cardH, PAGE.h - y4 - 22), 2.5, 2.5, 'FD');

        // Header
        drawCardHeader(doc, y4, {
            eyebrow: 'Topic-Übersicht · Detailansicht',
            title: 'Alle Topics',
            subtitle: `${ovSource} · ${topicOverviewData.topics.length} Topics · ${st.totalMentions || '–'} Erwähnungen`,
            iconTone: 'info',
            controlsText: ovSource,
        });

        // Header → Stats Trennlinie
        doc.setDrawColor(...C.s100);
        doc.setLineWidth(0.2);
        doc.line(cardX + 2, y4 + headerH, cardX + cardW - 2, y4 + headerH);

        // Stats-Strip
        const statsY = y4 + headerH;
        drawStatsFooter(doc, cardX, statsY, cardW, [
            { label: 'Topics',       value: String(topicOverviewData.topics.length), sub: 'identifiziert' },
            { label: 'Erwähnungen',  value: String(st.totalMentions || '–'),         sub: 'über alle Topics' },
            { label: 'Ø Rating',     value: st.avgRating ? String(st.avgRating).replace('.', ',') : '–', sub: 'gewichtet', tone: 'good' },
            { label: 'Sentiment',    value: `${sentCounts.pos}·${sentCounts.neu}·${sentCounts.neg}`,     sub: 'Pos · Neu · Neg' },
        ]);

        // Sentiment-Tabs
        const tabsY = statsY + statsH;
        drawSentimentTabs(doc, cardX, tabsY, cardW, sentCounts);

        // Tabelle
        const tableY = tabsY + tabsH + 6;
        const tableEndY = drawTopicTable(doc, cardX, tableY, cardW, topicOverviewData.topics);

        // Page-count Pill (falls Topics ausgeblendet)
        const shownTopics = topicOverviewData.topics.length;
        const totalTopicCount = topicOverviewData.stats?.totalTopics || shownTopics;
        const hiddenCount = Math.max(0, totalTopicCount - shownTopics);
        if (hiddenCount > 0) {
            const pcY = tableEndY + 6;
            const pcLabel = `${shownTopics} von ${totalTopicCount} Topics`;
            doc.setFont('courier', 'bold');
            doc.setFontSize(7.5);
            const pcW = doc.getTextWidth(pcLabel) + 10;
            doc.setFillColor(...C.s100);
            doc.setDrawColor(...C.s300);
            doc.setLineWidth(0.2);
            doc.roundedRect(PAGE.mx, pcY, pcW, 5.5, 2.75, 2.75, 'FD');
            doc.setTextColor(...C.s700);
            doc.text(pcLabel, PAGE.mx + pcW / 2, pcY + 3.8, { align: 'center' });
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7);
            doc.setTextColor(...C.s500);
            doc.text(
                `Weitere ${hiddenCount} Topics ausgeblendet · alle Topics in der Web-App einsehbar`,
                PAGE.mx + pcW + 5, pcY + 3.8
            );
        }

        drawPageFooter(doc, footerLeft, '04 / ' + totalPages, dateShort);
    }

    // ───────────────────────────────────────────────────────────────────────
    // Speichern
    // ───────────────────────────────────────────────────────────────────────
    const safeName = String(companyName).replace(/\s+/g, '_');
    const fileName = `Analytics_Report_${safeName}_${now.toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    console.log(`✅ PDF gespeichert: ${fileName}`);
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPARE PDF EXPORT — private helpers
// ═══════════════════════════════════════════════════════════════════════════

/** Draw a chart image scaled to fill available width, returns new y. */
const _cmpAddChart = (doc, imgResult, yPos, maxAvailableHeight = null) => {
    if (!imgResult?.dataUrl) return yPos;
    const availW = PAGE.cw;
    const availH = maxAvailableHeight || (PAGE.h - PAGE.my - 10 - yPos);
    const aspect = imgResult.w / imgResult.h;
    let imgW = availW;
    let imgH = imgW / aspect;
    if (imgH > availH) { imgH = availH; imgW = imgH * aspect; }
    const xPos = PAGE.mx + (availW - imgW) / 2;
    doc.addImage(imgResult.dataUrl, 'PNG', xPos, yPos, imgW, imgH);
    return yPos + imgH + 4;
};

/** Draw a bold section title + optional subtitle + rule, returns new y. */
const _cmpAddTitle = (doc, title, yPos, subtitle = null) => {
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s900);
    doc.text(title, PAGE.mx, yPos);
    let y = yPos + 7;
    if (subtitle) {
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s500);
        doc.text(subtitle, PAGE.mx, y);
        y += 5;
    }
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(PAGE.mx, y, PAGE.cr, y);
    return y + 6;
};

/** Draw page footer with label + page number. */
const _cmpAddFooter = (doc, pageNum, totalPages, label) => {
    const y = PAGE.h - PAGE.my + 6;
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(PAGE.mx, y - 4, PAGE.cr, y - 4);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.s400);
    doc.text(label, PAGE.mx, y);
    doc.text(`Seite ${pageNum} / ${totalPages}`, PAGE.cr, y, { align: 'right' });
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPARE PDF EXPORT — main
// ═══════════════════════════════════════════════════════════════════════════

export const exportCompareAsPDF = async (compareData) => {
    const {
        companies = [],         // [{ name, id, score, trend, mostCritical, negativeTopic, categoryRatings }]
        radarChartElement = null,
        barChartElement = null,
        timelineChartElement = null,
        categoryData = [],      // [{ category, ...companyValues }]
        companyColors = null,   // optional hex strings per company
        summaryData = null,     // unused – reserved for future use
        categoryChartView = 'radar',
    } = compareData;

    // Convert hex colour strings supplied by Compare.jsx to RGB triples
    const hexToRgb = (hex) => [
        parseInt(hex.slice(1, 3), 16),
        parseInt(hex.slice(3, 5), 16),
        parseInt(hex.slice(5, 7), 16),
    ];
    const CMP_COLORS_DEFAULT = [C.blue500, C.emerald500, C.orange500, C.rose500, [139, 92, 246]];
    const CMP_COLORS = companyColors
        ? companyColors.map(hexToRgb)
        : CMP_COLORS_DEFAULT;

    const companyNames = companies.map(c => c.name || 'Unbekannt');
    const titleLabel = companyNames.join(' vs. ');

    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    let currentPage = 1;

    // ── chart images ──────────────────────────────────────────────────────
    let radarImg = null, barImg = null, timelineImg = null;
    try { radarImg    = await extractChart(radarChartElement); }    catch (e) { console.warn('Radar-Chart Extraktion fehlgeschlagen:', e); }
    try { barImg      = await extractChart(barChartElement); }      catch (e) { console.warn('Bar-Chart Extraktion fehlgeschlagen:', e); }
    try { timelineImg = await extractChart(timelineChartElement); } catch (e) { console.warn('Timeline-Chart Extraktion fehlgeschlagen:', e); }

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 1 — cover
    // ═════════════════════════════════════════════════════════════════════
    const headerH = 125;
    doc.setFillColor(...C.navy);
    doc.rect(0, 0, PAGE.w, headerH, 'F');
    doc.setFillColor(...C.s800);
    doc.rect(0, headerH - 25, PAGE.w, 25, 'F');

    // accent strip
    doc.setFillColor(...C.blue600);
    doc.rect(0, 0, PAGE.w, 2.5, 'F');

    // bar-chart icon
    const logoX = PAGE.w / 2;
    const logoY = 38;
    [[logoX - 16, 18], [logoX - 8, 14], [logoX, 10], [logoX + 8, 16]].forEach(([x, h], i) => {
        doc.setFillColor(...(i % 2 === 0 ? C.blue600 : C.blue200));
        doc.roundedRect(x, logoY + (18 - h), 5, h, 1, 1, 'F');
    });

    // title
    doc.setFontSize(26);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s0);
    doc.text('Firmenvergleich', PAGE.w / 2, 78, { align: 'center' });

    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.blue200);
    const coverSubtitle = companyNames.length <= 3
        ? companyNames.join('  ·  ')
        : companyNames.slice(0, 3).join('  ·  ');
    doc.text(coverSubtitle, PAGE.w / 2, 90, { align: 'center' });

    doc.setDrawColor(...C.s300);
    doc.setLineWidth(0.3);
    doc.line(PAGE.w / 2 - 40, 96, PAGE.w / 2 + 40, 96);

    doc.setFontSize(10);
    doc.setTextColor(...C.s400);
    doc.text(
        new Date().toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' }),
        PAGE.w / 2, 103, { align: 'center' }
    );

    // summary box
    const execY = headerH + 15;
    doc.setFillColor(...C.s0);
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.4);
    doc.roundedRect(PAGE.mx, execY, PAGE.cw, 40 + companies.length * 8, 3, 3, 'FD');
    doc.setFillColor(...C.blue600);
    doc.roundedRect(PAGE.mx, execY, PAGE.cw, 3, 3, 3, 'F');
    doc.setFillColor(...C.s0);
    doc.rect(PAGE.mx, execY + 2, PAGE.cw, 2, 'F');

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s800);
    doc.text('Zusammenfassung', PAGE.mx + 8, execY + 12);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.s500);
    doc.text(`Vergleich von ${companies.length} Unternehmen anhand von Bewertungen,`, PAGE.mx + 8, execY + 20);
    doc.text('Kategorien, Trends und Themenbereichen.', PAGE.mx + 8, execY + 26);

    let summaryY = execY + 34;
    companies.forEach((comp, i) => {
        const col = CMP_COLORS[i] || C.s400;
        doc.setFillColor(...col);
        doc.circle(PAGE.mx + 12, summaryY + 3, 2, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...C.s800);
        doc.text(comp.name || 'Unbekannt', PAGE.mx + 18, summaryY + 4);
        summaryY += 8;
    });

    // table of contents
    let tocY = summaryY + 14;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s800);
    doc.text('Inhalt', PAGE.mx, tocY);
    tocY += 8;

    const tocItems = [];
    let pgCounter = 1;
    pgCounter++; tocItems.push(['KPI-Vergleich', pgCounter]);
    if (radarImg || barImg) { pgCounter++; tocItems.push(['Kategorievergleich', pgCounter]); }
    if (timelineImg)        { pgCounter++; tocItems.push(['Bewertungsverlauf', pgCounter]); }
    if (categoryData.length > 0) { pgCounter++; tocItems.push(['Detailvergleich', pgCounter]); }

    tocItems.forEach(([label, pg]) => {
        doc.setFontSize(9.5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s800);
        doc.text(label, PAGE.mx + 4, tocY);
        const dotX = PAGE.mx + 4 + doc.getTextWidth(label) + 2;
        const pageX = PAGE.cr - 4;
        doc.setTextColor(...C.s300);
        doc.text('.'.repeat(Math.max(1, Math.floor((pageX - dotX - 10) / 1.5))), dotX, tocY);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...C.blue600);
        doc.text(String(pg), pageX, tocY, { align: 'right' });
        tocY += 6;
    });

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 2 — KPI comparison
    // ═════════════════════════════════════════════════════════════════════
    doc.addPage(); currentPage++;
    doc.setFillColor(...C.s100);
    doc.rect(0, 0, PAGE.w, PAGE.h, 'F');

    let y = _cmpAddTitle(doc, 'KPI-Vergleich', PAGE.my + 5, 'Gegenüberstellung der wichtigsten Kennzahlen');

    // legend
    companies.forEach((comp, i) => {
        const col = CMP_COLORS[i] || C.s400;
        doc.setFillColor(...col);
        doc.circle(PAGE.mx + 4 + i * 60, y, 2, 'F');
        doc.setFontSize(8);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...col);
        doc.text(comp.name.length > 18 ? comp.name.substring(0, 18) + '…' : comp.name, PAGE.mx + 9 + i * 60, y + 0.5);
    });
    y += 10;

    const drawKPIBlock = (title, yPos, getValue) => {
        const rowH = 8;
        const boxH = 10 + companies.length * rowH + 4;
        doc.setFillColor(...C.s0);
        doc.setDrawColor(...C.s200);
        doc.setLineWidth(0.3);
        doc.roundedRect(PAGE.mx, yPos, PAGE.cw, boxH, 2, 2, 'FD');
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...C.s800);
        doc.text(title, PAGE.mx + 6, yPos + 7);
        let rowY = yPos + 14;
        companies.forEach((comp, i) => {
            const col = CMP_COLORS[i] || C.s400;
            const { value, valueColor } = getValue(comp);
            doc.setFillColor(...col);
            doc.circle(PAGE.mx + 10, rowY - 1, 1.5, 'F');
            doc.setFontSize(8.5);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(...C.s800);
            doc.text(comp.name.length > 30 ? comp.name.substring(0, 30) + '…' : comp.name, PAGE.mx + 15, rowY);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(...(valueColor || C.s800));
            doc.text(String(value), PAGE.cr - 6, rowY, { align: 'right' });
            rowY += rowH;
        });
        return yPos + boxH + 6;
    };

    y = drawKPIBlock('Ø Score', y, (comp) => {
        const s = comp.score;
        return {
            value: s != null ? String(s) : '–',
            valueColor: s > 3 ? C.emerald500 : s >= 2 ? C.s800 : s != null ? C.rose500 : C.s300,
        };
    });

    y = drawKPIBlock('Trend', y, (comp) => {
        if (!comp.trend) return { value: '–', valueColor: C.s300 };
        const tv = parseFloat(comp.trend.avgDelta);
        return {
            value: `${tv > 0 ? '+' : ''}${comp.trend.avgDelta}`,
            valueColor: tv > 0.05 ? C.emerald500 : tv < -0.05 ? C.rose500 : C.s500,
        };
    });

    y = drawKPIBlock('Most Critical', y, (comp) => {
        if (!comp.mostCritical) return { value: '–', valueColor: C.s300 };
        return { value: `${comp.mostCritical.topicName} (${comp.mostCritical.score})`, valueColor: C.rose500 };
    });

    drawKPIBlock('Negative Topic', y, (comp) => {
        const nt = comp.negativeTopic;
        if (!nt) return { value: '–', valueColor: C.s300 };
        const lbl = (nt.topic_label || nt.topic_text || nt.topic || '–');
        return { value: lbl.length > 30 ? lbl.substring(0, 30) + '…' : lbl, valueColor: C.orange500 };
    });

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 3 — category comparison (radar + bar)
    // ═════════════════════════════════════════════════════════════════════
    if (radarImg || barImg) {
        doc.addPage(); currentPage++;
        doc.setFillColor(...C.s100);
        doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
        let y3 = _cmpAddTitle(doc, 'Kategorievergleich', PAGE.my + 5, 'Bewertung der Firmen in den einzelnen Kategorien');

        if (radarImg) {
            doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s800);
            doc.text('Radar-Ansicht', PAGE.mx + 8, y3);
            y3 += 4;
            y3 = _cmpAddChart(doc, radarImg, y3, barImg ? 110 : PAGE.h - PAGE.my - 10 - y3);
            y3 += 4;
        }
        if (barImg) {
            doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s800);
            doc.text('Balken-Ansicht', PAGE.mx + 8, y3);
            y3 += 4;
            _cmpAddChart(doc, barImg, y3, PAGE.h - PAGE.my - 10 - y3);
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 4 — timeline
    // ═════════════════════════════════════════════════════════════════════
    if (timelineImg) {
        doc.addPage(); currentPage++;
        doc.setFillColor(...C.s100);
        doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
        const y4 = _cmpAddTitle(doc, 'Bewertungsverlauf', PAGE.my + 5, 'Historische Entwicklung der Bewertungen im Vergleich');
        _cmpAddChart(doc, timelineImg, y4, PAGE.h - PAGE.my - 10 - y4);
    }

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 5+ — detail table
    // ═════════════════════════════════════════════════════════════════════
    if (categoryData.length > 0) {
        doc.addPage(); currentPage++;
        doc.setFillColor(...C.s100);
        doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
        let yT = _cmpAddTitle(doc, 'Detailvergleich', PAGE.my + 5, 'Bewertungen nach Kategorien mit Differenzanalyse');

        const catColW = 55;
        const compColW = companies.length >= 3 ? 30 : 38;
        const rowH = 7;

        const drawTableHeader = (atY) => {
            doc.setFillColor(...C.s800);
            doc.roundedRect(PAGE.mx, atY - 5, PAGE.cw, rowH + 3, 1, 1, 'F');
            doc.setFontSize(7.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s0);
            doc.text('Kategorie', PAGE.mx + 4, atY);
            companies.forEach((comp, i) => {
                doc.text(
                    comp.name.length > 12 ? comp.name.substring(0, 12) + '…' : comp.name,
                    PAGE.mx + catColW + i * compColW, atY
                );
            });
            doc.text('Diff.', PAGE.cr - 4, atY, { align: 'right' });
            return atY + rowH + 2;
        };

        yT = drawTableHeader(yT);

        categoryData.forEach((row, idx) => {
            if (yT > PAGE.h - PAGE.my - 10) {
                doc.addPage(); currentPage++;
                doc.setFillColor(...C.s100);
                doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
                yT = PAGE.my;
                yT = drawTableHeader(yT);
            }
            doc.setFillColor(...(idx % 2 === 0 ? C.s0 : C.s50));
            doc.rect(PAGE.mx, yT - 4.5, PAGE.cw, rowH, 'F');

            doc.setFontSize(7.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s800);
            doc.text(row.category.length > 28 ? row.category.substring(0, 28) + '…' : row.category, PAGE.mx + 4, yT);

            const values = companies.map(comp => {
                const v = row[comp.name];
                return v != null ? Number(v) : null;
            });
            const valid = values.filter(v => v != null);
            const maxVal = valid.length ? Math.max(...valid) : null;
            const minVal = valid.length ? Math.min(...valid) : null;

            companies.forEach((comp, i) => {
                const x = PAGE.mx + catColW + i * compColW;
                const val = values[i];
                if (val == null) {
                    doc.setFont('helvetica', 'normal'); doc.setTextColor(...C.s300);
                    doc.text('–', x, yT);
                } else {
                    const isBest  = valid.length >= 2 && val === maxVal;
                    const isWorst = valid.length >= 2 && val === minVal && maxVal !== minVal;
                    doc.setFont('helvetica', 'bold');
                    doc.setTextColor(...(isBest ? C.emerald500 : isWorst ? C.rose500 : C.s800));
                    doc.text(val.toFixed(2), x, yT);
                }
            });

            if (valid.length >= 2) {
                doc.setFont('helvetica', 'normal'); doc.setTextColor(...C.s500);
                doc.text(`±${(maxVal - minVal).toFixed(2)}`, PAGE.cr - 4, yT, { align: 'right' });
            }
            yT += rowH;
        });

        doc.setDrawColor(...C.s200); doc.setLineWidth(0.3);
        doc.line(PAGE.mx, yT - 3, PAGE.cr, yT - 3);
    }

    // ═════════════════════════════════════════════════════════════════════
    // Footers on every page except cover
    // ═════════════════════════════════════════════════════════════════════
    const totalPages = doc.internal.pages.length - 1;
    for (let i = 2; i <= totalPages; i++) {
        doc.setPage(i);
        _cmpAddFooter(doc, i, totalPages, titleLabel);
    }

    const fileName = `Firmenvergleich_${companyNames.map(n => n.replace(/\s+/g, '_')).join('_vs_')}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    console.log(`✅ Firmenvergleich PDF gespeichert: ${fileName} (${totalPages} Seiten)`);
};
